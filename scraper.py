import requests
import os
import pandas as pd
import zipfile
import io
import numpy as np
from scipy.spatial import cKDTree # uses indexing 
from datetime import datetime, timezone
from google.transit import gtfs_realtime_pb2 # this lib parses protobuf binary data into 
# something readable
from supabase import create_client # connects and lets you write to the database

VEHICLE_POSITIONS_URL = "https://data.calgary.ca/download/am7c-qe3u/application%2Foctet-stream"
GTFS_URL = "https://data.calgary.ca/download/npk7-z3bj/application%2Fx-zip-compressed"

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_PRIVATE_KEY = os.environ["SUPABASE_PRIVATE_KEY"]

# reading from GITHUB Secrets and looking up the values stored using os.environ
supabase = create_client(SUPABASE_URL,SUPABASE_PRIVATE_KEY) # connection th supabase database

# create all the paths and dataframes needed for extraction 

def load_static_gtfs(retries=3): # added new function to also fetch from the GTFS URL
    # error handling

    for attempt in range(retries):
        try:
            print("Downloading GTFS...")
            response = requests.get(GTFS_URL, timeout =30)
            response.raise_for_status()
            z = zipfile.ZipFile(io.BytesIO(response.content))
            
            trips = pd.read_csv(z.open('trips.txt'))
            stops = pd.read_csv(z.open('stops.txt'))
            stop_times = pd.read_csv(z.open('stop_times.txt'))

            # fetch the route_id from the trip_id where key is the trip_id and val is route_id
            trip_to_route = dict(zip(trips['trip_id'].astype(str),trips['route_id'].astype(str)))
            trip_to_stoptimes = stop_times.groupby('trip_id')['stop_id'].apply(list).to_dict()
           
            return trip_to_route, stops, trip_to_stoptimes
        
        except Exception as e:
            print(f"Attempt {attempt +1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None, None, None

def nearest_stop(lat, lon, trip_id, stops, trip_to_stoptimes):
    valid_stop_ids = trip_to_stoptimes.get(str(trip_id))
    if not valid_stop_ids:
        return None
    valid_stop_ids = [str(s) for s in valid_stop_ids]
    valid_stops = stops[stops['stop_id'].astype(str).isin(valid_stop_ids)]
    if valid_stops.empty:
        return None
    stop_coords = valid_stops[['stop_lat', 'stop_lon']].values
    tree = cKDTree(stop_coords)
    distance, index = tree.query([lat, lon])
    nearest_stop_id = valid_stops['stop_id'].iloc[index]
    return str(nearest_stop_id) if distance < 0.05 else None

def get_feed(): # this function calls the api, then converts response to a python object
# and then returns it
    response = requests.get(VEHICLE_POSITIONS_URL)
    feed = gtfs_realtime_pb2.FeedMessage() # initialize empty feed containrt
    feed.ParseFromString(response.content) #parse content into feed
    return feed

def save_to_supabase(feed,trip_to_route,stops,trip_to_stoptimes):
    rows = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            v = entity.vehicle
            trip_id = v.trip.trip_id

            route_id = v.trip.route_id if v.trip.route_id else trip_to_route.get(str(trip_id), None)

            lat = v.position.latitude if v.HasField('position') else None
            lon = v.position.longitude if v.HasField('position') else None
            #debugging
            if lat and lon:
                stop_id = nearest_stop(lat,lon,trip_id,stops,trip_to_stoptimes)
            
            rows.append({
                "timestamp": datetime.fromtimestamp(feed.header.timestamp, tz=timezone.utc).isoformat(),
                "trip_id": trip_id,
                "route_id": route_id,
                "stop_id": stop_id,
                "delay_seconds": None,
                "schedule_relationship": v.trip.schedule_relationship,
                "lat": lat,
                "lon": lon     
            })
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        supabase.table("delays").insert(batch).execute()
        print(f"Inserted batch {i//batch_size + 1}, {len(batch)} rows")
    
    print(f"Done, saved {len(rows)} total rows")

trip_to_route, stops, trip_to_stoptimes = load_static_gtfs()
if trip_to_route is None or stops is None or trip_to_stoptimes is None:
    print("Failed to load GTFS data after multiple attempts.")
    exit(0)

feed = get_feed() # fetch data
save_to_supabase(feed,trip_to_route,stops,trip_to_stoptimes) # save to supabase
