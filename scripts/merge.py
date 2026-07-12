"""
build_daily.py
Joins the three cleaned sources into one daily table -- the modeling foundation.

Join logic (the important decisions):
  - Base = resting HR calendar (the target; every day we have a resting HR).
  - AZM training load: merged in, then non-active days filled with 0
    (a day with no AZM row means NO training, not missing data).
  - Sleep: merged in; genuine gaps left as NaN (missing = watch not worn,
    which is truly unknown, not zero).
  - Anomaly flags: boolean columns for travel and illness, from known windows.

Input : reads via load_resting_hr / load_azm / load_sleep
Output: data/daily.csv  and returns the DataFrame.
"""

from pathlib import Path
import pandas as pd

from load_resting_hr import load_resting_hr
from load_azm import load_azm
from load_sleep import load_sleep

# Known anomalous windows (inclusive). Travel cross-checked against sleep offsets.
TRAVEL_WINDOWS = [
    ("2026-01-08", "2026-01-13"),   # Toronto
    ("2026-01-18", "2026-01-29"),   # Malaysia
    ("2026-03-20", "2026-03-23"),   # Toronto
    ("2026-04-25", "2026-04-28"),   # Edmonton
]
SICK_WINDOW = ("2026-04-18", "2026-04-28")   # overlaps Edmonton at the tail


def _flag(index: pd.DatetimeIndex, windows) -> pd.Series:
    """Boolean series: True on dates falling in any (start,end) window."""
    flag = pd.Series(False, index=index)
    for start, end in windows:
        flag |= (index >= pd.Timestamp(start)) & (index <= pd.Timestamp(end))
    return flag


def build_daily() -> pd.DataFrame:
    hr = load_resting_hr()      # index=date, col: resting_hr
    azm = load_azm()            # index=date, cols: azm_load, fat_burn_min, ...
    sleep = load_sleep()        # index=date, cols: minutes_asleep, efficiency, ...

    # Base calendar: every day from first to last resting-HR reading
    full = pd.date_range(hr.index.min(), hr.index.max(), freq="D")
    daily = pd.DataFrame(index=full)
    daily.index.name = "date"

    # --- resting HR (target) ---
    daily = daily.join(hr)

    # --- training load: merge, then fill non-active days with 0 ---
    daily = daily.join(azm[["azm_load", "fat_burn_min", "cardio_min", "peak_min"]])
    load_cols = ["azm_load", "fat_burn_min", "cardio_min", "peak_min"]
    daily[load_cols] = daily[load_cols].fillna(0)

    # --- sleep: merge, leave gaps as NaN (genuinely missing) ---
    sleep_cols = ["minutes_asleep", "sleep_efficiency"]
    if "overall_score" in sleep:
        sleep_cols += ["deep_sleep_minutes", "rem_sleep_percent",
                       "restlessness_normalized"]
    daily = daily.join(sleep[[c for c in sleep_cols if c in sleep]])

    # --- anomaly flags ---
    daily["travel"] = _flag(daily.index, TRAVEL_WINDOWS)
    daily["sick"] = _flag(daily.index, [SICK_WINDOW])
    daily["anomaly"] = daily["travel"] | daily["sick"]

    return daily


def summarize(df: pd.DataFrame) -> None:
    print(f"Total days:        {len(df)}")
    print(f"Date range:        {df.index.min().date()} -> {df.index.max().date()}")
    print()
    print("Coverage (non-null) per column:")
    for col in df.columns:
        n = df[col].notna().sum()
        print(f"  {col:22s} {n:4d}  ({n/len(df):.0%})")
    print()
    print(f"Travel days: {df['travel'].sum()}   Sick days: {df['sick'].sum()}"
          f"   Any anomaly: {df['anomaly'].sum()}")
    print()
    print("First few rows:")
    print(df.head(3).to_string())


if __name__ == "__main__":
    daily = build_daily()
    summarize(daily)
    out = Path("data/daily.csv")
    daily.to_csv(out)
    print(f"\nSaved -> {out}")