"""
load_weather.py
Loads daily temperature from Open-Meteo CSV files downloaded into data/weather/.
No web call -- reads the committed CSVs, so the pipeline is reproducible offline.

Open-Meteo CSVs have 2 metadata rows + 1 blank line before the real header,
hence skiprows=3.

Weather source: Open-Meteo.com (ERA5 reanalysis), CC BY 4.0.

Two ways to use the data:
  load_weather()            -> Coquitlam only, full period (the main column).
  load_weather(stitch=True) -> Coquitlam, but with destination temperature
                               swapped in for each travel window ("temperature
                               where I actually was"). Useful e.g. for the
                               Malaysia heat case-study.

Output: DataFrame indexed by date with temp_mean, temp_max, temp_min
        (stitch=True adds a `temp_location` column naming the source city).
"""

from pathlib import Path
import pandas as pd

WEATHER_DIR = Path("data/weather")

# Trip files mapped to their date windows (inclusive)
TRIP_FILES = [
    ("toronto-jan-weather.csv",    "2026-01-08", "2026-01-13", "Toronto"),
    ("malaysia-weather.csv",       "2026-01-18", "2026-01-29", "Malaysia"),
    ("toronto-march-weather.csv",  "2026-03-20", "2026-03-23", "Toronto"),
    ("edmonton-weather.csv",       "2026-04-25", "2026-04-28", "Edmonton"),
]

_RENAME = {
    "time": "date",
    "temperature_2m_mean (\u00b0C)": "temp_mean",
    "temperature_2m_max (\u00b0C)": "temp_max",
    "temperature_2m_min (\u00b0C)": "temp_min",
}


def _read_meteo_csv(path: Path) -> pd.DataFrame:
    """Read one Open-Meteo CSV, skipping the metadata header."""
    df = pd.read_csv(path, skiprows=3).rename(columns=_RENAME)
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[["temp_mean", "temp_max", "temp_min"]].sort_index()


def load_weather(weather_dir: Path = WEATHER_DIR,
                 stitch: bool = False) -> pd.DataFrame:
    base = _read_meteo_csv(weather_dir / "coquitlam-weather.csv")

    if not stitch:
        return base

    out = base.copy()
    out["temp_location"] = "Coquitlam"
    for fname, start, end, city in TRIP_FILES:
        trip = _read_meteo_csv(weather_dir / fname)
        mask = (out.index >= pd.Timestamp(start)) & (out.index <= pd.Timestamp(end))
        for col in ["temp_mean", "temp_max", "temp_min"]:
            out.loc[mask, col] = trip[col].reindex(out.index[mask]).values
        out.loc[mask, "temp_location"] = city
    return out


def summarize(df: pd.DataFrame) -> None:
    print(f"Days:            {len(df)}")
    print(f"Date range:      {df.index.min().date()} -> {df.index.max().date()}")
    print(f"Mean temp range: {df['temp_mean'].min():.1f} to {df['temp_mean'].max():.1f} \u00b0C")
    print(f"Overall average: {df['temp_mean'].mean():.1f} \u00b0C")
    if "temp_location" in df:
        print("Days per location:")
        print(df["temp_location"].value_counts().to_string())


if __name__ == "__main__":
    print("=== Coquitlam only (main column) ===")
    summarize(load_weather())
    print("\n=== Stitched (where I actually was) ===")
    summarize(load_weather(stitch=True))