import requests
import os
import pandas as pd
import zipfile
import io
from datetime import datetime, timezone
from google.transit import gtfs_realtime_pb2 # this lib parses protobuf binary data into 
# something readable
from supabase import create_client # connects and lets you write to the database

VEHICLE_POSITIONS_URL = "https://data.calgary.ca/download/am7c-qe3u/application%2Foctet-stream"
GTFS_URL = "https://data.calgary.ca/download/npk7-z3bj/application%2Fx-zip-compressed"

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# reading from GITHUB Secrets and looking up the values stored using os.environ
supabase = create_client(SUPABASE_URL,SUPABASE_KEY) # connection th supabase database

# create all the paths and dataframes needed for extraction 

def load_static_gtfs(): # added new function to also fetch from the GTFS URL
    response = requests.get(GTFS_URL)
    z = zipfile.ZipFile(io.BytesIO(response.content))
    trips = pd.read_csv(z.open('trips.txt'))
    return dict(zip(trips['trip_id'].astype(str),trips['route_id'].astype(str)))

def get_feed(): # this function calls the api, then converts response to a python object
# and then returns it
    response = requests.get(VEHICLE_POSITIONS_URL)
    feed = gtfs_realtime_pb2.FeedMessage() # initialize empty feed containrt
    feed.ParseFromString(response.content) #parse content into feed
    return feed

def save_to_supabase(feed,trip_to_route):
    rows = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            v = entity.vehicle
            trip_id = v.trip.trip_id

            route_id = v.trip.route_id if v.trip.route_id else trip_to_route.get(str(trip_id), None)

            
            rows.append({
                "timestamp": datetime.fromtimestamp(feed.header.timestamp, tz=timezone.utc).isoformat(),
                "trip_id": trip_id,
                "route_id": route_id,
                "stop_id": str(v.current_stop_sequence) if v.current_stop_sequence else None,
                "delay_seconds": None,
                "schedule_relationship": v.trip.schedule_relationship,
                "lat": v.position.latitude if v.HasField('position') else None,
                "lon": v.position.longitude if v.HasField('position') else None
            })

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        supabase.table("delays").insert(batch).execute()
        print(f"Inserted batch {i//batch_size + 1}, {len(batch)} rows")
    
    print(f"Done, saved {len(rows)} total rows")

trip_to_route = load_static_gtfs()
feed = get_feed() # fetch data
save_to_supabase(feed,trip_to_route) # save to supabase