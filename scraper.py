import os
import json
import requests

# NIFC IRWIN Live Feed for Current Wildfire Incidents
# Structured with explicit spatial variables to satisfy strict ArcGIS server requirements.
URL = "https://services3.arcgis.com/T4gQDgGgFlphOOvF/arcgis/rest/services/CY_Wildfire_Locations_ToDate/FeatureServer/0/query"
PARAMS = {
    "where": "State = 'FL' AND FireOutDate IS NULL",
    "outFields": "IncidentName,DailyAcres,PercentContained,DiscoveryDate",
    "returnGeometry": "true",                # Forces server to send coordinate shapes
    "spatialRel": "esriSpatialRelIntersects",
    "outSR": "4326",                         # Forces coordinates into standard Lat/Lng mapping format
    "f": "geojson"                           # Packages output cleanly for Leaflet
}
HEADERS = {
    "User-Agent": "(sunsentinel.com, newsroom-data-team@sunsentinel.com)"
}

def run_scraper():
    print("Connecting to the National Interagency Fire Center (NIFC)...")
    try:
        response = requests.get(URL, params=PARAMS, headers=HEADERS, timeout=20)
        
        if response.status_code != 200:
            print(f"Error: NIFC server returned status {response.status_code}")
            print(f"Server response snippet: {response.text[:200]}")
            return
            
        fire_data = response.json()
        
        # Ensure 'data' directory exists locally inside wildfire-tracking-map
        os.makedirs("data", exist_ok=True)
        output_path = os.path.join("data", "wildfires.geojson")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(fire_data, f, indent=4)
            
        print(f"Wildfire sync complete. Saved: {output_path} ({len(fire_data.get('features', []))} active fires found)")
        
    except Exception as e:
        print(f"Network or parsing exception: {e}")

if __name__ == "__main__":
    run_scraper()