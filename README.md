# Calgary-Transit-Delay-and-Timing-Predictor

## Overview
The Calgary Transit Delay and Timing Predictor collects real-time GTFS transit data every 3-4 hours using GitHub Actions. Information collected includes the timestamp, trip_id, route_id, stop_id and the position of the vehicle. 

## What has been done so far
- Automated scraper pulls GTFS-Realtime vehicle positions useful for delay calculations every 3-4 hours via GitHub Actions.
- Cleaned and preprocessed data pulled from Supabase( 74k rows) using Juypyter Notebooks and Pandas.
- Calculated delay in seconds and minutes using the time from the timestamp and the arrival time from transit data. A negative value indicates its earlier than scheduled and vice-versa.

## Next Steps
- Build baseline model
- Train random forest regressor using hour, day of week, route_id, stop_id, etc...
- Evaluate against baseline
- Fix stop matching (limitation right now)
- Make into an interactive app

## Tech Stack
- Pandas
- Python
- Scipy
- Supabase
- Jupyter Notebook
- GTFS-Realtime
- Github Actions
