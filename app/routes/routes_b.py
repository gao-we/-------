from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.domain import POI, Food
from app.core.algorithms.sort_search import get_top_k, fuzzy_search_filter
from app.core.algorithms.trie_kmp import Trie

router = APIRouter()

# 字典树，用于前缀提示
search_trie = Trie()

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
    query = db.query(POI)
    if category:
        query = query.filter(POI.category == category)
    items = query.all()
        
    # 定义排序权重计算函数。这里的 score 我们用 POI 的 id 做一些简单混淆计算模拟
    def score_func(item):
        if sort_by == "heat":
            # 假装有些 id 的地点极其热门
            return (item.id * 13) % 100
        else:
            return (item.id * 31) % 50 / 10.0
            
    # 调用自行手写的基于最小堆的 Top-K 算法
    top_items = get_top_k(items, k=limit, key_func=score_func)
    
    return {
        "status": "success",
        "strategy": sort_by,
        "recommendations": [{"id": i.id, "name": i.name, "category": i.category} for i in top_items]
    }

@router.get("/suggest/foods")
def recommend_foods(
    limit: int = 10,
    sort_by: str = Query("score", description="排序依据: score, heat"),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
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

