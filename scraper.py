import os
import json
import requests
from datetime import datetime

URL = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Incident_Locations_Current/FeatureServer/0/query"

PARAMS = {
    "where": "IncidentTypeCategory IN ('WF', 'CX')",
    "outFields": "*",
    "geometry": "-87.6,24.0,-79.5,31.5",
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
            name = props.get('IncidentName') or "Unnamed Fire"
            size = props.get('IncidentSize') or props.get('DailyAcres') or props.get('DiscoveryAcres')
            if not size: 
                size = 0.1
                
            containment = props.get('PercentContained') or 0

            props['IncidentName'] = name
            props['IncidentSize'] = size
            props['PercentContained'] = containment

            feature['properties'] = props
            cleaned_features.append(feature)

        # THE FIX: Generate a clean human-readable timestamp string
        timestamp_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        florida_geojson = {
            "type": "FeatureCollection",
            "generated_at": timestamp_str, # Embed timestamp into the file metadata
            "features": cleaned_features
        }

        os.makedirs("data", exist_ok=True)
        output_path = os.path.join("data", "wildfires.geojson")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(florida_geojson, f, indent=4)
            
        print(f"✅ SUCCESS: Perfectly mirrored live NIFC map at {timestamp_str}!")

    except Exception as e:
        print(f"❌ CRASH: {e}")

if __name__ == "__main__":
    run_scraper()