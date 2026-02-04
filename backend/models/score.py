from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Score(Base):
    """
    Score 테이블: 시스템별 적합도 평가 결과 저장
    """
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    system_id = Column(Integer, ForeignKey("systems.id"), nullable=False, comment="시스템 ID")
    
    # 2.1 Ops 적합도 (O)
    ops_score = Column(Float, default=0.0, comment="Ops 적합도 점수")
    ops_rank = Column(Integer, nullable=True, comment="Ops 등수")
    
    # 2.2 Sec 적합도 (S)
    sec_score = Column(Float, default=0.0, comment="Sec 적합도 점수")
    sec_rank = Column(Integer, nullable=True, comment="Sec 등수")
    
    # 2.3 Biz 적합도 (X)
    biz_score = Column(Float, default=0.0, comment="Biz 적합도 점수")
    biz_rank = Column(Integer, nullable=True, comment="Biz 등수")
    
    # 2.4 Total 적합도
    total_score = Column(Float, default=0.0, comment="Total 적합도 점수")
    total_rank = Column(Integer, nullable=True, comment="Total 등수")
    
    # 그룹 판별 (1~4, 색상 매핑용)
    group_number = Column(Integer, nullable=True, comment="그룹 번호 (1~4)")
    group_color = Column(String(20), nullable=True, comment="그룹 색상")
    
    # 측정 근거 (RAG 기반 생성형 AI 결과)
    measurement_rationale = Column(Text, nullable=True, comment="측정 근거 (줄글)")
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="수정일시")

    def __repr__(self):
        return f"<Score(system_id={self.system_id}, total={self.total_score}, group={self.group_number})>"
