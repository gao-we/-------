from fastapi import APIRouter, Query
from typing import List, Optional
from app.models.schemas import RecommendationRequest
from app.data.recommendation_data import global_recommendation_db
from app.core.algorithms.sort_search import get_top_k, fuzzy_search_filter

router = APIRouter()

@router.get("/suggest/attractions")
def recommend_attractions(
    limit: int = 10,
    sort_by: str = Query("score", description="排序依据: score, heat"),
    category: Optional[str] = None
):
    """
    旅游游览前推荐列表。满足大作业要求：使用 Top-K 保证不完全排序。
    """
    items = global_recommendation_db["attraction"]
    
    if category:
        items = [i for i in items if i.category == category]
        
    # 定义排序权重计算函数
    def score_func(item):
        if sort_by == "heat":
            return item.heat
        else:
            return item.evaluate_score
            
    # 调用自行手写的基于最小堆的 Top-K 算法
    top_items = get_top_k(items, k=limit, key_func=score_func)
    
    return {
        "status": "success",
        "strategy": sort_by,
        "recommendations": [i.to_dict() for i in top_items]
    }

@router.get("/suggest/foods")
def recommend_foods(
    limit: int = 10,
    sort_by: str = Query("distance", description="排序依据: score, heat, distance"),
    category: Optional[str] = None,
    keyword: Optional[str] = None
):
    """
    美食推荐及查找功能。具备分类过滤以及名称/类别的模糊查找功能。
    使用编辑距离和 Top-K 优先级队列排序。
    """
    items = global_recommendation_db["food"]
    
    # 1. 类别过滤
    if category:
        items = [i for i in items if i.category == category]
        
    # 2. 模糊查找 (如果提供了名称关键字)，使用 编辑距离 算法过滤并获得部分匹配集
    if keyword:
        # text_selector 指定提取 item 中的哪些文本做匹配
        matched = fuzzy_search_filter(items, keyword, text_selector=lambda x: f"{x.name}_{x.category}", threshold=3)
        # 提取其中匹配结果的真实对象
        items = [m[1] for m in matched]
        
    # 3. 配置 Top-K 权重，如果要求距离排序，距离越短越好，由于 get_top_k 默认取最大值
    # 因此如果是按距离排序，我们需要将距离取负或者倒数来转换逻辑
    def score_func(item):
        if sort_by == "heat":
            return item.heat
        elif sort_by == "score":
            return item.evaluate_score
        else:
            # 距离越小分越高
            return 100000.0 / (item.distance + 1.0)
            
    top_items = get_top_k(items, k=limit, key_func=score_func)
    
    return {
        "status": "success",
        "strategy": sort_by,
        "keyword": keyword,
        "recommendations": [i.to_dict() for i in top_items]
    }

