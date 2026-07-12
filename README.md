\# Resting Heart Rate Model Predictor

CMPT 353 End of Term Project



\*\*Idea:\*\* Can we model resting heart rate (HR) as a function of training load,

sleep, and environment from personal wearable data?



\*\*Core Question:\*\* Based on my personal health data collected from Google Health

(September 2025 – July 2026), how does my resting heart rate relate to training

load, sleep, and environment — how much and what kind of exercise moves my

resting HR, and on what timescale?



\## Factors of resting heart rate

Resting HR depends on many things, notably genetics, sleep, cardiovascular

fitness, age, stress and emotions, medications and substances, environment, and

health conditions.



To reduce the effect of confounders, it helps that the data comes from a single,

stable subject: I am a healthy, active 21-year-old woman who does high-intensity

cardiovascular activity 2–3 times a week, consumes minimal medications and

substances, and lives in Coquitlam, BC. This keeps genetics, age, and baseline

health roughly constant across the period, so the analysis can focus on the

factors that vary day to day: training load, sleep, and environment.



\## Data

\*\*Google Health (≈9 months, Sept 2025 – July 2026):\*\*

\- Daily resting heart rate — the target variable (267 days)

\- Training load — Active Zone Minutes, logged minute-by-minute with

&#x20; intensity zones (fat burn / cardio / peak)

\- Sleep — per-night duration, efficiency, and sleep score

\- Daily readiness — score plus sleep / HRV / resting-HR subcomponents

&#x20; (from 2026-01-07 onward, after the device's readiness calibration period;

&#x20; \~145 days). Used as an exploratory feature only, since readiness is partly

&#x20; derived from resting HR and would otherwise leak into the target.



\*\*External:\*\*

\- Daily local temperature for Coquitlam, BC, from an external weather archive

&#x20; (Environment Canada or Open-Meteo), joined by date.



\## Note on travel (Jan 18–29, 2026)

For \~11 days I was travelling in Malaysia — a hot, humid climate with a large

time-zone shift, disrupted sleep, and an altered training schedule. This period

affects several variables at once and breaks the assumption that local Coquitlam

weather reflects my environment, so it is flagged explicitly and handled as a

special case in the analysis (examined separately or excluded, rather than

treated as ordinary days).



\## Running the code

\_(to be completed)\_ — required libraries, commands, and arguments.



\## Limitations

This is a single-subject, observational study, so results describe associations

for one person and are not intended as causal or generalizable claims.

## Notes on anomalous periods
Travel (different climate / timezone / routine — cross-checked against the
utc_offset recorded in the sleep data):
- Toronto: Jan 8–13 and Mar 20–23, 2026
- Malaysia: Jan 18–29, 2026 (hot/humid, +8h timezone)
- Edmonton: Apr 25–28, 2026

Illness: Apr 18–28, 2026 — resting HR elevated, training load ~0. Note this
overlaps the Edmonton trip at the end, so late April is treated as a single
excluded period rather than separating the two effects.

## Data coverage note
Resting heart rate and training load (AZM) span the full period (Sep 2025 – Jul 2026).
Sleep tracking is sparse before January: the watch wasn't worn to sleep
consistently until ~January 2026, so reliable nightly sleep data covers
Jan–Jul 2026 (~140 nights). Daily readiness likewise begins Jan 7 (after the
device's calibration period). Analyses using sleep or readiness are therefore
run on this shorter window, while training-load-vs-resting-HR analysis uses the
full 9 months.