

#general packages
import os
import json
import glob
import asyncio
import requests
import nest_asyncio
import matplotlib.pyplot as plt
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from google.colab import userdata

#geospatial packages
import rasterio
import geopandas as gpd
from shapely.geometry import shape
from shapely.geometry import shape, Point
from shapely import wkt
from shapely.ops import unary_union
import folium


#planet SDK
from planet import Auth, reporting, Session, OrdersClient, order_request, data_filter



# append_imagery_dates() queries Esri World Imagery Citations layer for metadata, including acquisition dates

def append_imagery_dates(service_url, geojson_features, zoom_level, output_path):
    # Define the Citations layer URL
    citations_layer_url = f"{service_url}/{zoom_level}/query"

    # Load the GeoJSON features
    with open(geojson_features, 'r') as f:
        geojson_data = json.load(f)

    total_features = len(geojson_data['features'])
    processed_count = 0
    last_reported_progress = 0

    # Iterate over each feature to query the Citations layer
    for i, feature in enumerate(geojson_data['features']):
        geometry = feature.get('geometry')
        if geometry is None:
            print(f"Skipping feature {i} due to missing geometry.")
            continue

        processed_count += 1  # Increment processed count for valid geometries

        # Get the centroid of the feature
        geometry = shape(geometry)
        centroid = geometry.centroid

        # Define the parameters for the query
        params = {
            "f": "json",  # Output format
            "geometryType": "esriGeometryPoint",  # We are using the centroid (point)
            "spatialRel": "esriSpatialRelIntersects",  # Spatial relationship
            "returnGeometry": "false",  # We only need attributes
            "outFields": "*",  # Retrieve all fields
            "geometry": json.dumps({
                "x": centroid.x,
                "y": centroid.y,
                "spatialReference": {"wkid": 4326}
            }),
            "inSR": "4326",  # Input spatial reference (WGS84)
        }

        # Send the request to the ArcGIS service
        response = requests.get(citations_layer_url, params=params)

        # Check for successful response
        if response.status_code == 200:
            data = response.json()
            # If features are found, append the citation attributes to the GeoJSON feature
            if 'features' in data and len(data['features']) > 0:
                for field, value in data['features'][0]['attributes'].items():
                    feature['properties'][field] = value
        else:
            print(f"Error querying service: {response.status_code}, {response.text}")

        # Calculate and report progress in 10% increments
        progress = int((processed_count / total_features) * 100)
        if progress >= last_reported_progress + 10:
            last_reported_progress = (progress // 10) * 10
            print(f"{last_reported_progress}...", end="", flush=True)
    
    # Print completion message
    print("100 - done.")

    # Output the modified GeoJSON to the specified path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(geojson_data, f, indent=2)
    
    print(f"Output saved to {output_path}")



# check_distinct_dates() extracts distinct SRC_DATE values from the GeoJSON features

def check_distinct_dates(geojson_features, output_path):
    # Load the GeoJSON features
    with open(geojson_features, 'r') as f:
        geojson_data = json.load(f)

    # Extract SRC_DATE values
    src_dates = set()  # Use a set to automatically handle distinct values
    for feature in geojson_data['features']:
        src_date = feature['properties'].get('SRC_DATE')
        if src_date:
            src_dates.add(src_date)

    # Convert the set to a sorted list
    distinct_dates = sorted(list(src_dates))

    # Prepare the output data
    output_data = {
        "distinct_dates": distinct_dates,
        "count": len(distinct_dates)
    }

    # Define the output file path
    output_file = os.path.join(output_path, "appended_features_distinct_dates.json")

    # Save the distinct dates to the output file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Distinct dates output saved to {output_file}")
    
    
# planet_auth() authenticates with the Planet API using the PL_API_KEY environment variable

    def planet_auth():
    # Check if the Planet API Key is set as an environment variable
    if 'PL_API_KEY' in os.environ:
        API_KEY = os.environ['PL_API_KEY']
    else:
        API_KEY = input("PASTE_API_KEY_HERE AND HIT RETURN:   ")
        os.environ['PL_API_KEY'] = API_KEY

    # Authenticate with the Planet API
    client = Auth.from_key(API_KEY)
    
    return client

# Example usage
client = planet_auth()