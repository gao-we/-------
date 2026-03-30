from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import routes_a, routes_b, routes_c

app = FastAPI(
    title="个性化旅游系统 API",
    description="数据结构大作业 - 后端系统",
    version="1.0.0"
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
