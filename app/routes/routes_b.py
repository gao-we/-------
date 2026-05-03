from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.domain import POI, Food
from app.core.algorithms.sort_search import get_top_k, fuzzy_search_filter
from app.core.algorithms.trie_kmp import Trie
from app.data.map_builder import campus_graph

router = APIRouter()

# 字典树，用于前缀提示
search_trie = Trie()

SCHOOL_KEYWORDS = ("大学", "学院", "校园", "学校")
SCENIC_KEYWORDS = ("景", "公园", "博物馆", "古镇", "山", "湖", "乐园", "广场")
SERVICE_CATEGORIES = ("商店", "饭店", "洗手间", "食堂", "超市", "咖啡馆", "急救点", "饮水机", "ATM", "停车场", "休息长椅")

def _destination_type(name: str, category: str) -> str:
    text = f"{name}{category}"
    if any(k in text for k in SCHOOL_KEYWORDS):
        return "school"
    if any(k in text for k in SCENIC_KEYWORDS):
        return "scenic"
    return "mixed"

def _is_destination_candidate(poi: POI) -> bool:
    if not poi.image_url:
        return False
    return _destination_type(poi.name or "", poi.category or "") in ("school", "scenic")

def init_search_trie(db: Session):
    """
    在启动时或者第一次被调用时初始化的 Trie 树，
    用于地点、美食前缀提示。
    """
    if len(search_trie.root.children) == 0:
        pois = db.query(POI).all()
        for p in pois:
            search_trie.insert(p.name, f"poi_{p.id}")
        foods = db.query(Food).all()
        for f in foods:
            search_trie.insert(f.name, f"food_{f.id}")

@router.get("/autocomplete")
def search_autocomplete(prefix: str, db: Session = Depends(get_db)):
    """
    搜索补全功能：基于 Trie 树。
    """
    init_search_trie(db)
    ids = search_trie.search_prefix(prefix)
    return {
        "prefix": prefix,
        "matches_count": len(ids),
        # 实际开发中应该到数据库中取回具体的记录展示，这里做ID简化返回
        "matched_ids": list(ids)[:10] 
    }

@router.get("/suggest/destinations")
def recommend_destinations(
    limit: int = 12,
    sort_by: str = Query("heat", description="排序依据: heat 或 score"),
    destination_type: str = Query("all", description="可选: all, scenic, school"),
    db: Session = Depends(get_db)
):
    """
    首页目的地推荐：先推荐多个景区/学校供用户选择，再进入目的地详情页。
    """
    items = db.query(POI).filter(POI.image_url != None).all()
    destination_items = [p for p in items if _is_destination_candidate(p)]
    if not destination_items:
        destination_items = items

    if destination_type in ("scenic", "school"):
        destination_items = [
            p for p in destination_items
            if _destination_type(p.name or "", p.category or "") == destination_type
        ]

    def score_func(item):
        if sort_by == "score":
            return (item.id * 31) % 50 / 10.0
        return 200 - item.id if item.id <= 20 else (item.id * 13) % 100

    top_items = get_top_k(destination_items, k=limit, key_func=score_func)
    return {
        "status": "success",
        "strategy": sort_by,
        "destination_type": destination_type,
        "recommendations": [
            {
                "id": i.id,
                "name": i.name,
                "category": i.category,
                "image_url": i.image_url,
                "score": score_func(i),
                "type": _destination_type(i.name or "", i.category or ""),
            }
            for i in top_items
        ],
    }

@router.get("/destination/{poi_id}/recommendations")
def destination_recommendations(
    poi_id: int,
    max_distance: float = 1500.0,
    limit_places: int = 12,
    limit_foods: int = 8,
    db: Session = Depends(get_db)
):
    """
    目的地场所推荐：进入景区/学校后，推荐其周边服务场所和美食。
    """
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise fastapi.HTTPException(status_code=404, detail="查找不到该地点")

    def collect_places(distance_limit: float):
        merged = {}
        for cat in SERVICE_CATEGORIES:
            facilities = campus_graph.find_nearby_facilities(str(poi.id), cat, distance_limit)
            for f in facilities[:3]:
                node_id = str(f.get("id"))
                distance = float(f.get("distance", 0))
                prev = merged.get(node_id)
                if prev is None or distance < prev["distance"]:
                    merged[node_id] = {
                        "id": node_id,
                        "name": f.get("name"),
                        "category": f.get("category"),
                        "distance": round(distance, 2),
                    }
        return merged

    merged = collect_places(max_distance)
    if not merged:
        merged = collect_places(max_distance * 20)

    nearby_places = sorted(merged.values(), key=lambda x: x["distance"])[:limit_places]

    foods = db.query(Food).filter(Food.location_id == poi.location_id).all()
    def food_score(item):
        direct_bonus = 1.0 if item.poi_id == poi.id else 0.0
        return float(item.rating) + direct_bonus

    top_foods = get_top_k(foods, k=limit_foods, key_func=food_score)
    return {
        "status": "success",
        "destination": {
            "id": poi.id,
            "name": poi.name,
            "category": poi.category,
            "image_url": poi.image_url,
            "type": _destination_type(poi.name or "", poi.category or ""),
        },
        "route_start_id": str(poi.id),
        "nearby_places": nearby_places,
        "food_recommendations": [
            {
                "id": i.id,
                "name": i.name,
                "rating": float(i.rating) if i.rating is not None else 0.0,
                "price_range": i.price_range,
                "related_to_destination": i.poi_id == poi.id,
            }
            for i in top_foods
        ],
    }

@router.get("/suggest/attractions")
def recommend_attractions(
    limit: int = 10,
    sort_by: str = Query("score", description="排序依据: score (此处为随机模拟评分), heat (按ID大小模拟热度)"),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    旅游游览前推荐列表。满足大作业要求：使用 Top-K 保证不完全排序。
    """
    query = db.query(POI).filter(POI.image_url != None)
    if category:
        query = query.filter(POI.category == category)
    items = query.all()
        
    # 定义排序权重计算函数。这里的 score 我们用 POI 的 id 做一些简单混淆计算模拟
    def score_func(item):
        if sort_by == "heat":
            # 假装有些 id 的地点极其热门
            return 200 - item.id if item.id <= 20 else (item.id * 13) % 100
        else:
            return (item.id * 31) % 50 / 10.0
            
    # 调用自行手写的基于最小堆的 Top-K 算法
    top_items = get_top_k(items, k=limit, key_func=score_func)
    
    return {
        "status": "success",
        "strategy": sort_by,
        "recommendations": [{"id": i.id, "name": i.name, "category": i.category, "image_url": getattr(i, "image_url", None), "score": score_func(i)} for i in top_items]
    }

@router.get("/suggest/foods")
def recommend_foods(
    limit: int = 10,
    sort_by: str = Query("score", description="排序依据: score, heat"),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    destination_poi_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    美食推荐及查找功能。具备分类过滤以及名称/类别的模糊查找功能。
    使用编辑距离和 Top-K 优先级队列排序。
    """
    items = db.query(Food).all()
    
    # 1. 类别过滤 (Food 我们当时没有设 category，这里为了兼容参数做 price_range 的判断)
    if category:
        items = [i for i in items if i.price_range == category]
        
    # 2. 模糊查找 (如果提供了名称关键字)，使用 编辑距离 算法过滤并获得部分匹配集
    if keyword:
        # text_selector 指定提取 item 中的哪些文本做匹配
        matched = fuzzy_search_filter(items, keyword, text_selector=lambda x: str(x.name), threshold=3)
        # 提取其中匹配结果的真实对象
        items = [m[1] for m in matched]

    if destination_poi_id is not None:
        items = [i for i in items if i.poi_id == destination_poi_id or i.poi_id is None]
        
    def score_func(item):
        if sort_by == "heat":
            return (item.id * 17) % 200
        else:
            return float(item.rating)
            
    top_items = get_top_k(items, k=limit, key_func=score_func)
    
    return {
        "status": "success",
        "strategy": sort_by,
        "keyword": keyword,
        "recommendations": [{"id": i.id, "name": i.name, "rating": i.rating, "price_range": i.price_range} for i in top_items]
    }


import fastapi
from app.models.domain import Location

@router.get("/suggest/attractions/{poi_id}")
def get_attraction_detail(poi_id: int, db: Session = Depends(get_db)):
    """
    获取单个景点的详细信息（包含描述）
    """
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        raise fastapi.HTTPException(status_code=404, detail="查找不到该地点")
        
    # 查询关联的实际 Location 获取详情描述信息
    location = db.query(Location).filter(Location.id == poi.location_id).first()
    
    return {
        "status": "success",
        "data": {
            "id": poi.id,
            "name": poi.name,
            "category": poi.category,
            "latitude": float(poi.latitude) if poi.latitude else None,
            "longitude": float(poi.longitude) if poi.longitude else None,
            "city": location.city if location else "未知",
            # 如果没有专门设置过描述（因为是随机种子数据），我们给它加上一段通用演示文案
            "description": location.description if location and location.description else f"{poi.name}是本地一个人气极高的{poi.category}景点。您可以在这里感受到独特的风景与良好的服务！",
        }
    }
