import os
import sys
import requests
import json
from datetime import datetime
import time

def main():
    print(f"[{datetime.now()}] Starting Wildfire & Smoke Data Scraper...")
    
    os.makedirs('data', exist_ok=True)
    florida_bbox = "-88.5,24.0,-79.0,31.5"
    cache_buster = int(time.time())

    # ==========================================
    # FAKE BROWSER HEADERS TO BYPASS FIREWALLS
    # ==========================================
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    # ==========================================
    # 1. FETCH WILDFIRE DATA FROM NIFC (SQL FILTER)
    # ==========================================
    nifc_base_url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0/query"
    
    nifc_params = {
        "where": "POOState = 'US-FL'",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",  
        "f": "geojson",
        "cb": cache_buster 
    }
    
    try:
        print("Fetching live wildfire data from NIFC...")
        response = requests.get(nifc_base_url, params=nifc_params, headers=headers, timeout=30)
        response.raise_for_status()
        fire_data = response.json()
        
        fire_data['generated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        features_count = len(fire_data.get('features', []))
        with open('data/wildfires.geojson', 'w') as f:
            json.dump(fire_data, f)
        print(f"✅ Wildfire data saved successfully ({features_count} active incidents found in Florida).")
        
    except Exception as e:
        print(f"❌ Error fetching wildfire data: {e}")

    # ==========================================
    # 2. FETCH SMOKE DATA FROM NOAA (SPATIAL FILTER)
    # ==========================================
    noaa_base_url = "https://services2.arcgis.com/C8EMgrsFcRFL6LrL/arcgis/rest/services/NOAA_Satellite_Smoke_Detection_(v1)/FeatureServer/0/query"
    
    noaa_params = {
        "where": "1=1",
        "geometry": florida_bbox,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",  
        "f": "geojson",
        "cb": cache_buster 
    }
    
    try:
        print("Fetching live smoke plume data from NOAA...")
        response = requests.get(noaa_base_url, params=noaa_params, headers=headers, timeout=30)
        response.raise_for_status()
        smoke_data = response.json()
        
        features_count = len(smoke_data.get('features', []))
        with open('data/smoke.geojson', 'w') as f:
            json.dump(smoke_data, f)
        print(f"✅ Smoke data saved successfully ({features_count} plumes found).")
        
    except Exception as e:
        print(f"❌ Error fetching smoke data: {e}")

    print(f"[{datetime.now()}] Scraping cycle complete.")

if __name__ == "__main__":
    main()