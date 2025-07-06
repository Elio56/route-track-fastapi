import requests
import polyline
import re

API_KEY = "AIzaSyCFo7709M-ddaTvahV_wG1Buh4lPjRFhvQ" 

def is_national_route(name):
    # Match phrases like "National Route 5" or "Route 5" (Kokudō 5)
    return bool(re.search(r"\b(National\s)?Route\s*\d+\b", name, re.IGNORECASE)) \
        or "国道" in name


def snap_to_road(lat, lng):
    url = f"https://roads.googleapis.com/v1/snapToRoads?path={lat},{lng}&key={API_KEY}"
    res = requests.get(url)
    res.raise_for_status()
    data = res.json()
    if "snappedPoints" in data:
        return data["snappedPoints"][0]["location"]
    return {"latitude": lat, "longitude": lng}

def get_named_road(lat, lng):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={API_KEY}"
    res = requests.get(url)
    res.raise_for_status()
    results = res.json().get("results", [])

    candidates = []
    for result in results:
        for comp in result.get("address_components", []):
            if "route" in comp.get("types", []):
                name = comp.get("long_name", "")
                candidates.append(name)

    # 1. First, return a national route if available
    for name in candidates:
        if is_national_route(name):
            return name

    # 2. Otherwise return nothing or a placeholder
    return "Not a national route"


def main():
    # 👉 Paste your polyline string here
    poly = "ghkwEqyfvY{@?y@HmARgABaIOw_@k@aFIaAIsGkAqBa@}@QC`@GjAGr@QlASz@m@dBSf@u@nAmB~Cu@fBUz@[nB[bDUxBYlBa@~B_@fBeAhEOf@m@jAW\\iBnB_CdCsChCsDtDy@|@qBzB}AtBYb@Ud@GXIf@Aj@Bd@R`BDRg@BsA@yBLoANiDp@qFlAoB`@}Cf@yKdB}HjAeBTmAV}IrAsFv@wD^kAL}E\\uANcARs@Vs@\\g@Zo@h@eAxAiEbIkEhI}BdEg@v@iAtAgDdDsHhH_D`DoEfE_@XmBnBkGbGc@n@iAnAW^Of@CTBb@N`@XPTBVAVKf@[NEpA{AtA{Ar@g@PKFOHOXc@b@y@Jc@BU@a@Gg@Oa@]k@{C{DWY?OIKiHqIwIcKqI{JiFmGaBsByDgFaB_CgDeF{DqGcCiEkC{EsEgIy@wA{BqD{BkDiBkCyFsH}AmBoDaEsB{BaH_HoGuFeNoLuQqO{QwOur@}l@mDyCqGoFkCqB{ByA}A}@aCoAeCgA}B}@mEuAuEeAwB_@qDc@_BOuBMmEKyC?oDJ_BJ_F^yIv@}]|CgMhAaBNoDZWRiBZcBVyBPUBQLe@Nm@LWDML_@@[?sB@aCFaCNsCVmEb@{ADqBCy@C}AO{@KyA[gBg@oAi@w@c@i@_@e@c@_AaAiCuC}CeDeIoIyA{AaA}@GGVE`@Qr@Y"

    coords = polyline.decode(poly)
    print(f"Decoded {len(coords)} points")

    step = 3  # Check every 3rd point to reduce API usage
    for i, (lat, lng) in enumerate(coords[::step]):
        snapped = snap_to_road(lat, lng)
        name = get_named_road(snapped["latitude"], snapped["longitude"])
        print(f"{snapped['latitude']:.6f}, {snapped['longitude']:.6f} → {name}")

if __name__ == "__main__":
    main()
