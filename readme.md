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