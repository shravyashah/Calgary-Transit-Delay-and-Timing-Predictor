import requests
import sqlite3
import pandas as pd
from datetime import datetime
from google.transit import gtfs_realtime_pb2

VEHICLE_POSITIONS_URL = "https://data.calgary.ca/download/gs4m-mdc2/application%2Foctet-stream"

conn = sqlite3.connect('trip_updates.db')
df = pd.read_sql('SELECT * FROM delays LIMIT 20', conn)
print(df)
print("\nDelay stats:")
print(df['delay_seconds'].describe())

def get_feed():
    response = requests.get(VEHICLE_POSITIONS_URL)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return feed

def save_to_db(feed):
    conn = sqlite3.connect('transit_delays.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS delays (
            timestamp TEXT,
            trip_id TEXT,
            route_id TEXT,
            stop_id TEXT,
            delay_seconds INTEGER,
            schedule_relationship INTEGER
        )
    ''')
    
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            tu = entity.trip_update
            trip_id = tu.trip.trip_id
            route_id = tu.trip.route_id
            for stop in tu.stop_time_update:
                delay = stop.arrival.delay if stop.HasField('arrival') else None
                cursor.execute('INSERT INTO delays VALUES (?,?,?,?,?,?)', (
                    datetime.now().isoformat(),
                    trip_id,
                    route_id,
                    stop.stop_id,
                    delay,
                    tu.trip.schedule_relationship
                ))
    
    conn.commit()
    conn.close()
    print(f"Done, saved {len(feed.entity)} trips")

feed = get_feed()
save_to_db(feed)