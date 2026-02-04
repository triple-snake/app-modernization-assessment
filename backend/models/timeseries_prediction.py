from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from .database import Base


class TimeseriesPrediction(Base):
    """
    TIMESERIES_PREDICTION 테이블: LSTM 모델의 시계열 예측값
    """
    __tablename__ = "timeseries_predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    system_id = Column(Integer, ForeignKey("systems.id"), nullable=False, comment="시스템 ID")
    model_version = Column(String(20), nullable=False, comment="모델 버전")
    
    # 예측 값
    metric_name = Column(String(100), nullable=False, comment="지표명")
    predicted_value = Column(Float, nullable=False, comment="예측값")
    predicted_at = Column(DateTime(timezone=True), nullable=False, comment="예측 시간")
    
    # 신뢰도
    confidence_interval_lower = Column(Float, nullable=True, comment="신뢰구간 하한")
    confidence_interval_upper = Column(Float, nullable=True, comment="신뢰구간 상한")
    confidence_score = Column(Float, nullable=True, comment="신뢰도 점수 (0~1)")
    
    # 메타
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="기록일시")

    def __repr__(self):
        return f"<TimeseriesPrediction(system={self.system_id}, predicted={self.predicted_value})>"
