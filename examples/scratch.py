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

#geospatial packages
import rasterio
import geopandas as gpd
from shapely.geometry import shape
from shapely.ops import unary_union
import folium


#planet SDK
from planet import Auth, reporting, Session, OrdersClient, order_request, data_filter


# create a small helper function to print out JSON with proper indentation.
def indent(data):
    print(json.dumps(data, indent=2))

with open("lakelagunita.geojson") as f:
    geom_all = json.loads(f.read())['features'][0]['geometry']
geom_large = {

print(geom_all)

# Define the filters we'll use to find our data

item_types = ["PSScene"]

#Geometry filter
geom_filter = data_filter.geometry_filter(geom_large)

#Date range filter
date_range_filter = data_filter.date_range_filter(
    "acquired", gt = datetime(month=12, day=10, year=2022),
    lt = datetime(month=9, day=30, year=2023))
#Cloud cover filter
cloud_cover_filter = data_filter.range_filter('clear_percent', gt = 80)

#Combine all of the filters
combined_filter = data_filter.and_filter([geom_filter, date_range_filter, cloud_cover_filter])

async with Session() as sess:
    cl = sess.client('data')
    item_list = [i async for i in cl.search(search_filter=combined_filter, item_types=item_types,limit=500)]
    
    
## Print the `combined_filter`
combined_filter

# Set the `item_types`
item_type = "PSScene"

# API request object
search_request = {
  "item_types": [item_type],
  "filter": combined_filter
}
# order with the SDK
async with Session() as sess:
    cl = sess.client('data')
    item_list = [i async for i in cl.search(search_filter=combined_filter, item_types=item_types,limit=500)]
    
    
   # Print the # of items in your Search Result
    len(item_list)
    
for item in item_list:
    print(item['id'], item['properties']['item_type'])
    
    
# Save all of our scene footprints as a GeoJSON file    
scene_geoms = {
  "type": "FeatureCollection",
  "features": []
}

if not os.path.isdir('output'):
    os.mkdir('output')
else:
    if os.path.isfile('output/results01.geojson'):
        os.remove('output/results01.geojson')

with open('output/results01.geojson','w') as f:
    for item in item_list:
        geom_out =     {
          "type": "Feature",
          "properties": item['properties'],
          "geometry": item['geometry']
        }
        scene_geoms['features'].append(geom_out)
    jsonStr = json.dumps(scene_geoms)
    f.write(jsonStr)
    f.close()
   
# Print the first item in the item_list 
item_list[0]

# group images by date for ordering
grouped_items = []
current_group = []
#reverse the list since it comes in last date first
reversed_items = sorted(item_list, key=lambda item: item['properties']['acquired'])

#Select the earliest item
group_start_date = datetime.strptime(reversed_items[0]['properties']['acquired'], "%Y-%m-%dT%H:%M:%S.%fZ")

for item in reversed_items:
    time_object = item['properties']['acquired']
    time = datetime.strptime(time_object, "%Y-%m-%dT%H:%M:%S.%fZ")

    if time < group_start_date + timedelta(days=30):
        current_group.append(item)

    else:
        grouped_items.append(current_group)
        current_group = [item]
        group_start_date = time
if current_group:
    grouped_items.append(current_group)

print(len(grouped_items))

# sort on clear percent

sorted_items = []
for group in grouped_items:
    sorted_group = sorted(group, key=lambda item: item['properties']['clear_percent'], reverse=True)
    sorted_items.append(sorted_group)


for item in sorted_items[0]:
    print(item['properties']['clear_percent'])
    

# Function for calculating the overlap between two geometries   
def get_overlap(geometry1, geometry2):
    """Calculate the area of overlap between two geometries."""
    shape1 = shape(geometry1)
    shape2 = shape(geometry2)

    # Compute the intersection of the two geometries.
    intersection = shape1.intersection(shape2)

    return intersection


#Evaluate coverage of geom_all for each week     
minimum_sorted_list = []


for week_items in sorted_items:
    intersection = False
    weekly_minimum_list = []
    for item in week_items:
        #for each scene itterate through every geometry and check if it overlaps with the scene
        overlap = get_overlap(geom_all, item['geometry'])
        if intersection:
            new_intersection = unary_union([overlap,intersection])

            #If the new interseciton is bigger then the old then add the scene to the order
            if round(new_intersection.area, 8) > round(intersection.area, 8):
                intersection = new_intersection
                weekly_minimum_list.append(item)
        else:
            if overlap.area > 0:
                intersection = overlap
                weekly_minimum_list.append(item)
    print(len(week_items), " to ", len(weekly_minimum_list))

    if len(weekly_minimum_list) > 0:
        minimum_sorted_list.append(weekly_minimum_list)    
        
# evaluate cloud cover before and after

for item in sorted_items[0]:
    print(item['properties']['clear_percent'])
print("Now")
for item in minimum_sorted_list[0]:
    print(item['properties']['clear_percent'])
    
# evaluate clarity of final selections
for group in minimum_sorted_list:
    clear = []
    for item in group:
        clear.append(int(item['properties']['clear_percent']))
    print(sum(clear)/len(clear))
    
# reorder the scenes by clarity for clear on top mosaic
order_items = []
for group in minimum_sorted_list:
    sorted_group = sorted(group, key=lambda item: item['properties']['clear_percent'])
    order_items.append(sorted_group)

for item in order_items[0]:
    print(item['properties']['clear_percent'])
    
# Create an `assemble_order()' function and test it

async def assemble_order(name,item_ids):
    products = [
        order_request.product(item_ids, 'analytic_udm2', 'PSScene')
    ]

    clip = order_request.clip_tool(aoi=geom_all)
    bandmath = order_request.band_math_tool(b1='(b2-b4)/(b2+b4)*100+100', pixel_type='8U')
    composite = order_request.composite_tool()



    tools = [clip,bandmath,composite]

    request = order_request.build_request(
        name, products=products, tools=tools)
    return request

request =  await assemble_order("test",['20230207_180504_51_24b6'])

request

# Create a function to order imagery
async def do_order(request):
    async with Session() as sess:
        cl = OrdersClient(sess)
        #with reporting.StateBar(state='creating') as bar:
        order = await cl.create_order(request)
        #bar.update(state='created', order_id=order['id'])

        await cl.wait(order['id'],max_attempts=0)#, callback=bar.update_state)
        os.mkdir(request['name'])

        # if we get here that means the order completed. Yay! Download the files.
        await cl.download_order(order['id'],directory=request['name'])


# Create all orders
order_list = []
folder_list= []
name = "lake_lagunita_cloud_"
for group in order_items:
    ids = []
    order_name = name + group[0]['properties']['acquired'][:10]
    print(order_name)
    folder_list.append(order_name)
    for item in group:
        ids.append(item['id'])
    order_list.append(await assemble_order(order_name,ids))
print(len(order_list))

# Submit and monitor orders
# asyncio, the Python package that provides the API to run and manage coroutines

nest_asyncio.apply()

#now all you need to do to have them run in parallel is to create an array of order requests
async with Session() as sess:
    tasks = [do_order(o) for o in order_list]
    await asyncio.gather(*tasks)
    
