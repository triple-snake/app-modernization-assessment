from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .database import Base


class System(Base):
    """
    Systems 테이블: 12개 모더나이제이션 대상 시스템 정보
    """
    __tablename__ = "systems"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="시스템명")
    description = Column(Text, nullable=True, comment="시스템 설명")
    project_id = Column(Integer, nullable=True, comment="프로젝트 ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일시")

    def __repr__(self):
        return f"<System(id={self.id}, name='{self.name}')>"
