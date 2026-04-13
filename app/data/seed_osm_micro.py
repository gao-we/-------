import math
import random
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app.models.domain import Base, Location, POI, Road, User

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))

def seed_data_from_mocked_real_dist():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        loc = Location(name="清华大学景区")
        db.add(loc)
        db.commit()
        db.refresh(loc)
        
        buildings = ["主楼", "二教", "三教", "四教", "五教", "六教", "大礼堂", "清华学堂", "图书馆", "新水木",
                     "紫荆公寓1号楼", "紫荆公寓2号楼", "紫荆公寓3号楼", "紫荆公寓4号楼", "综合体育馆",
                     "工字厅", "照澜院", "理学院楼", "蒙民伟楼", "生命科学馆", "美术学院楼", "苏世民书院"]
        facility_types = ['商店', '饭店', '洗手间', '图书馆', '食堂', '超市', '咖啡馆', '银行', '医院', '快递点', '体育场']
        target_pois = []
        
        for b in buildings:
            target_pois.append({'name': b, 'category': '教学楼' if '教' in b or '楼' in b else '景点', 'lat': 40.000 + random.uniform(-0.01, 0.01), 'lon': 116.325 + random.uniform(-0.01, 0.01)})
            
        for i in range(60):
            ftype = facility_types[i % len(facility_types)]
            target_pois.append({'name': f"{ftype}{i}", 'category': ftype, 'lat': 40.000 + random.uniform(-0.01, 0.01), 'lon': 116.325 + random.uniform(-0.01, 0.01)})
            
        for i in range(120):
            target_pois.append({'name': f"交叉路口_{i}", 'category': '道路口', 'lat': 40.000 + random.uniform(-0.01, 0.01), 'lon': 116.325 + random.uniform(-0.01, 0.01)})
            
        for p in target_pois:
            poi = POI(
                location_id=loc.id,
                name=p['name'],
                category=p['category'],
                latitude=p['lat'],
                longitude=p['lon'],
                image_url=f"https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=400&q=80" if p['category'] not in ['道路口', '洗手间'] else None
            )
            db.add(poi)
            
        db.commit()
        
        pois = db.query(POI).all()
        poi_ids = [p.id for p in pois]
        
        road_count = 0
        added_edges = set()
        
        for i in range(1, len(poi_ids)):
            parent = random.choice(poi_ids[:i])
            child = poi_ids[i]
            
            p1 = next(p for p in pois if p.id == parent)
            p2 = next(p for p in pois if p.id == child)
            dist = haversine(float(p1.latitude), float(p1.longitude), float(p2.latitude), float(p2.longitude))
            if dist < 1: dist = 10
            
            modes = ["walk", "bike"]
            if random.random() > 0.5: modes.append("shuttle")
                
            db.add(Road(start_poi_id=parent, end_poi_id=child, distance=round(dist, 2), crowd_level=random.randint(1, 5), transport_modes=modes))
            db.add(Road(start_poi_id=child, end_poi_id=parent, distance=round(dist, 2), crowd_level=random.randint(1, 5), transport_modes=modes))
            added_edges.add(tuple(sorted([parent, child])))
            road_count += 2
            
        while (road_count / 2) < 250:
            u = random.choice(poi_ids)
            v = random.choice(poi_ids)
            if u != v:
                edge = tuple(sorted([u, v]))
                if edge not in added_edges:
                    p1 = next(p for p in pois if p.id == u)
                    p2 = next(p for p in pois if p.id == v)
                    dist = haversine(float(p1.latitude), float(p1.longitude), float(p2.latitude), float(p2.longitude))
                    if dist < 1: dist = 10
                    
                    modes = ["walk", "bike"]
                    db.add(Road(start_poi_id=u, end_poi_id=v, distance=round(dist, 2), crowd_level=random.randint(1, 5), transport_modes=modes))
                    db.add(Road(start_poi_id=v, end_poi_id=u, distance=round(dist, 2), crowd_level=random.randint(1, 5), transport_modes=modes))
                    added_edges.add(edge)
                    road_count += 2
                    
        db.commit()
        
        for i in range(15):
            db.add(User(username=f"real_user_{i}", email=f"user{i}@test.com", password_hash="secret"))
            
        db.commit()
        
        print(f"🎉 数据库写入完成！")
        print(f"📊 统计数据：")
        print(f"  - 实体 POI (建筑/设施): {len([p for p in target_pois if p['category'] != '道路口'])} 个")
        print(f"    其中建筑物数量: {len(buildings)} 个 (要求>=20个)")
        print(f"    服务设施数量: 60 个 (要求>=50个)")
        print(f"    服务设施种类: {len(facility_types)} 种 (要求>=10种)")
        print(f"  - 总节点数量: {len(target_pois)} 个 (要求>=200)")
        print(f"  - 图结构双向连通边数: {road_count} 条，即无向边 {road_count//2} 条 (要求无向图或道路边数不能少于 200 条)")
        print(f"  - 系统用户数: 15 人 (要求>=10人)")
        
    except Exception as e:
        print(f"发生错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data_from_mocked_real_dist()
