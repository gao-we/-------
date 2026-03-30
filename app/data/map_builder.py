import random
from app.core.algorithms.graph_algo import Graph

def build_campus_scene_graph() -> Graph:
    """
    根据讲义要求构建基础图的模拟数据。
    要求：
    - 建筑物(景点/主楼) >= 20个
    - 设施(食堂/卫生间等) >= 50个
    - 节点总量 >= 200，边 >= 200
    """
    g = Graph()
    
    # 类别
    buildings_categories = ["教学楼", "办公楼", "宿舍楼", "博物馆", "图书馆", "图书馆", "景点_大门"]
    service_categories = ["商店", "饭店", "洗手间", "食堂", "超市", "咖啡馆", "急救点", "饮水机", "ATM", "停车场", "休息长椅"]
    
    # 构建建筑物 (30个)
    for i in range(1, 31):
        g.add_node(f"B{i}", f"建筑物{i}", random.choice(buildings_categories))
        
    # 构建服务设施 (60个)
    for i in range(1, 61):
        g.add_node(f"S{i}", f"设施{i}", random.choice(service_categories))
        
    # 构建其他道路交汇点 (小路口) (120个) 以满足200个节点的硬性规定
    for i in range(1, 121):
        g.add_node(f"R{i}", f"路口{i}", "道路口")
        
    # 构建随机边 (保证所有节点都在一个连通分支里比较麻烦，但可以用简单的线或树结构叠加随机边保证密度)
    nodes = list(g.adj_list.keys())
    
    # 构建一棵基本生成的树以保证连通性
    for i in range(1, len(nodes)):
        parent = random.choice(nodes[:i]) # 选一个前面的节点作为父节点
        dist = round(random.uniform(10.0, 500.0), 2)
        cong = round(random.uniform(0.5, 1.0), 2) # 当前道路拥挤度 0.5 - 1.0
        g.add_edge(nodes[i], parent, dist, cong, "walk")
        
    # 增加额外的边，达到 >= 300 条边
    for _ in range(150):
        u = random.choice(nodes)
        v = random.choice(nodes)
        if u != v:
            dist = round(random.uniform(10.0, 300.0), 2)
            cong = round(random.uniform(0.2, 1.0), 2)
            trans = random.choice(["walk", "bike", "shuttle"]) # 步行，自行车，电瓶车
            g.add_edge(u, v, dist, cong, trans)
            
    return g

# 单例全局地图对象
campus_graph = build_campus_scene_graph()
