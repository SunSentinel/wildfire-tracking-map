import json
import csv
import logging
from datetime import datetime
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

FFS_ENDPOINT_URL = "https://ffs.firesponse.com/public/api/Incident/geojson"

# Browser-like headers to prevent request blocking
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://ffs.firesponse.com/public/"
}

def fetch_ffs_raw_data() -> dict:
    """Fetch raw GeoJSON payload from the Florida Forest Service API."""
    try:
        logging.info(f"Fetching FFS data from {FFS_ENDPOINT_URL}...")
        response = requests.get(FFS_ENDPOINT_URL, headers=REQUEST_HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP request error: {e}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse response JSON: {e}")
        return {}

def parse_incidents(raw_geojson: dict, active_only: bool = False) -> list[dict]:
    """
    Parse raw GeoJSON features into a clean list of incident dictionaries.
    
    :param raw_geojson: Dict containing the GeoJSON payload.
    :param active_only: If True, filters out closed/controlled incidents.
    """
    features = raw_geojson.get("features", [])
    parsed_incidents = []

    for feature in features:
        props = feature.get("properties", {})
        geom = feature.get("geometry", {})
        coords = geom.get("coordinates", [None, None])

        status = props.get("Status", "Unknown")

        # Optional filter for active fires only
        if active_only and status.lower() not in ["active", "contained"]:
            continue

        # Extract normalized attributes
        incident = {
            "id": props.get("Id"),
            "incident_number": props.get("Number"),
            "incident_code": props.get("Code"),
            "name": props.get("Name", "").strip(),
            "status": status,
            "category": props.get("Category", "Wildfire"),
            "acres": float(props.get("Size") or 0.0),
            "containment_percent": int(props.get("Contained") or 0),
            "county": props.get("AdminDivision"),
            "field_unit": props.get("AdminDivisionUpper"),
            "region": props.get("AdminDivisionArea"),
            "protecting_unit": props.get("protectingunit"),
            "resources_assigned": int(props.get("Resources") or 0),
            "discovery_time": props.get("Discovery"),
            "status_updated_time": props.get("StatusUpdatedTimestamp"),
            "latitude": coords[1] if len(coords) >= 2 else None,
            "longitude": coords[0] if len(coords) >= 2 else None,
            "is_obscured": props.get("IsObscured", False)
        }

        parsed_incidents.append(incident)

    logging.info(f"Successfully parsed {len(parsed_incidents)} incidents.")
    return parsed_incidents

def save_as_json(incidents: list[dict], filename: str = "ffs_wildfires.json"):
    """Export clean dataset as a standard JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"updated_at": datetime.utcnow().isoformat() + "Z", "incidents": incidents}, f, indent=2)
    logging.info(f"Saved dataset to {filename}")

def save_as_geojson(incidents: list[dict], filename: str = "ffs_wildfires.geojson"):
    """Re-export clean dataset as a standard GeoJSON FeatureCollection."""
    geojson_out = {
        "type": "FeatureCollection",
        "features": []
    }

    for inc in incidents:
        if inc["longitude"] is None or inc["latitude"] is None:
            continue

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [inc["longitude"], inc["latitude"]]
            },
            "properties": {k: v for k, v in inc.items() if k not in ["longitude", "latitude"]}
        }
        geojson_out["features"].append(feature)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(geojson_out, f, indent=2)
    logging.info(f"Saved GeoJSON dataset to {filename}")

def save_as_csv(incidents: list[dict], filename: str = "ffs_wildfires.csv"):
    """Export dataset to CSV format."""
    if not incidents:
        logging.warning("No incidents to write to CSV.")
        return

    fieldnames = incidents[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(incidents)
    logging.info(f"Saved CSV dataset to {filename}")

def main():
    # 1. Fetch raw payload
    raw_data = fetch_ffs_raw_data()
    if not raw_data:
        logging.error("Scraping failed: No data retrieved.")
        return

    # 2. Parse incidents (set active_only=True if you want to filter out old/closed fires)
    incidents = parse_incidents(raw_data, active_only=False)

    # 3. Export to desired format(s)
    save_as_json(incidents, "ffs_active_fires.json")
    save_as_geojson(incidents, "ffs_active_fires.geojson")
    save_as_csv(incidents, "ffs_active_fires.csv")

if __name__ == "__main__":
    main()