import math
import random
from typing import Dict, List, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models.domain import Base, Comment, Diary, Food, Location, POI, Road, User
from app.data.beijing_web_seed import (
    fetch_beijing_destinations,
    fetch_beijing_foods,
    fetch_beijing_services,
)


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * (math.sin(dl / 2) ** 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _detect_legacy_dataset(db: Session) -> bool:
    old_location = db.query(Location).filter(Location.name == "主校区/主景区").first()
    old_tsinghua = db.query(POI).filter(POI.name.like("%清华%")).first()
    return old_location is not None or old_tsinghua is not None


def _clear_content_tables(db: Session) -> None:
    db.query(Comment).delete()
    db.query(Diary).delete()
    db.query(Food).delete()
    db.query(Road).delete()
    db.query(POI).delete()
    db.query(Location).delete()
    db.commit()


def _seed_users_if_empty(db: Session, count: int = 12) -> None:
    if db.query(User).count() > 0:
        return
    users = [
        User(
            username=f"beijing_user_{i}",
            email=f"beijing_user_{i}@example.com",
            password_hash="hashed_pw_here",
        )
        for i in range(1, count + 1)
    ]
    db.add_all(users)
    db.commit()


def _ensure_indexes(db: Session) -> None:
    """
    为高频查询补充索引，优化推荐和寻路相关查询。
    """
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_pois_location_id ON pois(location_id)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_pois_category ON pois(category)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_pois_name ON pois(name)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_foods_location_id ON foods(location_id)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_foods_poi_id ON foods(poi_id)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_foods_name ON foods(name)"))
    db.execute(text("CREATE INDEX IF NOT EXISTS idx_roads_start_end ON roads(start_poi_id, end_poi_id)"))
    db.commit()


def _build_roads_for_pois(pois: List[POI]) -> List[Road]:
    """
    使用经纬度近邻关系构建连通道路图，避免随机边导致数据失真。
    """
    random.seed(2026)
    id_to_coord: Dict[int, Tuple[float, float]] = {
        p.id: (float(p.latitude), float(p.longitude)) for p in pois
    }
    poi_ids = [p.id for p in pois]
    edges = set()
    roads: List[Road] = []

    # 先构建链路保证整体连通
    for idx in range(1, len(poi_ids)):
        u = poi_ids[idx - 1]
        v = poi_ids[idx]
        if u == v:
            continue
        key = (min(u, v), max(u, v))
        if key in edges:
            continue
        edges.add(key)
        dist = _haversine_meters(*id_to_coord[u], *id_to_coord[v])
        roads.append(
            Road(
                start_poi_id=u,
                end_poi_id=v,
                distance=round(max(10.0, dist), 2),
                crowd_level=random.randint(1, 10),
                transport_modes=["walk"],
            )
        )

    # 每个点再连 2 个最近邻
    for u in poi_ids:
        lat_u, lon_u = id_to_coord[u]
        nearest: List[Tuple[float, int]] = []
        for v in poi_ids:
            if u == v:
                continue
            lat_v, lon_v = id_to_coord[v]
            nearest.append((_haversine_meters(lat_u, lon_u, lat_v, lon_v), v))
        nearest.sort(key=lambda x: x[0])
        for dist, v in nearest[:2]:
            key = (min(u, v), max(u, v))
            if key in edges:
                continue
            edges.add(key)
            modes = ["walk"]
            if dist > 1500:
                modes.append("bike")
            if dist > 4000:
                modes.append("shuttle")
            roads.append(
                Road(
                    start_poi_id=u,
                    end_poi_id=v,
                    distance=round(max(10.0, dist), 2),
                    crowd_level=random.randint(1, 10),
                    transport_modes=modes,
                )
            )

    return roads


def _seed_beijing_web_data(db: Session) -> None:
    """
    删除旧内容并用在线抓取的北京景区/学校/服务设施/美食数据重建数据库。
    """
    destinations = fetch_beijing_destinations(limit=260)
    services = fetch_beijing_services(limit=170)
    foods = fetch_beijing_foods(limit=140)
    if len(destinations) < 40:
        raise RuntimeError("在线抓取到的北京景区/学校数据不足，无法完成初始化。")

    _clear_content_tables(db)

    location = Location(name="北京市", description="在线抓取的北京景区与学校数据集", city="Beijing")
    db.add(location)
    db.commit()
    db.refresh(location)

    pois: List[POI] = []
    for p in destinations + services:
        if "清华" in p.name:
            continue
        pois.append(
            POI(
                location_id=location.id,
                name=p.name,
                category=p.category,
                latitude=round(p.latitude, 7),
                longitude=round(p.longitude, 7),
                image_url=p.image_url if p.image_url else None,
            )
        )

    db.add_all(pois)
    db.commit()

    all_pois = db.query(POI).filter(POI.location_id == location.id).all()
    poi_ids = [p.id for p in all_pois]
    if len(poi_ids) < 80:
        raise RuntimeError("抓取后 POI 数量不足，无法构建有效推荐系统。")

    roads = _build_roads_for_pois(all_pois)
    db.add_all(roads)
    db.commit()

    destination_ids = [p.id for p in all_pois if p.category in ("景区", "学校", "博物馆")]
    if not destination_ids:
        destination_ids = poi_ids

    random.seed(2026)
    food_rows: List[Food] = []
    for item in foods:
        if "清华" in item.name:
            continue
        food_rows.append(
            Food(
                location_id=location.id,
                poi_id=random.choice(destination_ids),
                name=item.name,
                price_range=random.choice(["¥0-20", "¥20-50", "¥50-100", "¥100+"]),
                rating=round(random.uniform(3.5, 5.0), 2),
                image_url=None,
            )
        )
    db.add_all(food_rows)
    db.commit()

    _seed_users_if_empty(db)
    _ensure_indexes(db)


def seed_data(force_reseed: bool = False) -> None:
    db = SessionLocal()
    try:
        has_data = db.query(Location).first() is not None
        legacy = _detect_legacy_dataset(db)

        if has_data and not force_reseed and not legacy:
            print("数据库已有非旧版数据，跳过初始化。")
            return

        print("开始使用在线北京数据重建数据库...")
        _seed_beijing_web_data(db)
        print("数据库已完成北京景区/学校在线数据初始化。")
    finally:
        db.close()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_data(force_reseed=True)
