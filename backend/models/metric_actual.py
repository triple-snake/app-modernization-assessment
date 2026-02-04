from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from .database import Base


class MetricActual(Base):
    """
    METRIC_ACTUAL 테이블: 실제 측정된 성능 지표
    """
    __tablename__ = "metric_actuals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    system_id = Column(Integer, ForeignKey("systems.id"), nullable=False, comment="시스템 ID")
    
    # 지표
    metric_name = Column(String(100), nullable=False, comment="지표명 (e.g., availability, response_time)")
    metric_value = Column(Float, nullable=False, comment="지표값")
    unit = Column(String(50), nullable=True, comment="단위 (%, ms, etc)")
    
    # 시계열
    measured_at = Column(DateTime(timezone=True), nullable=False, comment="측정 시간")
    source = Column(String(100), nullable=True, comment="데이터 소스 (monitoring, logs, etc)")
    
    # 메타
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="기록일시")

    def __repr__(self):
        return f"<MetricActual(system={self.system_id}, metric={self.metric_name}, value={self.metric_value})>"
