from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from .database import Base


class ModelRetrainingLog(Base):
    """
    MODEL_RETRAINING_LOG 테이블: LSTM 모델 재학습 이력 기록
    """
    __tablename__ = "model_retraining_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 트리거 정보
    trigger_reason = Column(String(200), nullable=False, comment="재학습 트리거 이유 (e.g., RMSD_THRESHOLD_EXCEEDED)")
    trigger_rmsd = Column(Integer, nullable=True, comment="트리거가 된 RMSD 값")
    related_evaluation_id = Column(Integer, ForeignKey("prediction_evaluations.id"), nullable=True, comment="관련 평가 ID")
    
    # 재학습 프로세스
    retraining_started_at = Column(DateTime(timezone=True), nullable=False, comment="재학습 시작 시간")
    retraining_completed_at = Column(DateTime(timezone=True), nullable=True, comment="재학습 완료 시간")
    retraining_status = Column(String(50), default="pending", comment="상태 (pending, running, completed, failed)")
    
    # 모델 정보
    previous_model_version = Column(String(20), nullable=False, comment="이전 모델 버전")
    new_model_version = Column(String(20), nullable=True, comment="새로운 모델 버전")
    
    # 학습 데이터
    training_data_count = Column(Integer, nullable=True, comment="학습 데이터 개수")
    training_duration_seconds = Column(Integer, nullable=True, comment="학습 소요 시간(초)")
    
    # 결과
    is_successful = Column(Boolean, default=False, comment="성공 여부")
    performance_improvement = Column(Integer, nullable=True, comment="성능 개선도 (%)")
    notes = Column(Text, nullable=True, comment="재학습 노트")
    
    # 메타
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="기록일시")

    def __repr__(self):
        return f"<ModelRetrainingLog(reason={self.trigger_reason}, status={self.retraining_status})>"
