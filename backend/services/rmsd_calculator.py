import math
from typing import List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import MetricActual, TimeseriesPrediction, PredictionEvaluation, ModelRetrainingLog
from config.settings import settings


class RMSDCalculator:
    """
    RMSD(Root Mean Square Deviation) 계산 및 모델 재학습 트리거 엔진
    """
    
    THRESHOLD_PERCENT = 5.0  # 임계값: 5%
    
    @staticmethod
    def calculate_rmsd(actual_values: List[float], predicted_values: List[float]) -> float:
        """
        RMSD 계산
        공식: RMSD = sqrt((1/n) * sum((y_i - y_hat_i)^2))
        
        Args:
            actual_values: 실제값 리스트
            predicted_values: 예측값 리스트
        
        Returns:
            RMSD 값
        """
        if len(actual_values) != len(predicted_values) or len(actual_values) == 0:
            return 0.0
        
        sum_squared_errors = sum(
            (actual - predicted) ** 2
            for actual, predicted in zip(actual_values, predicted_values)
        )
        
        rmsd = math.sqrt(sum_squared_errors / len(actual_values))
        return round(rmsd, 4)
    
    @staticmethod
    def calculate_mae(actual_values: List[float], predicted_values: List[float]) -> float:
        """
        MAE(Mean Absolute Error) 계산
        공식: MAE = (1/n) * sum(|y_i - y_hat_i|)
        """
        if len(actual_values) != len(predicted_values) or len(actual_values) == 0:
            return 0.0
        
        sum_abs_errors = sum(
            abs(actual - predicted)
            for actual, predicted in zip(actual_values, predicted_values)
        )
        
        mae = sum_abs_errors / len(actual_values)
        return round(mae, 4)
    
    @staticmethod
    def calculate_mape(actual_values: List[float], predicted_values: List[float]) -> float:
        """
        MAPE(Mean Absolute Percentage Error) 계산
        공식: MAPE = (1/n) * sum(|y_i - y_hat_i| / |y_i|) * 100
        """
        if len(actual_values) != len(predicted_values) or len(actual_values) == 0:
            return 0.0
        
        sum_percentage_errors = 0
        valid_count = 0
        
        for actual, predicted in zip(actual_values, predicted_values):
            if actual != 0:  # 0으로 나누기 방지
                sum_percentage_errors += abs((actual - predicted) / actual)
                valid_count += 1
        
        if valid_count == 0:
            return 0.0
        
        mape = (sum_percentage_errors / valid_count) * 100
        return round(mape, 4)
    
    @staticmethod
    def check_threshold(rmsd: float, actual_mean: float) -> Tuple[bool, float]:
        """
        임계값 확인
        
        Args:
            rmsd: RMSD 값
            actual_mean: 실제값의 평균
        
        Returns:
            (임계값 이내 여부, 오차율(%))
        """
        if actual_mean == 0:
            return False, 0.0
        
        error_percent = (rmsd / actual_mean) * 100
        is_within_threshold = error_percent <= RMSDCalculator.THRESHOLD_PERCENT
        
        return is_within_threshold, round(error_percent, 2)
    
    @classmethod
    async def evaluate_predictions(
        cls,
        db: AsyncSession,
        system_id: int,
        metric_name: str,
        model_version: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        예측값 평가 수행
        
        Args:
            db: AsyncSession
            system_id: 시스템 ID
            metric_name: 지표명
            model_version: 모델 버전
            start_date: 평가 시작일
            end_date: 평가 종료일
        
        Returns:
            평가 결과 딕셔너리
        """
        # 실제값 조회
        actual_result = await db.execute(
            select(MetricActual).filter(
                MetricActual.system_id == system_id,
                MetricActual.metric_name == metric_name,
                MetricActual.measured_at.between(start_date, end_date)
            ).order_by(MetricActual.measured_at)
        )
        actual_records = actual_result.scalars().all()
        actual_values = [record.metric_value for record in actual_records]
        
        # 예측값 조회
        pred_result = await db.execute(
            select(TimeseriesPrediction).filter(
                TimeseriesPrediction.system_id == system_id,
                TimeseriesPrediction.metric_name == metric_name,
                TimeseriesPrediction.model_version == model_version,
                TimeseriesPrediction.predicted_at.between(start_date, end_date)
            ).order_by(TimeseriesPrediction.predicted_at)
        )
        pred_records = pred_result.scalars().all()
        predicted_values = [record.predicted_value for record in pred_records]
        
        # 길이 맞추기
        min_len = min(len(actual_values), len(predicted_values))
        actual_values = actual_values[:min_len]
        predicted_values = predicted_values[:min_len]
        
        if min_len == 0:
            return {
                "system_id": system_id,
                "metric_name": metric_name,
                "model_version": model_version,
                "rmsd": 0.0,
                "mae": 0.0,
                "mape": 0.0,
                "sample_count": 0,
                "is_within_threshold": True,
                "threshold_exceeded": False,
                "error_percent": 0.0
            }
        
        # 지표 계산
        rmsd = cls.calculate_rmsd(actual_values, predicted_values)
        mae = cls.calculate_mae(actual_values, predicted_values)
        mape = cls.calculate_mape(actual_values, predicted_values)
        
        # 평균 계산
        actual_mean = sum(actual_values) / len(actual_values) if actual_values else 0
        
        # 임계값 확인
        is_within_threshold, error_percent = cls.check_threshold(rmsd, actual_mean)
        threshold_exceeded = not is_within_threshold
        
        return {
            "system_id": system_id,
            "metric_name": metric_name,
            "model_version": model_version,
            "rmsd": rmsd,
            "mae": mae,
            "mape": mape,
            "sample_count": min_len,
            "is_within_threshold": is_within_threshold,
            "threshold_exceeded": threshold_exceeded,
            "error_percent": error_percent
        }
    
    @classmethod
    async def save_evaluation(
        cls,
        db: AsyncSession,
        evaluation_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> PredictionEvaluation:
        """
        평가 결과 DB에 저장
        """
        evaluation = PredictionEvaluation(
            system_id=evaluation_data["system_id"],
            model_version=evaluation_data["model_version"],
            rmsd=evaluation_data["rmsd"],
            mae=evaluation_data["mae"],
            mape=evaluation_data["mape"],
            evaluation_start_date=start_date,
            evaluation_end_date=end_date,
            sample_count=evaluation_data["sample_count"],
            is_within_threshold=evaluation_data["is_within_threshold"],
            threshold_exceeded=evaluation_data["threshold_exceeded"]
        )
        
        db.add(evaluation)
        await db.flush()
        await db.commit()
        
        return evaluation
    
    @classmethod
    async def trigger_model_retraining(
        cls,
        db: AsyncSession,
        system_id: int,
        evaluation: PredictionEvaluation,
        current_model_version: str
    ) -> ModelRetrainingLog:
        """
        모델 재학습 트리거
        
        Args:
            db: AsyncSession
            system_id: 시스템 ID
            evaluation: 평가 결과
            current_model_version: 현재 모델 버전
        
        Returns:
            생성된 ModelRetrainingLog
        """
        # 새 모델 버전 생성 (semantic versioning)
        version_parts = current_model_version.split('.')
        minor = int(version_parts[-1])
        new_version = f"{version_parts[0]}.{version_parts[1]}.{minor + 1}"
        
        retraining_log = ModelRetrainingLog(
            trigger_reason="RMSD_THRESHOLD_EXCEEDED",
            trigger_rmsd=int(evaluation.rmsd),
            related_evaluation_id=evaluation.id,
            retraining_started_at=datetime.utcnow(),
            retraining_status="pending",
            previous_model_version=current_model_version,
            new_model_version=new_version
        )
        
        db.add(retraining_log)
        await db.flush()
        await db.commit()
        
        return retraining_log


rmsd_calculator = RMSDCalculator()
