import fiona
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import shape

# Path to your shapefile
shapefile_path = r"C:\Users\TejasP1\Downloads\gm-jpn-all_u_2_2\gm-jpn-all_u_2_2\roadl_jpn.shp"

# Fix bad geometry records
features = []
with fiona.open(shapefile_path) as src:
    for feat in src:
        geom = feat.get("geometry")
        if geom and geom.get("coordinates") and len(geom.get("coordinates")) > 1:
            feat["geometry"] = shape(geom)
            features.append(feat)

# Create GeoDataFrame
gdf = gpd.GeoDataFrame.from_features(features)

# Filter only national highways (rtt == 14)
national_highways = gdf[gdf["rtt"] == 14]

# Plot
national_highways.plot(figsize=(10, 12), color="blue", linewidth=0.5)
plt.title("Japan National Highways (rtt = 14)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.axis("equal")  # Keep aspect ratio
plt.tight_layout()
plt.show()
