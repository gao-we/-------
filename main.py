from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import routes_a, routes_b, routes_c
from app.database import engine
from app.models.domain import Base
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    # 2. 从数据库初始化测试数据（如果没有的话）
    from app.data.seed import seed_data
    seed_data()
    
    # 3. 将数据库中的节点与边载入内存邻接表
    import app.data.map_builder as mb
    mb.load_graph_from_db(mb.campus_graph)
    # 同时可以初始化搜索引擎 Trie/KMP 等
    
    yield
    # 清理阶段（例如关闭一些连接）

app = FastAPI(
    title="个性化旅游系统 API",
    description="数据结构大作业 - 后端系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置，方便前端联调
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册三位成员的独立路由模块
app.include_router(routes_a.router, prefix="/api/routing", tags=["地图与路径规划 (成员A)"])
app.include_router(routes_b.router, prefix="/api/recommendation", tags=["推荐系统 (成员B)"])
app.include_router(routes_c.router, prefix="/api/social", tags=["旅游社区与日记 (成员C)"])

@app.get("/")
def read_root():
    return {"message": "欢迎访问个性化旅游系统 API。请访问 /docs 查看API文档。"}
