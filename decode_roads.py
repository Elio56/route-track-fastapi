import requests
import polyline
import time

# 🔑 Replace with your actual Google API key
API_KEY = "AIzaSyCFo7709M-ddaTvahV_wG1Buh4lPjRFhvQ" 

# 🧭 Input: your traveled route as polyline
your_polyline = "ctsxEyttsYzD{AjAkAtB{CbCgDhCsDlAsAl@y@fCyBhCyDf@g@n@e@^Qh@SVGn@I|CM\\An@Gn@UvAs@h@a@fAiApB_C|BgCVa@FYt@iFPsAXqE@uAG{Ag@qFa@sE_@aF@{@J_Ah@wAVq@Z_Ap@wDz@oF\\wCJg@Pe@rBgDL]Nq@Jw@@m@AoADY?c@GwCCoCAcCGw@Ic@?WQcAMmACcEKoBO{BQ_D@oAFs@Li@Vs@Ra@^cAPs@Fc@H_ADi@HiB?i@Ek@G]Wq@S]][s@_@kCu@sBm@}@]_@OeA]g@GUA]?sANoDj@eFx@_AFg@Ei@K{Ai@_AQOCECICeAMeBYk@S[QWWYa@Oe@Ic@Ee@?u@FeBAg@Dq@Bq@HaARuAb@aCP}AJ_B\\yJBkAL}ALu@^w@`AgAJ[HMdAeAJMVi@La@?i@ASIUSWQG]Cc@Ag@KDq@T}DJgC?U^BrAJv@F`Gj@jE`@z@LnALbIr@"

# 🚧 API: Snap the polyline to roads
def snap_to_roads(encoded_polyline, sample_rate):
    # Decode the polyline into a list of lat/lng points
    decoded = polyline.decode(encoded_polyline)

    print(f"Original points: {len(decoded)}")

    # Sample every Nth point
    sampled_points = decoded[::sample_rate]
    print(f"Sampled {len(sampled_points)} points (every {sample_rate}th)")

    # Trim to max 100 points if needed (Google API limit)
    # if len(sampled_points) > 100:
    #     sampled_points = sampled_points[:100]
    #     print(f"Trimmed to 100 points due to API limit.")

    # Format for API: lat,lng|lat,lng|...
    path = "|".join([f"{lat},{lng}" for lat, lng in sampled_points])

    # Send request
    url = f"https://roads.googleapis.com/v1/snapToRoads?path={path}&interpolate=true&key={API_KEY}"
    print(f"Requesting: {url[:100]}... [length: {len(url)}]")

    response = requests.get(url)
    response.raise_for_status()
    return response.json()



# 🗺️ API: Get road name from placeId
def get_road_name(place_id):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?place_id={place_id}&key={API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if data["status"] == "OK":
        for comp in data["results"][0]["address_components"]:
            if "route" in comp["types"]:
                return comp["long_name"]
        return data["results"][0]["formatted_address"]  # fallback
    return "Unknown"

# 🚀 Run
def main():
    print("Snapping to roads...")
    snap_data = snap_to_roads(your_polyline, sample_rate=5)


    print("Getting road names...\n")
    results = []
    for point in snap_data.get("snappedPoints", []):
        loc = point["location"]
        place_id = point.get("placeId", "")
        lat, lng = loc["latitude"], loc["longitude"]
        road_name = get_road_name(place_id)
        results.append((lat, lng, place_id, road_name))
        print(f"{lat:.6f}, {lng:.6f} | {road_name}")
        time.sleep(0.1)  # to avoid rate limit

    # Optionally save to CSV
    import csv
    with open("traveled_roads.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Latitude", "Longitude", "PlaceID", "Road Name"])
        writer.writerows(results)

    print("\nSaved to traveled_roads.csv")

if __name__ == "__main__":
    main()
