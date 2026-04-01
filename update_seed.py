import re

with open("app/data/seed.py", "r") as f:
    content = f.read()

new_content = content.replace("""    # 建筑物 (30个)
    for i in range(1, 31):
        poi = POI(
            location_id=main_location.id,
            name=f"建筑物_{i}",
            category=random.choice(buildings_categories),
            latitude=random.uniform(39.9, 40.0),
            longitude=random.uniform(116.3, 116.4)
        )
        pois.append(poi)""", 
"""    from app.data.recommendation_data import attractions_data, foods_data
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
        pois.append(poi)""")

new_content = new_content.replace("""    # 服务设施 (60个)
    for i in range(1, 61):
        poi = POI(
            location_id=main_location.id,
            name=f"设施_{i}",
            category=random.choice(service_categories),
            latitude=random.uniform(39.9, 40.0),
            longitude=random.uniform(116.3, 116.4)
        )
        pois.append(poi)""",
"""    # 服务设施
    for i in range(1, 31):
        poi = POI(
            location_id=main_location.id,
            name=f"设施_{i}",
            category=random.choice(service_categories),
            latitude=random.uniform(39.9, 40.0),
            longitude=random.uniform(116.3, 116.4)
        )
        pois.append(poi)""")

with open("app/data/seed.py", "w") as f:
    f.write(new_content)
