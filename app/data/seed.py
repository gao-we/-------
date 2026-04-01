import random
import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.domain import Base, Location, POI, Road, User, Food, Diary

def seed_data():
    db = SessionLocal()
    
    # 检查是否已有数据
    if db.query(Location).first():
        print("数据已存在，跳过初始化")
        db.close()
        return

    print("开始生成数据并插入 PostgreSQL...")

    # 1. 创建基础 Location
    main_location = Location(name="主校区/主景区", description="系统核心演示区", city="Beijing")
    db.add(main_location)
    db.commit()
    db.refresh(main_location)

    # 2. 生成 210 个 POI 节点
    buildings_categories = ["教学楼", "办公楼", "宿舍楼", "博物馆", "图书馆", "景点_大门"]
    service_categories = ["商店", "饭店", "洗手间", "食堂", "超市", "咖啡馆", "急救点", "饮水机", "ATM", "停车场", "休息长椅"]
    
    pois = []
    from app.data.recommendation_data import attractions_data, foods_data
    # 使用推荐数据中的真实数据
    for i, a in enumerate(attractions_data[:80]):
        poi = POI(
            location_id=main_location.id,
            name=a.name,
            category=a.category,
            latitude=random.uniform(39.9, 40.0),
            longitude=random.uniform(116.3, 116.4),
            image_url=a.image_url
        )
        pois.append(poi)
    
    # 服务设施
    for i in range(1, 31):
        poi = POI(
            location_id=main_location.id,
            name=f"设施_{i}",
            category=random.choice(service_categories),
            latitude=random.uniform(39.9, 40.0),
            longitude=random.uniform(116.3, 116.4)
        )
        pois.append(poi)

    # 道路路口 (120个)
    for i in range(1, 121):
        poi = POI(
            location_id=main_location.id,
            name=f"路口_{i}",
            category="道路口",
            latitude=random.uniform(39.9, 40.0),
            longitude=random.uniform(116.3, 116.4)
        )
        pois.append(poi)

    db.add_all(pois)
    db.commit()

    # 重新查出所有的 POI 获得它们的 ID
    all_pois = db.query(POI).all()
    poi_ids = [p.id for p in all_pois]

    # 3. 生成 300+ 条 Road
    roads = []
    # 连通树保证所有节点连通
    for i in range(1, len(poi_ids)):
        parent_id = random.choice(poi_ids[:i])
        roads.append(Road(
            start_poi_id=poi_ids[i],
            end_poi_id=parent_id,
            distance=round(random.uniform(10.0, 500.0), 2),
            crowd_level=random.randint(1, 10),
            transport_modes=["walk"]
        ))

    # 额外随机边
    for _ in range(150):
        u = random.choice(poi_ids)
        v = random.choice(poi_ids)
        if u != v:
            roads.append(Road(
                start_poi_id=u,
                end_poi_id=v,
                distance=round(random.uniform(10.0, 300.0), 2),
                crowd_level=random.randint(1, 10),
                transport_modes=[random.choice(["walk", "bike", "shuttle"])]
            ))
    
    db.add_all(roads)
    db.commit()

    # 4. 生成 Foods
    foods = []
    for i in range(1, 40):
        foods.append(Food(
            location_id=main_location.id,
            poi_id=random.choice(poi_ids),
            name=f"特色美食_{i}",
            price_range=random.choice(["¥0-20", "¥20-50", "¥50-100", "¥100+"]),
            rating=round(random.uniform(3.0, 5.0), 2)
        ))
    db.add_all(foods)

    # 5. 生成 Users
    users = []
    for i in range(1, 10):
        users.append(User(
            username=f"test_user_{i}",
            email=f"user{i}@example.com",
            password_hash="hashed_pw_here"
        ))
    db.add_all(users)
    db.commit()

    print("数据库基础数据初始化(Seed)完成！")
    db.close()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_data()
