from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from .database import Base


class UserRole(str, enum.Enum):
    """사용자 역할"""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(Base):
    """
    USER 테이블: 시스템 사용자 정보
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True, comment="사용자명")
    email = Column(String(100), nullable=False, unique=True, comment="이메일")
    password_hash = Column(String(255), nullable=False, comment="해시된 비밀번호")
    full_name = Column(String(100), nullable=True, comment="이름")
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, comment="역할")
    is_active = Column(Boolean, default=True, comment="활성화 여부")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일시")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
