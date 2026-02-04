from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.sql import func
from .database import Base


class PredictionEvaluation(Base):
    """
    PREDICTION_EVALUATION 테이블: LSTM 모델 예측값 평가 기록
    """
    __tablename__ = "prediction_evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    system_id = Column(Integer, ForeignKey("systems.id"), nullable=False, comment="시스템 ID")
    model_version = Column(String(20), nullable=False, comment="모델 버전")
    
    # 평가 지표
    rmsd = Column(Float, nullable=False, comment="RMSD (오차율)")
    mae = Column(Float, nullable=True, comment="MAE (평균 절대 오차)")
    mape = Column(Float, nullable=True, comment="MAPE (평균 백분율 오차)")
    
    # 데이터 범위
    evaluation_start_date = Column(DateTime(timezone=True), nullable=False, comment="평가 시작일")
    evaluation_end_date = Column(DateTime(timezone=True), nullable=False, comment="평가 종료일")
    sample_count = Column(Integer, nullable=True, comment="평가 샘플 수")
    
    # 평가 결과
    is_within_threshold = Column(Boolean, default=True, comment="임계값 이내 여부 (5%)")
    threshold_exceeded = Column(Boolean, default=False, comment="임계값 초과 여부")
    
    # 메타 정보
    evaluation_notes = Column(Text, nullable=True, comment="평가 노트")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="평가일시")

    def __repr__(self):
        return f"<PredictionEvaluation(system={self.system_id}, rmsd={self.rmsd})>"
