-- 启用 pgcrypto 插件以支持 UUID
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 创建用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建景区/校区表
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    city VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建设施(POI)表
CREATE TABLE pois (
    id SERIAL PRIMARY KEY,
    location_id INT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7)
);

-- 创建道路表(用于图论导航)
CREATE TABLE roads (
    id SERIAL PRIMARY KEY,
    start_poi_id INT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    end_poi_id INT NOT NULL REFERENCES pois(id) ON DELETE CASCADE,
    distance DECIMAL(8, 2) NOT NULL,
    crowd_level INT DEFAULT 1 CHECK (crowd_level BETWEEN 1 AND 10),
    transport_modes VARCHAR(50)[] -- 例如: '{"walk", "bike"}'
);

-- 创建美食表
CREATE TABLE foods (
    id SERIAL PRIMARY KEY,
    location_id INT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    poi_id INT REFERENCES pois(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    price_range VARCHAR(50),
    rating DECIMAL(3, 2) DEFAULT 0.0 CHECK (rating BETWEEN 0.0 AND 5.0)
);

-- 创建旅游日记表
CREATE TABLE diaries (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    location_id INT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    content TEXT NOT NULL,
    images TEXT[],         -- 保存图片URL列表 (PostgreSQL 数组特性)
    video_path VARCHAR(255),
    views INT DEFAULT 0,   -- 浏览量/热度
    rating DECIMAL(3, 2) CHECK (rating BETWEEN 0.0 AND 5.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建评论与评分表
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type VARCHAR(20) NOT NULL CHECK (target_type IN ('location', 'poi', 'food')),
    target_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-----------------------------------------------------------
-- 性能优化：创建常用查询索引
-----------------------------------------------------------

-- POI按景区查询索引，加快地图加载
CREATE INDEX idx_pois_location_id ON pois(location_id);

-- 道路寻路相关的起点终点索引，支持快速图构建
CREATE INDEX idx_roads_pathfinding ON roads(start_poi_id, end_poi_id);

-- 日记按热度(视图数)倒序查询和景区查询索引，支持 Top-K 计算
CREATE INDEX idx_diaries_location_id ON diaries(location_id);
CREATE INDEX idx_diaries_views ON diaries(views DESC);

-- 评论按目标查询的组合索引，加快拉取详情页评论
CREATE INDEX idx_comments_target ON comments(target_type, target_id);