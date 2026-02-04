from pydantic_settings import BaseSettings
from typing import Optional
from datetime import timedelta


class Settings(BaseSettings):
    """
    애플리케이션 설정
    환경변수로부터 값을 읽어옴
    """
    # 애플리케이션 설정
    APP_NAME: str = "App Modernization Assessment"
    DEBUG: bool = True
    VERSION: str = "2.0.0"
    
    # MariaDB 설정
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "modernization_db"
    
    # Qdrant 설정
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_MODERNIZATION_RAG: str = "modernization_rag"
    QDRANT_SYSTEM_METRICS_LSTM: str = "system_metrics_lstm"
    QDRANT_COLLECTION: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    
    # JWT 설정
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS 설정
    ALLOWED_ORIGINS: list = ["http://localhost:8000", "http://127.0.0.1:8000"]
    
    @property
    def DATABASE_URL(self) -> str:
        """동기 MariaDB 연결 URL 생성"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """비동기 MariaDB 연결 URL 생성"""
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
