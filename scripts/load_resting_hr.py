"""
load_resting_hr.py
Loads and cleans the daily resting heart rate data (the target variable).

Input : data/daily_resting_heart_rate.csv
Output: a tidy DataFrame indexed by date with one column, resting_hr.

Run directly to print a summary and save a plot:
    python load_resting_hr.py
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Adjust if your data lives elsewhere
DATA_PATH = Path("data/daily_resting_heart_rate.csv")


def load_resting_hr(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load daily resting HR, return a clean DataFrame indexed by date."""
    df = pd.read_csv(path)

    # Rename the awkward source columns to something usable
    df = df.rename(columns={
        "timestamp": "date",
        "beats per minute": "resting_hr",
        "data source": "source",
    })

    # Parse timestamp -> date (drop the time part; it's always midnight UTC)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["date"] = pd.to_datetime(df["date"])

    # Keep only what we need, set date as index, sort
    df = df[["date", "resting_hr"]].set_index("date").sort_index()

    # Basic cleaning: drop exact-duplicate dates if any, drop missing HR
    df = df[~df.index.duplicated(keep="first")]
    df = df.dropna(subset=["resting_hr"])

    return df


def summarize(df: pd.DataFrame) -> None:
    """Print a quick sanity-check summary."""
    print(f"Rows:           {len(df)}")
    print(f"Date range:     {df.index.min().date()} -> {df.index.max().date()}")
    print(f"Resting HR min: {df['resting_hr'].min():.1f}")
    print(f"Resting HR max: {df['resting_hr'].max():.1f}")
    print(f"Resting HR mean:{df['resting_hr'].mean():.1f}")

    # Check for gaps in the daily series
    full_range = pd.date_range(df.index.min(), df.index.max(), freq="D")
    missing = full_range.difference(df.index)
    print(f"Missing days:   {len(missing)}")
    if len(missing) > 0:
        print(f"  e.g. {[d.date() for d in missing[:5]]}")


def plot_resting_hr(df: pd.DataFrame, out="resting_hr_over_time.png") -> None:
    """Plot resting HR over time and save to file."""
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df["resting_hr"], linewidth=1, color="#c0392b")
    ax.scatter(df.index, df["resting_hr"], s=8, color="#c0392b", alpha=0.4)

    # highlighting Malaysia trip and sickness
    ax.axvspan(pd.Timestamp("2026-01-18"), pd.Timestamp("2026-01-29"),
               color="orange", alpha=0.15, label="Malaysia trip")

    ax.axvspan(pd.Timestamp("2026-04-18"), pd.Timestamp("2026-04-28"),
               color="orange", alpha=0.15, label="Sickness")

    ax.set_title("Daily Resting Heart Rate Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Resting HR (bpm)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    print(f"Saved plot -> {out}")


if __name__ == "__main__":
    df = load_resting_hr()
    summarize(df)
    plot_resting_hr(df)