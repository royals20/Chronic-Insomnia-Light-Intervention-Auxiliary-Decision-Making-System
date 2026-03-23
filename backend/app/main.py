from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.data_imports import router as data_import_router
from app.api.routes.health import router as health_router
from app.api.routes.model_center import router as model_center_router
from app.api.routes.patients import router as patient_router
from app.api.routes.quality import router as quality_router
from app.api.routes.recommendations import router as recommendation_router
from app.api.routes.reports import router as report_router
from app.api.routes.system_settings import router as system_settings_router
from app.api.routes.users import router as user_router
from app.core.config import get_settings
from app.db.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="慢性失眠光干预科研辅助决策系统后端服务",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(user_router, prefix=settings.api_v1_prefix)
app.include_router(patient_router, prefix=settings.api_v1_prefix)
app.include_router(data_import_router, prefix=settings.api_v1_prefix)
app.include_router(quality_router, prefix=settings.api_v1_prefix)
app.include_router(recommendation_router, prefix=settings.api_v1_prefix)
app.include_router(report_router, prefix=settings.api_v1_prefix)
app.include_router(system_settings_router, prefix=settings.api_v1_prefix)
app.include_router(model_center_router, prefix=settings.api_v1_prefix)


@app.get("/", summary="根路径")
def read_root() -> dict[str, str]:
    return {
        "message": "慢性失眠光干预科研辅助决策系统后端服务已启动",
        "notice": "仅供科研辅助，不替代临床诊断与治疗",
    }
