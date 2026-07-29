from supabase import create_client
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv() # load environment variables from .env file

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url,key)

def fetch_data_from_supabase(table_name):
    all_data = []
    page_size = 1000
    offset = 0

    while True:
        response = supabase.table("delays").select("*").range(offset, offset + page_size - 1).execute()
        data = response.data
        if not data:
            break
        all_data.extend(data)
        offset += page_size
    return pd.DataFrame(all_data)

if __name__ == "__main__":
    df = fetch_data_from_supabase("delays")
    df.to_csv("data/transit_delays.csv", index=False)
    print("Data fetched and saved to data/transit_delays.csv")