from fastapi import APIRouter

router = APIRouter(tags=["系统"])


@router.get("/health", summary="健康检查")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "backend",
        "message": "服务运行正常",
    }
