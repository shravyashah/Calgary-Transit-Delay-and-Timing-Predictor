import requests
import os
from datetime import datetime
from google.transit import gtfs_realtime_pb2 # this lib parses protobuf binary data into 
# something readable
from supabase import create_client # connects and lets you write to the database

VEHICLE_POSITIONS_URL = "https://data.calgary.ca/download/am7c-qe3u/application%2Foctet-stream"

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

print(f"Connecting to: {SUPABASE_URL}")
print(f"Connecting to: {SUPABASE_KEY}")
# reading from GITHUB Secrets and looking up the values stored using os.environ
supabase = create_client(SUPABASE_URL,SUPABASE_KEY) # connection th supabase database


def get_feed(): # this function calls the api, then converts response to a python object
# and then returns it
    response = requests.get(VEHICLE_POSITIONS_URL)
    feed = gtfs_realtime_pb2.FeedMessage() # initialize empty feed containrt
    feed.ParseFromString(response.content) #parse content into feed
    return feed

def save_to_supabase(feed):
    rows = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            v = entity.vehicle
            rows.append({
                "timestamp": datetime.now().isoformat(),
                "trip_id": v.trip.trip_id,
                "route_id": v.trip.route_id if v.trip.route_id else None,
                "stop_id": str(v.current_stop_sequence) if v.current_stop_sequence else None,
                "delay_seconds": None,
                "schedule_relationship": v.trip.schedule_relationship
            })

    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        result = supabase.table("delays").insert(batch).execute()
        print(f"Inserted batch {i//batch_size + 1}, {len(batch)} rows")
    
    print(f"Done, saved {len(rows)} total rows")

    result = supabase.table("delays").insert(rows).execute()
    print(f"Done, saved {len(rows)} rows")
    print(f"Result: {result}")

feed = get_feed() # fetch data
save_to_supabase(feed) # save to supabase