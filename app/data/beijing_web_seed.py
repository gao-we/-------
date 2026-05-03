import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.error import HTTPError, URLError


OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


@dataclass
class WebPlace:
    name: str
    category: str
    latitude: float
    longitude: float
    image_url: str = ""


def _run_overpass(query: str) -> Dict:
    headers = {
        "User-Agent": "data-structure-hw-seeder/1.0 (+https://example.local)",
        "Accept": "application/json",
    }
    for url in OVERPASS_URLS:
        data = urllib.parse.urlencode({"data": query}).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST", headers=headers)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            if e.code not in (406, 429, 500, 502, 503, 504):
                raise
        except URLError:
            continue

    raise RuntimeError("Overpass API 不可用，无法在线抓取北京数据。")


def _extract_center(element: Dict) -> Tuple[float, float]:
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center")
    if center and "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    raise ValueError("Element has no coordinates")


def _clean_name(name: str) -> str:
    return " ".join(name.split()).strip()


def fetch_beijing_destinations(limit: int = 260) -> List[WebPlace]:
    """
    从 OpenStreetMap(Overpass) 拉取北京景区/学校数据。
    """
    query = """
    [out:json][timeout:90];
    area["name"="北京市"]["boundary"="administrative"]->.bj;
    (
      node["tourism"~"attraction|museum|theme_park|zoo|viewpoint"](area.bj);
      way["tourism"~"attraction|museum|theme_park|zoo|viewpoint"](area.bj);
      relation["tourism"~"attraction|museum|theme_park|zoo|viewpoint"](area.bj);
      node["amenity"~"university|college|school"](area.bj);
      way["amenity"~"university|college|school"](area.bj);
      relation["amenity"~"university|college|school"](area.bj);
    );
    out center tags;
    """
    payload = _run_overpass(query)
    elements = payload.get("elements", [])

    scenic_image = "https://images.unsplash.com/photo-1472396961693-142e6e269027?auto=format&fit=crop&w=900&q=60"
    school_image = "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=900&q=60"

    places: List[WebPlace] = []
    seen = set()
    for el in elements:
        tags = el.get("tags", {})
        raw_name = tags.get("name")
        if not raw_name:
            continue
        name = _clean_name(raw_name)
        if len(name) < 2 or len(name) > 80:
            continue

        amenity = tags.get("amenity", "")
        tourism = tags.get("tourism", "")
        if amenity in ("university", "college", "school"):
            category = "学校"
            image = school_image
        elif tourism == "museum":
            category = "博物馆"
            image = scenic_image
        elif tourism:
            category = "景区"
            image = scenic_image
        else:
            continue

        try:
            lat, lon = _extract_center(el)
        except ValueError:
            continue

        key = (name, category)
        if key in seen:
            continue
        seen.add(key)
        places.append(WebPlace(name=name, category=category, latitude=lat, longitude=lon, image_url=image))

    places.sort(key=lambda x: (x.category, x.name))
    return places[:limit]


def fetch_beijing_services(limit: int = 160) -> List[WebPlace]:
    """
    从 OSM 拉取北京服务设施点（供场所推荐使用）。
    """
    query = """
    [out:json][timeout:90];
    area["name"="北京市"]["boundary"="administrative"]->.bj;
    (
      node["amenity"~"restaurant|fast_food|food_court|cafe|toilets|library|parking|hospital|clinic|atm|drinking_water"](area.bj);
      way["amenity"~"restaurant|fast_food|food_court|cafe|toilets|library|parking|hospital|clinic|atm|drinking_water"](area.bj);
      relation["amenity"~"restaurant|fast_food|food_court|cafe|toilets|library|parking|hospital|clinic|atm|drinking_water"](area.bj);
      node["shop"~"supermarket|convenience|mall"](area.bj);
      way["shop"~"supermarket|convenience|mall"](area.bj);
      relation["shop"~"supermarket|convenience|mall"](area.bj);
    );
    out center tags;
    """
    payload = _run_overpass(query)
    elements = payload.get("elements", [])

    def map_category(tags: Dict) -> str:
        amenity = tags.get("amenity", "")
        shop = tags.get("shop", "")
        if amenity in ("restaurant", "food_court", "fast_food"):
            return "饭店"
        if amenity == "cafe":
            return "咖啡馆"
        if amenity == "toilets":
            return "洗手间"
        if amenity == "library":
            return "图书馆"
        if amenity == "parking":
            return "停车场"
        if amenity in ("hospital", "clinic"):
            return "急救点"
        if amenity == "atm":
            return "ATM"
        if amenity == "drinking_water":
            return "饮水机"
        if shop in ("supermarket", "convenience", "mall"):
            return "超市"
        return "商店"

    places: List[WebPlace] = []
    seen = set()
    for el in elements:
        tags = el.get("tags", {})
        raw_name = tags.get("name")
        if not raw_name:
            continue
        name = _clean_name(raw_name)
        if len(name) < 2 or len(name) > 80:
            continue
        category = map_category(tags)
        try:
            lat, lon = _extract_center(el)
        except ValueError:
            continue

        key = (name, category)
        if key in seen:
            continue
        seen.add(key)
        places.append(WebPlace(name=name, category=category, latitude=lat, longitude=lon))

    places.sort(key=lambda x: (x.category, x.name))
    return places[:limit]


def fetch_beijing_foods(limit: int = 120) -> List[WebPlace]:
    """
    从 OSM 拉取北京餐饮点（用于美食推荐库）。
    """
    query = """
    [out:json][timeout:90];
    area["name"="北京市"]["boundary"="administrative"]->.bj;
    (
      node["amenity"~"restaurant|fast_food|food_court|cafe"](area.bj);
      way["amenity"~"restaurant|fast_food|food_court|cafe"](area.bj);
      relation["amenity"~"restaurant|fast_food|food_court|cafe"](area.bj);
    );
    out center tags;
    """
    payload = _run_overpass(query)
    elements = payload.get("elements", [])

    places: List[WebPlace] = []
    seen = set()
    for el in elements:
        tags = el.get("tags", {})
        raw_name = tags.get("name")
        if not raw_name:
            continue
        name = _clean_name(raw_name)
        if len(name) < 2 or len(name) > 80:
            continue
        amenity = tags.get("amenity", "")
        category = "咖啡馆" if amenity == "cafe" else "饭店"
        try:
            lat, lon = _extract_center(el)
        except ValueError:
            continue
        key = (name, category)
        if key in seen:
            continue
        seen.add(key)
        places.append(WebPlace(name=name, category=category, latitude=lat, longitude=lon))

    places.sort(key=lambda x: (x.category, x.name))
    return places[:limit]
