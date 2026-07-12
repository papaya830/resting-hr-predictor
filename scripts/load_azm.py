"""
load_azm.py
Loads and cleans Active Zone Minutes (AZM) data -> daily training load.

AZM files are one row per active minute, tagged with a heart-rate zone and a
`total_minutes` value that is already Fitbit's weighted AZM credit for that
minute (FAT_BURN = 1, CARDIO/PEAK = 2). Daily training load is therefore just
the sum of total_minutes per day.

Input : data/active_zone_minutes/Active Zone Minutes - *.csv   (11 monthly files)
Output: a tidy DataFrame indexed by date with columns:
    azm_load        - total weighted AZM for the day (main training-load feature)
    fat_burn_min    - minutes in FAT_BURN zone
    cardio_min      - minutes in CARDIO zone
    peak_min        - minutes in PEAK zone
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

AZM_DIR = Path("data/active_zone_minutes")


def load_azm(azm_dir: Path = AZM_DIR) -> pd.DataFrame:
    """Load all monthly AZM files, aggregate to one row per day."""
    files = sorted(azm_dir.glob("Active Zone Minutes - *.csv"))
    if not files:
        raise FileNotFoundError(f"No AZM files found in {azm_dir}")

    # Concatenate all monthly files into one long minute-level frame
    frames = [pd.read_csv(f) for f in files]
    df = pd.concat(frames, ignore_index=True)

    # Parse timestamp -> date (times are local, no timezone suffix)
    df["date"] = pd.to_datetime(df["date_time"]).dt.normalize()

    # --- Daily total training load: sum the weighted total_minutes ---
    daily_load = df.groupby("date")["total_minutes"].sum().rename("azm_load")

    # --- Zone breakdown: count minutes per zone per day ---
    # (one row = one minute, so a simple count per zone per day)
    zone_counts = (
        df.groupby(["date", "heart_zone_id"]).size()
        .unstack(fill_value=0)
    )
    # Normalize expected zone columns even if one never appears
    for zone, col in [("FAT_BURN", "fat_burn_min"),
                      ("CARDIO", "cardio_min"),
                      ("PEAK", "peak_min")]:
        zone_counts[col] = zone_counts[zone] if zone in zone_counts else 0
    zone_counts = zone_counts[["fat_burn_min", "cardio_min", "peak_min"]]

    # Combine load + breakdown
    out = pd.concat([daily_load, zone_counts], axis=1).sort_index()
    out.index.name = "date"
    return out


def summarize(df: pd.DataFrame) -> None:
    print(f"Active days:      {len(df)}")
    print(f"Date range:       {df.index.min().date()} -> {df.index.max().date()}")
    print(f"Daily load min:   {df['azm_load'].min():.0f}")
    print(f"Daily load max:   {df['azm_load'].max():.0f}")
    print(f"Daily load mean:  {df['azm_load'].mean():.1f}")
    print(f"Total AZM (all):  {df['azm_load'].sum():.0f}")
    print(f"Zone totals -> fat_burn:{df['fat_burn_min'].sum():.0f} "
          f"cardio:{df['cardio_min'].sum():.0f} peak:{df['peak_min'].sum():.0f}")


def plot_azm(df: pd.DataFrame, out="azm_load_over_time.png") -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(df.index, df["azm_load"], width=1.0, color="#2980b9", alpha=0.8)

    # Mark the anomalous windows
    ax.axvspan(pd.Timestamp("2026-01-18"), pd.Timestamp("2026-01-29"),
               color="orange", alpha=0.15, label="Malaysia trip")
    ax.axvspan(pd.Timestamp("2026-04-18"), pd.Timestamp("2026-04-28"),
               color="red", alpha=0.12, label="Illness")

    ax.set_title("Daily Training Load (Active Zone Minutes) Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Weighted AZM")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    print(f"Saved plot -> {out}")


if __name__ == "__main__":
    df = load_azm()
    summarize(df)
    plot_azm(df)