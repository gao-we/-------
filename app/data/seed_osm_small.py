import requests
import json
import math
import random
import os
import sys

# 将项目根目录加入路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.domain import Base, Location, POI, Road, Food, User
from app.data.recommendation_data import foods_data

# 计算地球上两点间的距离（米）
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # 地球半径，单位为米
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + \
        math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))

def fetch_osm_data():
    print("🌍 正在从 OpenStreetMap (Kumi Endpoint) 爬取小规模北京清华大学周边的真实数据...")
    url = "https://overpass.kumi.systems/api/interpreter"
    
    # 缩小范围以避免超时 (39.995, 116.315, 40.010, 116.330)
    query = """
    [out:json][timeout:30];
    node(39.995, 116.315, 40.010, 116.330)->.allnodes;
    (
      way["building"](39.995, 116.315, 40.010, 116.330);
      node["building"](39.995, 116.315, 40.010, 116.330);
      node["amenity"](39.995, 116.315, 40.010, 116.330);
      node["shop"](39.995, 116.315, 40.010, 116.330);
      way["highway"](39.995, 116.315, 40.010, 116.330);
    );
    out body;
    >;
    out skel qt;
    """
    try:
        response = requests.post(url, data={'data': query})
        response.raise_for_status()
        print("✅ 真实数据下载成功！")
        return response.json()
    except Exception as e:
        print(f"❌ 下载失败，改用 overpass-api.de: {e}")
        try:
            url_alt = "https://overpass-api.de/api/interpreter"
            response = requests.post(url_alt, data={'data': query})
            response.raise_for_status()
            print("✅ 真实数据下载成功 (DE节点)！")
            return response.json()
        except Exception as e2:
            print(f"❌ 下载全失败: {e2}")
            return None

def seed_osm_data():
    data = fetch_osm_data()
    if not data:
        print("未获取到数据，直接返回。")
        return
        
    print("🔄 开始处理数据并写入数据库...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        elements = data.get('elements', [])
        nodes_map = {}
        target_pois = []
        highways = []
        
        facility_types_map = {
            'toilets': '洗手间', 'restaurant': '饭店', 'cafe': '咖啡馆',
            'fast_food': '食堂', 'library': '图书馆', 'supermarket': '超市',
            'convenience': '商店', 'bank': '银行', 'hospital': '医院',
            'clinic': '诊所', 'vending_machine': '自动售货机'
        }
        
        # 1. 创建地点
        loc = Location(name="清华大学及周边", description="真实地理数据导入", latitude=40.000, longitude=116.325)
        db.add(loc)
        db.commit()
        db.refresh(loc)
        
        # 2. 解析节点
        for el in elements:
            if el['type'] == 'node':
                nodes_map[el['id']] = el
                tags = el.get('tags', {})
                name = tags.get('name', '')
                
                amenity = tags.get('amenity')
                shop = tags.get('shop')
                facility_type = None
                
                if amenity in facility_types_map:
                    facility_type = facility_types_map[amenity]
                elif shop in ['supermarket', 'convenience']:
                    facility_type = facility_types_map[shop]
                elif shop:
                    facility_type = '商店'
                    
                if facility_type:
                    target_pois.append({
                        'osm_id': el['id'], 'name': name or f"真实{facility_type}", 
                        'category': facility_type, 'lat': el['lat'], 'lon': el['lon']
                    })
                    continue
                    
                if 'building' in tags and name:
                    target_pois.append({
                        'osm_id': el['id'], 'name': name, 'category': '教学楼' if '楼' in name else '景点',
                        'lat': el['lat'], 'lon': el['lon']
                    })

        # 3. 解析路和区
        for el in elements:
            if el['type'] == 'way':
                tags = el.get('tags', {})
                nodes = el.get('nodes', [])
                if 'highway' in tags and len(nodes) > 1:
                    highways.append((nodes, tags))
                elif 'building' in tags and len(nodes) > 0 and 'name' in tags:
                    n_id = nodes[0]
                    if n_id in nodes_map:
                        n = nodes_map[n_id]
                        target_pois.append({
                            'osm_id': el['id'], 'name': tags['name'], 'category': '建筑物',
                            'lat': n['lat'], 'lon': n['lon']
                        })

        used_highway_nodes = set()
        for nodes, _ in highways:
            for n in nodes:
                used_highway_nodes.add(n)
                
        osm_to_db_id = {}
        for p in target_pois:
            poi = POI(
                location_id=loc.id,
                name=p['name'],
                description="真实世界抓取的兴趣点",
                category=p['category'],
                latitude=p['lat'],
                longitude=p['lon'],
                rating=round(random.uniform(3.5, 5.0), 1),
                heat_score=random.randint(100, 10000),
                image_url=f"https://source.unsplash.com/400x300/?{p['category']},building"
            )
            db.add(poi)
            db.commit()
            db.refresh(poi)
            osm_to_db_id[p['osm_id']] = poi.id
            if p['osm_id'] in used_highway_nodes:
                used_highway_nodes.remove(p['osm_id'])

        road_nodes_added = 0
        for n_id in used_highway_nodes:
            if n_id in nodes_map and road_nodes_added < 300:
                n = nodes_map[n_id]
                poi = POI(
                    location_id=loc.id,
                    name=f"路口_{n_id}",
                    description="导航节点",
                    category="道路口",
                    latitude=n['lat'],
                    longitude=n['lon'],
                    rating=0,
                    heat_score=0
                )
                db.add(poi)
                db.commit()
                db.refresh(poi)
                osm_to_db_id[n_id] = poi.id
                road_nodes_added += 1

        road_count = 0
        added_edges = set()
        for nodes, tags in highways:
            for i in range(len(nodes) - 1):
                n1_osm, n2_osm = nodes[i], nodes[i+1]
                if n1_osm in osm_to_db_id and n2_osm in osm_to_db_id:
                    db_id1, db_id2 = osm_to_db_id[n1_osm], osm_to_db_id[n2_osm]
                    edge_key = tuple(sorted([db_id1, db_id2]))
                    if edge_key in added_edges or db_id1 == db_id2: continue
                    added_edges.add(edge_key)
                    
                    n1, n2 = nodes_map[n1_osm], nodes_map[n2_osm]
                    dist = haversine(n1['lat'], n1['lon'], n2['lat'], n2['lon'])
                    if dist <= 0: dist = 1.0
                        
                    hw_type = tags.get('highway', 'pedestrian')
                    modes = ["walk"]
                    if hw_type in ['primary', 'secondary', 'tertiary', 'residential']:
                        modes = ["walk", "bike", "shuttle"]
                    elif hw_type == 'cycleway':
                        modes = ["walk", "bike"]
                        
                    db.add(Road(start_poi_id=db_id1, end_poi_id=db_id2, distance=round(dist, 2), crowd_level=random.randint(1, 5), transport_modes=modes))
                    db.add(Road(start_poi_id=db_id2, end_poi_id=db_id1, distance=round(dist, 2), crowd_level=random.randint(1, 5), transport_modes=modes))
                    road_count += 2
        
        db.commit()
        
        for i in range(15):
            db.add(User(username=f"real_user_{i}", email=f"user{i}@test.com", password_hash="secret"))
            
        all_pois = db.query(POI).filter(POI.category != '道路口').all()
        if all_pois:
            for food_data in foods_data:
                poi = random.choice(all_pois)
                f = Food(
                    poi_id=poi.id, name=food_data["name"], cuisine=food_data["cuisine"],
                    price_level=food_data["price_level"], rating=food_data["rating"],
                    heat_score=food_data["heat_score"], image_url=food_data.get("image_url")
                )
                db.add(f)
        
        db.commit()
        print(f"🎉 数据库写入完成！")
        print(f"📊 统计数据：")
        print(f"  - 实体 POI (建筑/设施): {len(target_pois)} 个 (需求要求>=20，设施>=50)")
        print(f"  - 额外导航路口: {road_nodes_added} 个")
        print(f"  - 真实道路连接 (单向边数): {road_count} 条 (需求要求 >= 200)")
        print(f"  - 测试用户: 15 人 (需求要求 >= 10)")
        
    except Exception as e:
        print(f"发生错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_osm_data()
