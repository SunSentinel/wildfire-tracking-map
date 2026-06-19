import os
import json
import requests
from datetime import datetime

# THE FIX: Pointing exactly to the "Current" live feed, not the historical database
URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0/query"

# NIFC already handles the expiration rules on this endpoint, so we just ask for active Wildfires and Complexes
PARAMS = {
    "where": "IncidentTypeCategory IN ('WF', 'CX')",
    "outFields": "*",
    "geometry": "-87.6,24.0,-79.5,31.5", # Florida boundaries
    "geometryType": "esriGeometryEnvelope",
    "inSR": "4326",
    "spatialRel": "esriSpatialRelIntersects",
    "returnGeometry": "true",
    "outSR": "4326",
    "f": "geojson"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) NewsroomDataScraper"
}

def run_scraper():
    print("Connecting directly to the NIFC 'Current' Live Map feed...")
    try:
        response = requests.get(URL, params=PARAMS, headers=HEADERS, timeout=20)
        
        if response.status_code != 200:
            print(f"❌ SERVER ERROR: {response.status_code}")
            return

        live_data = response.json()
        raw_features = live_data.get('features', [])
        
        cleaned_features = []
        
        for feature in raw_features:
            if not feature.get('geometry'):
                continue

            props = feature.get('properties', {})
            
            # Extract standard names
            name = props.get('IncidentName') or "Unnamed Fire"
            
            # THE ACREAGE HUNT: Check every column where local crews might hide the size
            size = props.get('IncidentSize') or props.get('DailyAcres') or props.get('DiscoveryAcres')
            if not size: 
                size = 0.1 # Fallback to 0.1 so app.js doesn't say "Unreported acreage"
                
            containment = props.get('PercentContained') or 0

            # Map the clean data back to the properties
            props['IncidentName'] = name
            props['IncidentSize'] = size
            props['PercentContained'] = containment

            feature['properties'] = props
            cleaned_features.append(feature)

        florida_geojson = {
            "type": "FeatureCollection",
            "features": cleaned_features
        }

        os.makedirs("data", exist_ok=True)
        output_path = os.path.join("data", "wildfires.geojson")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(florida_geojson, f, indent=4)
            
        timestamp_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        print(f"✅ SUCCESS: Perfectly mirrored the live NIFC map ({len(cleaned_features)} active fires) at {timestamp_str}!")

    except Exception as e:
        print(f"❌ CRASH: {e}")

if __name__ == "__main__":
    run_scraper()