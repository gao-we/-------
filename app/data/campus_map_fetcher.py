import json
import math
import os
import urllib.parse
import urllib.request
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError


AMAP_PLACE_AROUND_URL = "https://restapi.amap.com/v3/place/around"
AMAP_WALKING_ROUTE_URL = "https://restapi.amap.com/v3/direction/walking"
BAIDU_PLACE_SEARCH_URL = "https://api.map.baidu.com/place/v2/search"
BAIDU_WALKING_ROUTE_URL = "https://api.map.baidu.com/directionlite/v1/walking"

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def _run_overpass(query: str) -> Dict:
    headers = {
        "User-Agent": "data-structure-campus-map/1.0",
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
    raise RuntimeError("校园地图在线抓取失败（Overpass 不可用）")


def _http_get_json(url: str, params: Dict[str, str], timeout: int = 45) -> Dict:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{url}?{query}",
        method="GET",
        headers={"User-Agent": "data-structure-campus-map/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _parse_lnglat_polyline(polyline: str) -> List[Dict[str, float]]:
    points: List[Dict[str, float]] = []
    for pair in (polyline or "").split(";"):
        if "," not in pair:
            continue
        lon_s, lat_s = pair.split(",", 1)
        try:
            lon = float(lon_s)
            lat = float(lat_s)
        except ValueError:
            continue
        points.append({"lat": lat, "lon": lon})
    return points


def _spot_category(name: str, poi_type: str, keyword: str) -> str:
    text = f"{name}{poi_type}{keyword}"
    if "图书馆" in text:
        return "图书馆"
    if "花园" in text or "公园" in text:
        return "花园"
    if "教学楼" in text or "学院" in text or "大学" in text:
        return "教学楼/校区设施"
    if "博物馆" in text or "景" in text:
        return "景点"
    return "服务设施"


def _dedupe_roads(roads: List[List[Dict[str, float]]]) -> List[List[Dict[str, float]]]:
    deduped: List[List[Dict[str, float]]] = []
    seen = set()
    for seg in roads:
        if len(seg) < 2:
            continue
        norm = tuple((round(p["lat"], 6), round(p["lon"], 6)) for p in seg)
        if norm in seen:
            continue
        seen.add(norm)
        deduped.append(seg)
    return deduped


def _spot_distance(center_lat: float, center_lon: float, spot: Dict) -> float:
    return _distance_m(center_lat, center_lon, float(spot["latitude"]), float(spot["longitude"]))


def _fetch_amap_map(destination_name: str, center_lat: float, center_lon: float, radius_m: int, api_key: str) -> Optional[Dict]:
    keywords = [
        "图书馆", "教学楼", "实验楼", "花园", "博物馆", "景点",
        "食堂", "咖啡馆", "体育馆", "停车场", "卫生间", "游客中心",
        "地铁站", "公交站", "校门"
    ]
    spots = []
    seen_spot = set()
    pages_fetched = 0

    for keyword in keywords:
        for page in range(1, 4):
            data = _http_get_json(
                AMAP_PLACE_AROUND_URL,
                {
                    "key": api_key,
                    "location": f"{center_lon},{center_lat}",
                    "radius": str(radius_m),
                    "keywords": keyword,
                    "offset": "25",
                    "page": str(page),
                    "extensions": "all",
                    "sortrule": "distance",
                },
            )
            if str(data.get("status")) != "1":
                continue
            pages_fetched += 1
            pois = data.get("pois", []) or []
            if not pois:
                continue
            for poi in pois:
                loc = poi.get("location", "")
                if "," not in loc:
                    continue
                lon_s, lat_s = loc.split(",", 1)
                try:
                    lat = float(lat_s)
                    lon = float(lon_s)
                except ValueError:
                    continue
                name = (poi.get("name") or "").strip()
                if not name:
                    continue
                category = _spot_category(name, str(poi.get("type", "")), keyword)
                key = (name, round(lat, 6), round(lon, 6), category)
                if key in seen_spot:
                    continue
                seen_spot.add(key)
                spots.append(
                    {
                        "name": name,
                        "category": category,
                        "latitude": round(lat, 7),
                        "longitude": round(lon, 7),
                    }
                )
            if len(pois) < 25:
                break

    if not spots:
        return None

    spots.sort(key=lambda x: _spot_distance(center_lat, center_lon, x))
    roads = []
    route_queries = 0
    for spot in spots[:24]:
        route_data = _http_get_json(
            AMAP_WALKING_ROUTE_URL,
            {
                "key": api_key,
                "origin": f"{center_lon},{center_lat}",
                "destination": f"{spot['longitude']},{spot['latitude']}",
            },
        )
        route_queries += 1
        if str(route_data.get("status")) != "1":
            continue
        paths = route_data.get("route", {}).get("paths", [])
        if not paths:
            continue
        for step in paths[0].get("steps", []):
            seg = _parse_lnglat_polyline(step.get("polyline", ""))
            if len(seg) >= 2:
                roads.append(seg)

    for idx in range(0, min(18, len(spots) - 1), 2):
        a = spots[idx]
        b = spots[idx + 1]
        route_data = _http_get_json(
            AMAP_WALKING_ROUTE_URL,
            {
                "key": api_key,
                "origin": f"{a['longitude']},{a['latitude']}",
                "destination": f"{b['longitude']},{b['latitude']}",
            },
        )
        route_queries += 1
        if str(route_data.get("status")) != "1":
            continue
        paths = route_data.get("route", {}).get("paths", [])
        if not paths:
            continue
        for step in paths[0].get("steps", []):
            seg = _parse_lnglat_polyline(step.get("polyline", ""))
            if len(seg) >= 2:
                roads.append(seg)

    roads = _dedupe_roads(roads)

    return {
        "scope": "internal",
        "target_name": destination_name,
        "provider": "amap-mcp-compatible",
        "roads": roads[:620],
        "buildings": [],
        "spots": spots[:320],
        "meta": {
            "detail_level": "high",
            "spots_count": len(spots),
            "roads_count": len(roads),
            "keywords_used": len(keywords),
            "pages_fetched": pages_fetched,
            "route_queries": route_queries,
        },
    }


def _fetch_baidu_map(destination_name: str, center_lat: float, center_lon: float, radius_m: int, api_key: str) -> Optional[Dict]:
    keywords = ["图书馆", "教学楼", "花园", "博物馆", "景点", "食堂", "咖啡馆", "体育馆"]
    spots = []
    seen_spot = set()
    pages_fetched = 0

    for keyword in keywords:
        for page_num in range(0, 3):
            data = _http_get_json(
                BAIDU_PLACE_SEARCH_URL,
                {
                    "ak": api_key,
                    "output": "json",
                    "query": keyword,
                    "location": f"{center_lat},{center_lon}",
                    "radius": str(radius_m),
                    "scope": "2",
                    "page_size": "20",
                    "page_num": str(page_num),
                },
            )
            if int(data.get("status", -1)) != 0:
                continue
            pages_fetched += 1
            results = data.get("results", []) or []
            if not results:
                continue
            for item in results:
                loc = item.get("location", {})
                try:
                    lat = float(loc.get("lat"))
                    lon = float(loc.get("lng"))
                except (TypeError, ValueError):
                    continue
                name = (item.get("name") or "").strip()
                if not name:
                    continue
                detail_info = item.get("detail_info", {}) or {}
                category = _spot_category(name, str(detail_info.get("tag", "")), keyword)
                key = (name, round(lat, 6), round(lon, 6), category)
                if key in seen_spot:
                    continue
                seen_spot.add(key)
                spots.append(
                    {
                        "name": name,
                        "category": category,
                        "latitude": round(lat, 7),
                        "longitude": round(lon, 7),
                    }
                )
            if len(results) < 20:
                break

    if not spots:
        return None

    spots.sort(key=lambda x: _spot_distance(center_lat, center_lon, x))
    roads = []
    route_queries = 0
    for spot in spots[:24]:
        route_data = _http_get_json(
            BAIDU_WALKING_ROUTE_URL,
            {
                "ak": api_key,
                "output": "json",
                "origin": f"{center_lat},{center_lon}",
                "destination": f"{spot['latitude']},{spot['longitude']}",
            },
        )
        route_queries += 1
        if int(route_data.get("status", -1)) != 0:
            continue
        routes = route_data.get("result", {}).get("routes", [])
        if not routes:
            continue
        for step in routes[0].get("steps", []):
            seg = _parse_lnglat_polyline(step.get("path", ""))
            if len(seg) >= 2:
                roads.append(seg)

    roads = _dedupe_roads(roads)

    return {
        "scope": "internal",
        "target_name": destination_name,
        "provider": "baidu-mcp-compatible",
        "roads": roads[:620],
        "buildings": [],
        "spots": spots[:320],
        "meta": {
            "detail_level": "high",
            "spots_count": len(spots),
            "roads_count": len(roads),
            "keywords_used": len(keywords),
            "pages_fetched": pages_fetched,
            "route_queries": route_queries,
        },
    }


def _center_of_element(el: Dict):
    if "lat" in el and "lon" in el:
        return float(el["lat"]), float(el["lon"])
    center = el.get("center")
    if center and "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    geom = el.get("geometry")
    if geom and len(geom) > 0:
        lat = sum(float(x["lat"]) for x in geom) / len(geom)
        lon = sum(float(x["lon"]) for x in geom) / len(geom)
        return lat, lon
    return None, None


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * (math.sin(dl / 2) ** 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _escape_overpass_text(name: str) -> str:
    return name.replace("\\", "\\\\").replace('"', '\\"')


def _expand_destination_names(name: str) -> List[str]:
    cands = [name.strip()]
    for token in ("大学", "学院", "学校"):
        idx = name.find(token)
        if idx != -1:
            base = name[: idx + len(token)].strip()
            if len(base) >= 2:
                cands.append(base)
    # 去重保序
    uniq = []
    seen = set()
    for n in cands:
        if n and n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq


def _extract_layers(elements: List[Dict]) -> Dict:
    roads: List[List[Dict[str, float]]] = []
    buildings: List[List[Dict[str, float]]] = []
    spots = []
    seen_spot = set()

    for el in elements:
        tags = el.get("tags", {})
        geom = el.get("geometry")
        if geom and len(geom) >= 2:
            coords = [{"lat": float(p["lat"]), "lon": float(p["lon"])} for p in geom if "lat" in p and "lon" in p]
            if len(coords) >= 2:
                if "highway" in tags:
                    roads.append(coords)
                elif "building" in tags or tags.get("leisure") in ("park", "garden", "pitch"):
                    buildings.append(coords)

        lat, lon = _center_of_element(el)
        if lat is None or lon is None:
            continue
        amenity = tags.get("amenity", "")
        tourism = tags.get("tourism", "")
        leisure = tags.get("leisure", "")
        building = tags.get("building", "")
        name = tags.get("name", "").strip()
        if not name:
            continue

        category = None
        if amenity == "library":
            category = "图书馆"
        elif leisure in ("park", "garden"):
            category = "花园"
        elif amenity in ("university", "school", "college"):
            category = "教学楼/校区设施"
        elif tourism in ("attraction", "museum", "artwork", "viewpoint"):
            category = "景点"
        elif building in ("university", "school", "college", "yes"):
            category = "教学楼/建筑"
        if not category:
            continue

        key = (name, round(lat, 6), round(lon, 6), category)
        if key in seen_spot:
            continue
        seen_spot.add(key)
        spots.append({
            "name": name,
            "category": category,
            "latitude": round(lat, 7),
            "longitude": round(lon, 7),
        })

    return {
        "roads": roads[:320],
        "buildings": buildings[:220],
        "spots": spots[:160],
    }


def _fetch_internal_by_area(destination_name: str, center_lat: float, center_lon: float, radius_m: int) -> Optional[Dict]:
    names = _expand_destination_names(destination_name)
    name_blocks = []
    for nm in names:
        escaped_name = _escape_overpass_text(nm)
        # exact + prefix regex 两种方式，提高命中“XX大学博物馆 -> XX大学”这类场景
        name_blocks.append(f'way(around:{radius_m},{center_lat},{center_lon})["name"="{escaped_name}"]["amenity"~"university|school|college"];')
        name_blocks.append(f'relation(around:{radius_m},{center_lat},{center_lon})["name"="{escaped_name}"]["amenity"~"university|school|college"];')
        name_blocks.append(f'way(around:{radius_m},{center_lat},{center_lon})["name"="{escaped_name}"]["tourism"~"attraction|museum|theme_park|zoo"];')
        name_blocks.append(f'relation(around:{radius_m},{center_lat},{center_lon})["name"="{escaped_name}"]["tourism"~"attraction|museum|theme_park|zoo"];')
        name_blocks.append(f'way(around:{radius_m},{center_lat},{center_lon})["name"~"^{escaped_name}"]["amenity"~"university|school|college"];')
        name_blocks.append(f'relation(around:{radius_m},{center_lat},{center_lon})["name"~"^{escaped_name}"]["amenity"~"university|school|college"];')

    # 先在附近按名称定位“学校/景区”主体，拿到其 area，再抓取 area 内部要素
    locate_query = f"""
    [out:json][timeout:90];
    (
      {" ".join(name_blocks)}
    );
    out center tags;
    """
    located = _run_overpass(locate_query).get("elements", [])
    if not located:
        return None

    # 选与中心最近的边界对象
    best = None
    best_score = float("inf")
    for el in located:
        lat, lon = _center_of_element(el)
        if lat is None or lon is None:
            continue
        d = _distance_m(center_lat, center_lon, lat, lon)
        tags = el.get("tags", {})
        amenity = tags.get("amenity", "")
        tourism = tags.get("tourism", "")
        name = tags.get("name", "")
        # 优先学校/校区边界，其次景区主体，再次博物馆等点位
        penalty = 0.0
        if amenity in ("university", "college", "school"):
            penalty = 0.0
        elif tourism in ("attraction", "theme_park", "zoo"):
            penalty = 300.0
        elif tourism == "museum":
            penalty = 1200.0
        else:
            penalty = 800.0
        # 命中更完整校园名时给更高优先级
        if any(k in name for k in ("大学", "学院", "学校")):
            penalty -= 120.0
        score = d + penalty
        if score < best_score:
            best_score = score
            best = el
    if not best:
        return None

    target_type = best.get("type")
    target_id = best.get("id")
    if target_type not in ("way", "relation") or target_id is None:
        return None

    if target_type == "way":
        area_define = f"way({target_id});\nmap_to_area->.targetArea;"
    else:
        area_define = f"relation({target_id});\nmap_to_area->.targetArea;"

    internal_query = f"""
    [out:json][timeout:90];
    {area_define}
    (
      way(area.targetArea)["highway"]["highway"!~"motorway|trunk|primary"];
      way(area.targetArea)["building"];
      way(area.targetArea)["leisure"~"park|garden|pitch|playground"];
      node(area.targetArea)["amenity"~"library|school|college|university|cafe|restaurant|toilets"];
      way(area.targetArea)["amenity"~"library|school|college|university|cafe|restaurant|toilets"];
      node(area.targetArea)["tourism"~"attraction|museum|artwork|viewpoint"];
      way(area.targetArea)["tourism"~"attraction|museum|artwork|viewpoint"];
    );
    out center geom tags;
    """
    try:
        internal_elements = _run_overpass(internal_query).get("elements", [])
    except Exception:
        return None
    if not internal_elements:
        return None

    layers = _extract_layers(internal_elements)
    if not layers["roads"] and not layers["buildings"] and not layers["spots"]:
        return None
    return {
        "scope": "internal",
        "target_name": best.get("tags", {}).get("name", destination_name),
        **layers,
    }


def _fetch_fallback_around(center_lat: float, center_lon: float, radius_m: int) -> Dict:
    query = f"""
    [out:json][timeout:90];
    (
      way(around:{radius_m},{center_lat},{center_lon})["highway"];
      way(around:{radius_m},{center_lat},{center_lon})["building"];
      way(around:{radius_m},{center_lat},{center_lon})["leisure"~"park|garden|pitch"];
      node(around:{radius_m},{center_lat},{center_lon})["amenity"~"library|university|school|college"];
      node(around:{radius_m},{center_lat},{center_lon})["tourism"~"attraction|museum|artwork|viewpoint"];
      node(around:{radius_m},{center_lat},{center_lon})["leisure"~"park|garden"];
      way(around:{radius_m},{center_lat},{center_lon})["amenity"~"library|university|school|college"];
      way(around:{radius_m},{center_lat},{center_lon})["tourism"~"attraction|museum"];
    );
    out center geom tags;
    """
    elements = _run_overpass(query).get("elements", [])
    return {
        "scope": "around",
        **_extract_layers(elements),
    }


def fetch_campus_map(destination_name: str, center_lat: float, center_lon: float, radius_m: int = 1200, provider: str = "auto") -> Dict:
    """
    优先抓取“目的地内部”地图要素；如果定位不到内部边界再退化为周边抓取。
    """
    selected_provider = (provider or "auto").strip().lower()
    if selected_provider not in ("auto", "amap", "baidu", "osm"):
        raise ValueError("provider 仅支持 auto/amap/baidu/osm")

    amap_key = os.getenv("AMAP_MAPS_API_KEY") or os.getenv("AMAP_API_KEY")
    baidu_key = os.getenv("BAIDU_MAPS_API_KEY") or os.getenv("BAIDU_MAP_AK") or os.getenv("BAIDU_API_KEY")

    if selected_provider in ("auto", "amap"):
        if selected_provider == "amap" and not amap_key:
            raise RuntimeError("未配置高德地图 Key（AMAP_MAPS_API_KEY 或 AMAP_API_KEY）")
        if amap_key:
            amap_data = _fetch_amap_map(destination_name, center_lat, center_lon, radius_m, amap_key)
            if amap_data:
                return {"center": {"latitude": center_lat, "longitude": center_lon}, "radius_m": radius_m, **amap_data}
            if selected_provider == "amap":
                raise RuntimeError("高德地图抓取失败，请检查目的地名称、Key 权限与配额")

    if selected_provider in ("auto", "baidu"):
        if selected_provider == "baidu" and not baidu_key:
            raise RuntimeError("未配置百度地图 Key（BAIDU_MAPS_API_KEY 或 BAIDU_MAP_AK）")
        if baidu_key:
            baidu_data = _fetch_baidu_map(destination_name, center_lat, center_lon, radius_m, baidu_key)
            if baidu_data:
                return {"center": {"latitude": center_lat, "longitude": center_lon}, "radius_m": radius_m, **baidu_data}
            if selected_provider == "baidu":
                raise RuntimeError("百度地图抓取失败，请检查目的地名称、Key 权限与配额")

    internal = _fetch_internal_by_area(destination_name, center_lat, center_lon, radius_m)
    if internal:
        internal.setdefault(
            "meta",
            {
                "detail_level": "standard",
                "spots_count": len(internal.get("spots", [])),
                "roads_count": len(internal.get("roads", [])),
            },
        )
        return {
            "center": {"latitude": center_lat, "longitude": center_lon},
            "radius_m": radius_m,
            "provider": "osm-overpass",
            **internal,
        }

    fallback = _fetch_fallback_around(center_lat, center_lon, radius_m)
    fallback.setdefault(
        "meta",
        {
            "detail_level": "standard",
            "spots_count": len(fallback.get("spots", [])),
            "roads_count": len(fallback.get("roads", [])),
        },
    )
    return {
        "center": {"latitude": center_lat, "longitude": center_lon},
        "radius_m": radius_m,
        "provider": "osm-overpass",
        **fallback,
    }
