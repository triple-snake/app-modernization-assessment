from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from config import settings
from routers import api_v2_router, auth_router
from models.database import engine, Base

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    description="App Modernization Assessment 백엔드 서버"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)      # /api/v1/auth
app.include_router(api_v2_router)    # /api/v1

# 정적 파일 호스팅 (프론트엔드)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 이벤트"""
    print(f"🚀 {settings.APP_NAME} v{settings.VERSION} 서버 시작")
    print(f"📊 Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"🔍 Qdrant RAG: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}/{settings.QDRANT_MODERNIZATION_RAG}")
    print(f"🔍 Qdrant LSTM: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}/{settings.QDRANT_SYSTEM_METRICS_LSTM}")
    print(f"🌐 Frontend: {frontend_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행되는 이벤트"""
    print("👋 서버 종료")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
