# Calgary-Transit-Delay-and-Timing-Predictor

## Overview
The Calgary Transit Delay and Timing Predictor collects real-time GTFS transit data every 3-4 hours using GitHub Actions. Information collected includes the timestamp, trip_id, route_id, stop_id and the position of the vehicle which is used to calculate delays and then that is used to make a machine learning model to predict delays based on training data. 

## Motivation
As someone who heavily relies on transit, using the transit app is not always reliable and cannot predict all delays. So I thought that using a machine learning algorithm on transit data would allow for a more accurate representation of transit delays. Right now this is only used for transit buses but will be used for C-trains in the near future.

## What has been done so far
- Automated scraper pulls GTFS-Realtime vehicle positions useful for delay calculations every 3-4 hours via GitHub Actions.
- Cleaned and preprocessed data pulled from Supabase( 74k rows) using Juypyter Notebooks and Pandas.
- Calculated delay in seconds and minutes using the time from the timestamp and the arrival time from transit data. A negative value indicates its earlier than scheduled and vice-versa.
- Built a baseline model which had an MAE of 5.36 min and then made a Random Forest regressor that had an MAE of 4.46 min
- Fixed spatial matching to only record stops that are scheduled for specific trip id
  
## Next Steps
- Re-collect data as stop-matching is now fixed
- Use a different algorithm/ fine tune for greater results
- Add more features such as weather, events, holidays 
- Make into an interactive app

## Tech Stack
- Pandas
- Python
- SciPy
- Supabase
- Jupyter Notebook
- GTFS-Realtime
- GitHub Actions
- Scikit-learn
