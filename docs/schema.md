# 个性化旅游系统数据库设计文档 (PostgreSQL)

本文档详细描述了个性化旅游系统的数据库结构（ER模型），包括表名、字段、数据类型、主外键关系以及设计初衷。

## 实体关系 (ER) 概述

- **User (用户)**: 系统的核心，可以发布日记(Diary)、发表评论(Comment)。
- **Location (景区/校区)**: 顶层地点，包含多个POI和食物推荐。
- **POI (建筑/服务设施)**: 具体的兴趣点，隶属于某个Location。
- **Road (道路/路线)**: 表示POI之间的连接，支持寻路算法。
- **Food (美食)**: 关联到具体的Location或POI，供用户参考。
- **Diary (旅游日记)**: 用户关联到Location发布的游记。
- **Comment (评论/评分)**: 用户对特定POI、Food或Location的评价。

---

## 表结构设计

### 1. 用户表 (`users`)
存储系统用户的基本信息。
- `id` (UUID, PK): 唯一标识
- `username` (VARCHAR): 用户名，唯一
- `email` (VARCHAR): 邮箱，唯一
- `password_hash` (VARCHAR): 加密密码
- `created_at` (TIMESTAMP)

### 2. 景区/校区表 (`locations`)
表示大的旅游区域或校区。
- `id` (SERIAL, PK): 区域ID
- `name` (VARCHAR): 景区名称
- `description` (TEXT): 描述
- `city` (VARCHAR): 所在城市
- `created_at` (TIMESTAMP)

### 3. 设施/建筑表 (`pois`)
Points of Interest (兴趣点)，如某栋教学楼、某个服务中心。
- `id` (SERIAL, PK)
- `location_id` (INT, FK -> locations.id): 所属景区
- `name` (VARCHAR): 设施名称
- `category` (VARCHAR): 分类 (如 restroom, building, service)
- `latitude` (DECIMAL): 纬度
- `longitude` (DECIMAL): 经度

### 4. 道路连通表 (`roads`)
有向或无向图的边，用于规划最短路径。
- `id` (SERIAL, PK)
- `start_poi_id` (INT, FK -> pois.id): 起点设施
- `end_poi_id` (INT, FK -> pois.id): 终点设施
- `distance` (DECIMAL): 距离 (米)
- `crowd_level` (INT): 拥挤度 (1-10)
- `transport_modes` (VARCHAR[]): 支持的交通方式 (如 walk, bike, bus)

### 5. 美食表 (`foods`)
区域内的美食推荐。
- `id` (SERIAL, PK)
- `location_id` (INT, FK -> locations.id): 所属景区
- `poi_id` (INT, FK -> pois.id): 具体的餐馆POI (可选)
- `name` (VARCHAR): 食物名称
- `price_range` (VARCHAR): 价格区间
- `rating` (DECIMAL): 平均评分

### 6. 旅游日记表 (`diaries`)
用户分享的旅游体验。
- `id` (SERIAL, PK)
- `user_id` (UUID, FK -> users.id): 作者
- `location_id` (INT, FK -> locations.id): 关联景区
- `title` (VARCHAR): 日记标题
- `content` (TEXT): 正文内容
- `images` (TEXT[]): 图片URL数组
- `video_path` (VARCHAR): 视频URL (可选)
- `views` (INT): 浏览量/热度
- `rating` (DECIMAL): 作者给景区的评分
- `created_at` (TIMESTAMP)

### 7. 评论评分表 (`comments`)
多态设计，能够点评景区、具体设施或美食。
- `id` (SERIAL, PK)
- `user_id` (UUID, FK -> users.id): 评论者
- `target_type` (VARCHAR): 评论目标类型 ('location', 'poi', 'food')
- `target_id` (INT): 目标ID
- `rating` (INT): 评分 1-5
- `content` (TEXT): 评论内容
- `created_at` (TIMESTAMP)

## 设计说明
1. **空间与图结构**: `pois` 与 `roads` 构成了图结构，方便后续后端使用 Dijkstra 或 A* 算法计算最短、最少拥挤道路。
2. **多媒体存储**: `diaries` 采用 PostgreSQL 的 `TEXT[]` 数组来存储多张图片链接，避免额外引入中间表，提高查询效率。
3. **扩展性**: `comments` 表使用 `target_type` 和 `target_id`进行多态关联，使其能够支持对美食、设施或景区本身进行点评，而不需要建立三张不同的评论表。
