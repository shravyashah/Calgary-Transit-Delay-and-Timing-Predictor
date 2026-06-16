import requests
import os
from datetime import datetime
from google.transit import gtfs_realtime_pb2 # this lib parses protobuf binary data into 
# something readable
from supabase import create_client # connects and lets you write to the database

VEHICLE_POSITIONS_URL = "https://data.calgary.ca/download/gs4m-mdc2/application%2Foctet-stream"

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
# reading from GITHUB Secrets and looking up the values stored using os.environ
supabase = create_client(SUPABASE_URL,SUPABASE_KEY) # connection th supabase database


def get_feed(): # this function calls the api, then converts response to a python object
# and then returns it
    response = requests.get(VEHICLE_POSITIONS_URL)
    feed = gtfs_realtime_pb2.FeedMessage() # initialize empty feed containrt
    feed.ParseFromString(response.content) #parse content into feed
    return feed

def save_to_supabase(feed):
    rows = [] # empty list that will hold bus trips
    for entity in feed.entity: # loops through every active trip in the feed
        if entity.HasField('trip_update'): # if it has an update
            tu = entity.trip_update # shorthand for less typing 
            for stop in tu.stop_time_update: # loops through each stop
                delay = stop.arrival.delay if stop.HasField('arrival') else None 
                # check to see if there has been a delay
                rows.append({ # add to the list with different columns that hold data
                    "timestamp": datetime.now().isoformat(),
                    "trip_id": tu.trip.trip_id,
                    "route_id": tu.trip.route_id,
                    "stop_id": stop.stop_id,
                    "delay_seconds": delay,
                    "schedule_relationship": tu.trip.schedule_relationship
                })
    supabase.table("delays").insert(rows).execute # insert rows into supabase
    print(f"Done, saved {len(rows)}rows")

    result = supabase.table("delays").insert(rows).execute()
    print(f"Done, saved {len(rows)} rows")
    print(f"Result: {result}")
    
feed = get_feed() # fetch data
save_to_supabase(feed) # save to supabase