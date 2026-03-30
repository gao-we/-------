from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.models.schemas import RouteRequest
from app.data.map_builder import campus_graph

router = APIRouter()

@router.post("/shortest_path")
def calculate_shortest_path(
    request: RouteRequest, 
    strategy: str = Query("distance", description="策略：distance 或 time"),
    transport: str = Query("any", description="交通工具：walk, bike, shuttle, any")
):
    """
    计算两个地理位置之间的最优路径，或者多点的环游路径。
    使用自定义 Dijkstra 算法实现。
    """
    if request.start_id not in campus_graph.adj_list:
        raise HTTPException(status_code=404, detail="Start location not found")
        
    if request.waypoints and len(request.waypoints) > 0:
        # 如果有途经点，调用 TSP 算法 (多点游览最后回到起点)
        path, dist = campus_graph.find_tsp_path(request.start_id, request.waypoints)
        return {
            "status": "success",
            "message": "多点环游最短路径 (TSP近似)",
            "route": path,
            "total_weight": dist
        }
    else:
        # 单目标路线规划
        if request.end_id not in campus_graph.adj_list:
            raise HTTPException(status_code=404, detail="End location not found")
            
        path, cost = campus_graph.dijkstra(
            request.start_id, 
            request.end_id, 
            weight_strategy=strategy, 
            transport_mode=transport
        )
        return {
            "status": "success",
            "strategy": strategy,
            "transport_mode": transport,
            "route": path,
            "total_cost": cost
        }

@router.get("/locations/search")
def search_locations(start_id: str, category: str, max_distance: float = 1000.0):
    """
    场所查询：输入起点、想寻找的类别（如：洗手间、食堂），返回按照实际步行最短距离排序的结果。
    不能使用直线距离，内部调用 Dijkstra 的 BFS 变体进行范围搜索。
    """
    if start_id not in campus_graph.adj_list:
        raise HTTPException(status_code=404, detail="Start location not found")
        
    results = campus_graph.find_nearby_facilities(start_id, category, max_distance)
    return {
        "status": "success",
        "start": start_id,
        "category_searched": category,
        "results": results
    }

@router.get("/graph/nodes")
def get_all_nodes():
    """获取所有节点用于前端展示地图"""
    return {
        "total": len(campus_graph.node_info),
        "nodes": campus_graph.node_info
    }
