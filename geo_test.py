import fiona
import geopandas as gpd
from shapely.geometry import shape
from tabulate import tabulate

shapefile_path = r"C:\Users\TejasP1\Downloads\gm-jpn-all_u_2_2\gm-jpn-all_u_2_2\roadl_jpn.shp"

# Load and fix bad geometry records
features = []
with fiona.open(shapefile_path) as src:
    for feat in src:
        geom = feat.get("geometry")
        if geom and geom.get("coordinates") and len(geom.get("coordinates")) > 1:
            feat["geometry"] = shape(geom)
            features.append(feat)

# Convert to GeoDataFrame
gdf = gpd.GeoDataFrame.from_features(features)

# Filter to only national routes (rtt == 14)
national_routes = gdf[gdf['rtt'] == 14]

coords = national_routes.iloc[0].geometry.coords
print(list(coords))

# Drop geometry for table view
df = national_routes.drop(columns=["geometry"], errors="ignore")


# Show column names
print("Available columns:\n", df.columns.tolist())

# Print sample rows in tabular format
print(f"\nShowing {len(df)} national routes (rtt=14):\n")
print(tabulate(df.head(20), headers="keys", tablefmt="pretty"))