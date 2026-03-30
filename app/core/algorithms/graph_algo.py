from typing import Dict, List, Tuple
from app.core.algorithms.heap_pq import MinHeap

class Graph:
    """
    手写的图结构（Adjacency List 邻接表实现）。
    满足数据结构作业考核要求。
    """
    def __init__(self):
        # 邻接表存储：{ node_id: [(neighbor_id, distance, congestion, transport_type), ...] }
        self.adj_list: Dict[str, List[Tuple[str, float, float, str]]] = {}
        # 存储节点基础信息用于辅助： { node_id: {name, category, ...} }
        self.node_info: Dict[str, dict] = {}

    def add_node(self, node_id: str, name: str, category: str):
        if node_id not in self.adj_list:
            self.adj_list[node_id] = []
            self.node_info[node_id] = {"name": name, "category": category}

    def add_edge(self, u: str, v: str, distance: float, congestion: float = 1.0, transport_type: str = "walk"):
        """
        添加无向边（假设双向通行）。
        拥挤度(congestion)默认为1.0，值越小代表越拥堵（真实速度=理想速度*拥挤度，时间=距离/(理想速度*拥挤度)）。
        """
        self.adj_list[u].append((v, distance, congestion, transport_type))
        self.adj_list[v].append((u, distance, congestion, transport_type))

    def dijkstra(self, start_id: str, end_id: str, weight_strategy: str = "distance", transport_mode: str = "any") -> Tuple[List[str], float]:
        """
        Dijkstra 最短路径算法。
        策略：
        - "distance": 最短物理距离
        - "time": 最短时间（考虑拥挤度）
        """
        if start_id not in self.adj_list:
            return [], -1.0
            
        distances = {node: float('inf') for node in self.adj_list}
        distances[start_id] = 0
        parents = {node: None for node in self.adj_list}
        
        pq = MinHeap()
        pq.push(0, start_id)
        
        # 记录节点是否已被访问（防止重复扩展）
        visited = set()

        while not pq.is_empty():
            current_dist, current_node = pq.pop()
            
            if current_node in visited:
                continue
            visited.add(current_node)
            
            if current_node == end_id:
                break
                
            for neighbor, dist, cong, trans in self.adj_list[current_node]:
                # 根据指定出行方式过滤边（"any" 允许所有）
                if transport_mode != "any" and trans != transport_mode and trans != "walk":
                    # 总是可以作为步行保底(简化逻辑)
                    continue

                # 计算边的权重
                weight = dist
                if weight_strategy == "time":
                    # 根据 PPT 需求：真实速度 = 理想速度(这里设为1当作基准) * 拥挤度(<=1)
                    # 耗时 = 距离 / 真实速度
                    speed = 1.0 * cong
                    weight = dist / max(0.01, speed)   # 避免除以0
                
                new_dist = current_dist + weight
                
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    parents[neighbor] = current_node
                    pq.push(new_dist, neighbor)
                    
        # 回溯构建路径
        if distances.get(end_id) == float('inf'):
            return [], -1.0 # 无法到达
            
        path = []
        curr = end_id
        while current_node is not None:
            path.append(curr)
            curr = parents[curr]
            if curr is None:
                break
        
        path.reverse()
        return path, distances[end_id]

    def find_tsp_path(self, start_id: str, waypoints: List[str]) -> Tuple[List[str], float]:
        """
        多点途经规划 (旅行商问题近似/贪心解法：最近邻点算法)
        从 start_id 出发，经过所有 waypoints，并要求返回 start_id
        """
        unvisited = set(waypoints)
        current = start_id
        full_path = [start_id]
        total_dist = 0.0
        
        # 每次寻找距离当前点最近的一个未访问目标点
        while unvisited:
            best_next = None
            best_dist = float('inf')
            best_sub_path = []
            
            for wp in unvisited:
                sub_path, dist = self.dijkstra(current, wp, "distance")
                if dist < best_dist and dist != -1:
                    best_dist = dist
                    best_next = wp
                    best_sub_path = sub_path
            
            if not best_next:
                # 有些点不可达
                break
                
            unvisited.remove(best_next)
            # sub_path_1[1:] 避免首尾重复点
            full_path.extend(best_sub_path[1:])
            total_dist += best_dist
            current = best_next
            
        # 回到起点
        if current != start_id:
            sub_path, dist = self.dijkstra(current, start_id, "distance")
            if dist != -1:
                full_path.extend(sub_path[1:])
                total_dist += dist
                
        return full_path, total_dist
        
    def find_nearby_facilities(self, start_id: str, target_category: str, max_distance: float) -> List[dict]:
        """
        场所核心查询：查找一定范围内(通过图 BFS/Dijkstra 的实际路径，而非直线)的某类服务设施
        """
        near_facilities = []
        
        distances = {node: float('inf') for node in self.adj_list}
        distances[start_id] = 0
        pq = MinHeap()
        pq.push(0, start_id)
        visited = set()
        
        while not pq.is_empty():
            dist, node = pq.pop()
            
            # 如果出队的节点距离已经超过范围，提前剪枝
            if dist > max_distance:
                break
                
            if node in visited: continue
            visited.add(node)
            
            # 记录符合条件的设施
            if self.node_info[node].get("category") == target_category and node != start_id:
                info = dict(self.node_info[node])
                info["id"] = node
                info["distance"] = dist
                near_facilities.append(info)
                
            for neighbor, border_dist, _, _ in self.adj_list[node]:
                new_dist = dist + border_dist
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    pq.push(new_dist, neighbor)
                    
        # 按距离排序(也可交由成员 B 的优先级队列 Top-K 处理，此处简单直接返回后由上层再排)
        near_facilities.sort(key=lambda x: x["distance"])
        return near_facilities
