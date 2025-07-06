from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from urllib.parse import urlparse, unquote
import re
from datetime import datetime
import requests
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import databases
import sqlalchemy
import os
from contextlib import asynccontextmanager

DATABASE_URL = os.getenv("DATABASE_URL")
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

routes = sqlalchemy.Table(
    "routes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.String),
    sqlalchemy.Column("polyline", sqlalchemy.Text),
    sqlalchemy.Column("timestamp", sqlalchemy.DateTime),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

GOOGLE_API_KEY = "AIzaSyCFo7709M-ddaTvahV_wG1Buh4lPjRFhvQ" 

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

class ShortURLRequest(BaseModel):
    short_url: str

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})

@app.post("/save-route")
async def save_route(data: dict = Body(...)):
    user_id = data.get("user_id")
    polyline = data.get("polyline")

    if not user_id or not polyline:
        raise HTTPException(status_code=400, detail="Missing user_id or polyline")

    query = routes.insert().values(
        user_id=user_id,
        polyline=polyline,
        timestamp=datetime.utcnow()
    )
    await database.execute(query)
    return {"message": "Route saved successfully"}

@app.get("/user-paths")
async def get_user_paths(user_id: str):
    query = routes.select().where(routes.c.user_id == user_id)
    results = await database.fetch_all(query)
    return {
        "paths": [
            {"polyline": r["polyline"], "timestamp": str(r["timestamp"])}
            for r in results
        ]
    }

def expand_url_with_selenium(url: str) -> str:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    final_url = driver.current_url
    driver.quit()
    return final_url

@app.post("/expand-and-parse")
def expand_and_parse(req: ShortURLRequest):
    try:
        # Try to expand with requests
        try:
            expanded_response = requests.get(req.short_url, allow_redirects=True, timeout=5)
            final_url = expanded_response.url
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to expand the short URL")

        parsed_url = urlparse(final_url)
        path_parts = parsed_url.path.split('/')

        if "dir" not in path_parts:
            raise HTTPException(status_code=400, detail="Not a directions URL")

        dir_index = path_parts.index("dir")
        locations = path_parts[dir_index + 1:]

        cleaned = [
            unquote(loc.replace('+', ' '))
            for loc in locations
            if loc and not loc.startswith('@') and not loc.startswith('data') and not loc.startswith('3e')
        ]

        if len(cleaned) < 2:
            raise HTTPException(status_code=400, detail="Could not extract both origin and destination")

        origin = cleaned[0]
        destination = cleaned[-1]
        waypoints = cleaned[1:-1] if len(cleaned) > 2 else []

        mode = "driving"
        match = re.search(r"/3e(\d)", final_url)
        if match:
            mode_map = {
                "0": "driving",
                "1": "walking",
                "2": "bicycling",
                "3": "transit"
            }
            mode = mode_map.get(match.group(1), "driving")

        return {
            "short_url": req.short_url,
            "expanded_url": final_url,
            "origin": origin,
            "destination": destination,
            "waypoints": waypoints,
            "mode": mode
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.post("/google-directions")
def get_google_directions(data: dict = Body(...)):
    origin = data.get("origin")
    destination = data.get("destination")
    mode = data.get("mode", "driving")

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "alternatives": "true",
        "key": GOOGLE_API_KEY
    }

    response = requests.get(url, params=params)
    result = response.json()

    if result["status"] != "OK":
        return {"error": result.get("error_message", "Failed to get route")}

    routes_list = []
    for idx, route in enumerate(result["routes"]):
        routes_list.append({
            "route_index": idx,
            "summary": route.get("summary"),
            "distance": route["legs"][0]["distance"]["text"],
            "duration": route["legs"][0]["duration"]["text"],
            "polyline": route["overview_polyline"]["points"]
        })

    return {"routes": routes_list}
