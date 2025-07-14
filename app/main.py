import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api.v1 import sms, admin
from app.services.scheduler_service import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()

    # 启动僵尸任务恢复定时器
    asyncio.create_task(scheduler.start_zombie_task_recovery())

    yield

    # 关闭时停止定时器
    await scheduler.stop_zombie_task_recovery()


# 创建FastAPI应用
app = FastAPI(
    title="LKSMS Service",
    description="短信发送任务服务",
    version="1.0.0",
    lifespan=lifespan,
    # 根据配置决定是否启用文档页面
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sms.router, prefix="/api/v1/sms", tags=["短信服务"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["管理接口"])


@app.get("/")
async def root():
    """根路径"""
    return {"message": "LKSMS Service is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "lksms-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
