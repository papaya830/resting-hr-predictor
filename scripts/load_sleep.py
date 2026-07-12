"""
load_sleep.py
Loads and cleans session-level sleep data -> one row per night.

Key cleaning steps:
  1. Apply each session's own UTC offset to get LOCAL start/end times
     (offsets vary: -07:00/-08:00 at home, +08:00 in Malaysia, others while
     travelling -- so we must use the per-row offset, not assume Pacific).
  2. Separate naps from main sleep using a minutes_asleep threshold.
  3. Assign each main-sleep session to a calendar date by its WAKE-UP morning
     (local end time's date).
  4. If more than one main-sleep session shares a night, keep the longest.
  5. Compute sleep efficiency = minutes_asleep / minutes_in_sleep_period.

Optionally merges per-night quality (deep sleep, REM%, restlessness) from
UserSleepScores by sleep_id.

Input : data/UserSleeps_2025-09-26.csv
        data/UserSleepScores_2025-09-26.csv   (optional, for quality metrics)
Output: DataFrame indexed by date with columns:
    minutes_asleep, sleep_efficiency, utc_offset  (+ deep/rem/restlessness if scores merged)
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

SLEEP_PATH = Path("data/UserSleeps_2025-09-26.csv")
SCORES_PATH = Path("data/UserSleepScores_2025-09-26.csv")

# A session with less sleep than this (minutes) is treated as a nap, not a night.
NAP_THRESHOLD_MIN = 180


def _to_local(utc_series: pd.Series, offset_series: pd.Series) -> pd.Series:
    """Convert a UTC timestamp column to local time using per-row offsets."""
    utc = pd.to_datetime(utc_series, utc=True)
    # offset like '-07:00' -> Timedelta; add to UTC to get local wall-clock
    td = pd.to_timedelta(offset_series.str.replace(":", "", regex=False)
                         .str.replace(r"(\d{2})(\d{2})$", r"\1 hours \2 minutes",
                                      regex=True))
    return (utc + td.values).dt.tz_localize(None)


def load_sleep(sleep_path: Path = SLEEP_PATH,
               scores_path: Path = SCORES_PATH,
               merge_scores: bool = True) -> pd.DataFrame:
    df = pd.read_csv(sleep_path)

    # --- 1. Local start/end from per-row offsets ---
    df["local_start"] = _to_local(df["sleep_start"], df["start_utc_offset"])
    df["local_end"] = _to_local(df["sleep_end"], df["end_utc_offset"])

    # --- 2. Drop naps: keep only sessions with enough sleep ---
    main = df[df["minutes_asleep"] >= NAP_THRESHOLD_MIN].copy()

    # --- 3. Assign to wake-up morning (local end date) ---
    main["date"] = main["local_end"].dt.normalize()

    # --- 4. One row per night: if duplicates, keep the longest sleep ---
    main = (main.sort_values("minutes_asleep", ascending=False)
                .drop_duplicates(subset="date", keep="first"))

    # --- 5. Efficiency ---
    main["sleep_efficiency"] = (
        main["minutes_asleep"] / main["minutes_in_sleep_period"]
    )

    out = main.set_index("date").sort_index()[[
        "minutes_asleep", "sleep_efficiency", "start_utc_offset"
    ]].rename(columns={"start_utc_offset": "utc_offset"})

    # --- optional: merge quality metrics from scores by sleep_id ---
    if merge_scores and scores_path.exists():
        scores = pd.read_csv(scores_path)
        keep = scores[["sleep_id", "overall_score", "deep_sleep_minutes",
                       "rem_sleep_percent", "restlessness_normalized"]]
        # attach sleep_id back to main via index alignment
        sid = main.set_index("date")["sleep_id"]
        merged = keep.set_index("sleep_id").reindex(sid.values)
        merged.index = sid.index
        out = out.join(merged)

    return out


def summarize(df: pd.DataFrame) -> None:
    print(f"Nights:            {len(df)}")
    print(f"Date range:        {df.index.min().date()} -> {df.index.max().date()}")
    print(f"Asleep min/med/max:{df['minutes_asleep'].min():.0f} / "
          f"{df['minutes_asleep'].median():.0f} / {df['minutes_asleep'].max():.0f}")
    print(f"Efficiency mean:   {df['sleep_efficiency'].mean():.1%}")
    non_pacific = df[~df["utc_offset"].isin(["-07:00", "-08:00"])]
    print(f"Non-Pacific nights (travel): {len(non_pacific)}")
    if "overall_score" in df:
        print(f"Nights with score: {df['overall_score'].notna().sum()}")


def plot_sleep(df: pd.DataFrame, out="sleep_over_time.png") -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df["minutes_asleep"] / 60, linewidth=1, color="#8e44ad")
    ax.scatter(df.index, df["minutes_asleep"] / 60, s=8, color="#8e44ad", alpha=0.4)
    ax.axvspan(pd.Timestamp("2026-01-18"), pd.Timestamp("2026-01-29"),
               color="orange", alpha=0.15, label="Malaysia trip")
    ax.axvspan(pd.Timestamp("2026-04-18"), pd.Timestamp("2026-04-28"),
               color="red", alpha=0.12, label="Illness")
    ax.set_title("Nightly Sleep Duration Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Hours asleep")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    print(f"Saved plot -> {out}")


if __name__ == "__main__":
    df = load_sleep()
    summarize(df)
    plot_sleep(df)