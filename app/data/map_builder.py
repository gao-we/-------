import random
from sqlalchemy.orm import Session
from app.core.algorithms.graph_algo import Graph
from app.database import SessionLocal
from app.models.domain import POI, Road

def load_graph_from_db(g: Graph) -> None:
    """
    从 PostgreSQL 数据库中加载节点和边，构建用于寻路和导览的内存邻接表。
    """
    db: Session = SessionLocal()
    
    try:
        # 清空现有图
        g.adj_list.clear()
        g.node_info.clear()

        # 加载所有 POI 节点作为图的顶点
        pois = db.query(POI).all()
        for p in pois:
            # 兼容之前 Graph 的设计，由于 ID 是 int，我们转为 str
            g.add_node(str(p.id), p.name, p.category)
            
        # 加载所有连通边
        roads = db.query(Road).all()
        for r in roads:
            # 兼容旧设计，如果 transport_modes 是空的，就默认 walk
            t_mode = r.transport_modes[0] if r.transport_modes and len(r.transport_modes) > 0 else "walk"
            # traffic = 10 -> 严重拥堵(慢), 1 -> 畅通(快)
            # 在图算法中我们通过用 crowd_level 生成一个(0, 1]的折扣系数来计算速度
            # crowd_level越小，速度越接近1.0
            congestion_factor = max(0.1, 1.0 - (r.crowd_level - 1) * 0.1) 
            g.add_edge(str(r.start_poi_id), str(r.end_poi_id), float(r.distance), congestion_factor, t_mode)
            
    finally:
        db.close()

# 单例全局地图对象
campus_graph = Graph() 

