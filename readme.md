# Planet-Nomads

A set of tools to work with Planetscope imagery, for the Making Pastoralists Count project.


Currently working:

## Append Esri Imagery Dates

A function to query Esri's World ImageryCitations layer for the acquisition dates of the source imagery used create feature annotations.

The function accepts:

* `service_url`: the current url for the Esri World Imagery Service
* `geojson_features`: valid geojson file containing the target features
* `zoom_level`: the zoom level used to query the imagery service citations, since imagery sources change at different zoom levels. THis should be expressed in typical web mercator zoom levels.
* `output_path`: the path and filename of the output geojson file

`append_imagery_dates(service_url, geojson_features, zoom_level, output_path)`

The function should return a geojson file as `./output/{geojson_features}_appended.geojson` with all `FIELDS:values` for the Citations layer features that contain the centroid of each of the `geojson_features`, appended as new properties.
```python
# Example usage
append_imagery_dates(
    service_url="https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer",
    geojson_features="../data/village_points_esri_imagery_08092024.geojson",
    zoom_level=14,
    output_path="../output/appended_features.geojson")
```

## check_distinct_dates(geojson_features, output_path) 

Checks the output of `append_imagery_dates()` to determine the number of distinct values in the `SRC_DATE` property. The function then writes these distinct dates to a `appended_features_distinct_dates.json` file.



- **Extracting `SRC_DATE` Values**: The function iterates through all features in the provided GeoJSON file, extracting the `SRC_DATE` values.
- **Using a Set**: A set is used to automatically filter out duplicate `SRC_DATE` values, ensuring only distinct dates are recorded.
- **Saving Output**: The distinct dates are saved as a sorted list in a `appended_features_distinct_dates.json` file in the specified output path.
- **Output**: The JSON output contains both the list of distinct dates and a count of how many distinct dates were found.

### Usage:

- After running the `append_imagery_dates()` function, you can use `check_distinct_dates()` to generate a file listing all distinct `SRC_DATE` values.
- The resulting `appended_features_distinct_dates.json` will be stored in the `output_path` directory.

```python
# Example usage
check_distinct_dates(
    geojson_features="../output/appended_features.geojson",
    output_path="../output"
)
```

##  `create_aoi` 

function that creates a minimum bounding geometry for the features from the `geojson_features` and writes the resulting AOI (Area of Interest) to an `aoi.geojson` file at the specified `output_path`.



### Key Points:

- **Loading GeoJSON Features**: The function starts by loading the input GeoJSON file.
- **Geometry Collection**: It collects all valid geometries from the features.
- **Minimum Bounding Geometry**: Using `shapely.ops.unary_union`, it combines all the geometries into one, and then computes the minimum bounding geometry (convex hull) that contains all the geometries.
- **Output GeoJSON**: The function creates a new GeoJSON structure with the bounding geometry and saves it as `aoi.geojson` in the specified `output_path`.
- **Error Handling**: If no valid geometries are found in the input, the function raises a `ValueError`.

### Usage:

- Run the `create_aoi()` function with the paths to your input GeoJSON file and the desired output directory.
- The function will generate an `aoi.geojson` file containing the minimum bounding geometry for all the features in your input GeoJSON.

```python
# Example usage
create_aoi(
    geojson_features="../data/village_points_esri_imagery_08092024.geojson",
    output_path="../output"
)
```

## `search_planet_imagery()` 

takes the output from the `check_distinct_dates()` function, along with a GeoJSON file representing a single AOI, to perform searches for PlanetScope imagery. The function will store the results as JSON files and provide a summary of the searches.


1. **Load AOI and Dates**:
   - The AOI is loaded from the provided GeoJSON file.
   - The distinct dates are loaded from the `appended_features_distinct_dates.json` file.

2. **Date Range Calculation**:
   - For each distinct date, a search is performed for imagery within one week before and one week after the date.

3. **Search and Save Results**:
   - The function queries the Planet API for imagery within the calculated date range and the AOI.
   - The results for each search are saved as JSON files in the `search_results` directory under the specified `output_path`.

4. **Summary of Results**:
   - The function prints a summary that includes the distinct dates, the date range for each search, and the number of items found in each search.
   - The summary is also saved as a JSON file named `search_summary.json` in the specified `output_path`.

### Usage:

You can call the `search_planet_imagery()` function with the path to your `appended_features_distinct_dates.json`, the AOI GeoJSON file, and the desired output path. The function will perform the searches, store the results, and print a summary.

```
# Example usage
search_planet_imagery(
    distinct_dates_file="../output/appended_features_distinct_dates.json",
    aoi_geojson="../output/aoi.geojson",
    output_path="../output"
)
```