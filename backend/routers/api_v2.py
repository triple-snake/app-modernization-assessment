from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from models import get_async_db, System, Score, TimeseriesPrediction
from services import calculation_engine, rmsd_calculator
from config import qdrant_service
from utils.dependencies import get_current_user
from utils.jwt_handler import TokenData
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["API"])


# ==================== Pydantic 모델 ====================

class SystemScoreResponse(BaseModel):
    system_id: int
    system_name: str
    ops_score: float
    ops_rank: int
    sec_score: float
    sec_rank: int
    biz_score: float
    biz_rank: int
    total_score: float
    total_rank: int
    group_number: int
    group_color: str
    lstm_trend: Optional[List[dict]] = None
    rag_insights: Optional[List[dict]] = None


class ScoresResponse(BaseModel):
    count: int
    scores: List[SystemScoreResponse]


class ProjectSelectionRequest(BaseModel):
    project_id: int
    project_name: str


# ==================== 헬스 체크 ====================

@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok", "version": "2.0.0"}


# ==================== 점수 조회 (통합) ====================

@router.get("/scores", response_model=ScoresResponse)
async def get_scores(
    system_id: Optional[int] = Query(None),
    include_lstm: bool = Query(True),
    include_rag: bool = Query(True),
    db: AsyncSession = Depends(get_async_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    적합도 평가 결과 조회 (MariaDB + LSTM + RAG 통합)
    
    Args:
        system_id: 특정 시스템 ID (옵션)
        include_lstm: LSTM 예측 추세 포함 여부
        include_rag: RAG 인사이트 포함 여부
    """
    try:
        if system_id:
            # 특정 시스템 조회
            score = await db.get(Score, system_id)
            if not score:
                raise HTTPException(status_code=404, detail="점수 정보를 찾을 수 없습니다")
            
            system = await db.get(System, system_id)
            
            # LSTM 데이터 병합
            lstm_trend = None
            if include_lstm:
                lstm_trend = await qdrant_service.get_lstm_predictions(system_id, limit=7)
            
            # RAG 데이터 병합
            rag_insights = None
            if include_rag:
                rag_insights = await qdrant_service.get_rag_rationale(system_id)
            
            response_item = SystemScoreResponse(
                system_id=score.system_id,
                system_name=system.name if system else "Unknown",
                ops_score=score.ops_score,
                ops_rank=score.ops_rank,
                sec_score=score.sec_score,
                sec_rank=score.sec_rank,
                biz_score=score.biz_score,
                biz_rank=score.biz_rank,
                total_score=score.total_score,
                total_rank=score.total_rank,
                group_number=score.group_number,
                group_color=score.group_color,
                lstm_trend=lstm_trend,
                rag_insights=rag_insights
            )
            
            return ScoresResponse(count=1, scores=[response_item])
        else:
            # 전체 조회
            result = await db.execute(select(Score))
            scores = result.scalars().all()
            
            results = []
            for score in scores:
                system = await db.get(System, score.system_id)
                
                # LSTM 데이터 병합
                lstm_trend = None
                if include_lstm:
                    lstm_trend = await qdrant_service.get_lstm_predictions(score.system_id, limit=7)
                
                # RAG 데이터 병합
                rag_insights = None
                if include_rag:
                    rag_insights = await qdrant_service.get_rag_rationale(score.system_id)
                
                results.append(SystemScoreResponse(
                    system_id=score.system_id,
                    system_name=system.name if system else "Unknown",
                    ops_score=score.ops_score,
                    ops_rank=score.ops_rank,
                    sec_score=score.sec_score,
                    sec_rank=score.sec_rank,
                    biz_score=score.biz_score,
                    biz_rank=score.biz_rank,
                    total_score=score.total_score,
                    total_rank=score.total_rank,
                    group_number=score.group_number,
                    group_color=score.group_color,
                    lstm_trend=lstm_trend,
                    rag_insights=rag_insights
                ))
            
            return ScoresResponse(count=len(results), scores=results)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 오류: {str(e)}")


# ==================== RMSD 평가 ====================

@router.post("/evaluations/rmsd/{system_id}")
async def evaluate_rmsd(
    system_id: int,
    metric_name: str = Query("availability"),
    model_version: str = Query("1.0.0"),
    db: AsyncSession = Depends(get_async_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    RMSD 기반 예측값 평가 수행
    """
    try:
        # 지난 1개월 데이터 기반 평가
        end_date = datetime.utcnow()
        start_date = end_date.replace(day=1)
        
        # RMSD 계산
        evaluation_data = await rmsd_calculator.evaluate_predictions(
            db=db,
            system_id=system_id,
            metric_name=metric_name,
            model_version=model_version,
            start_date=start_date,
            end_date=end_date
        )
        
        # DB에 저장
        evaluation = await rmsd_calculator.save_evaluation(
            db=db,
            evaluation_data=evaluation_data,
            start_date=start_date,
            end_date=end_date
        )
        
        # 임계값 초과 시 재학습 트리거
        if evaluation.threshold_exceeded:
            retraining_log = await rmsd_calculator.trigger_model_retraining(
                db=db,
                system_id=system_id,
                evaluation=evaluation,
                current_model_version=model_version
            )
            
            return {
                "status": "success",
                "evaluation": {
                    "id": evaluation.id,
                    "rmsd": evaluation.rmsd,
                    "mae": evaluation.mae,
                    "mape": evaluation.mape,
                    "sample_count": evaluation.sample_count,
                    "is_within_threshold": evaluation.is_within_threshold
                },
                "retraining_triggered": True,
                "retraining_log": {
                    "id": retraining_log.id,
                    "previous_version": retraining_log.previous_model_version,
                    "new_version": retraining_log.new_model_version,
                    "status": retraining_log.retraining_status
                }
            }
        else:
            return {
                "status": "success",
                "evaluation": {
                    "id": evaluation.id,
                    "rmsd": evaluation.rmsd,
                    "mae": evaluation.mae,
                    "mape": evaluation.mape,
                    "sample_count": evaluation.sample_count,
                    "is_within_threshold": evaluation.is_within_threshold
                },
                "retraining_triggered": False
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"평가 오류: {str(e)}")


# ==================== 프로젝트 선택 ====================

@router.post("/projects/select")
async def select_project(
    request: ProjectSelectionRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    사용자가 프로젝트 선택
    
    프로젝트 선택 후 대시보드로 이동
    """
    # TODO: 프로젝트 존재 여부 확인, 권한 확인 등
    
    return {
        "status": "success",
        "message": f"프로젝트 '{request.project_name}' 선택 완료",
        "project_id": request.project_id,
        "user_id": current_user.user_id,
        "redirect": f"/dashboard?project_id={request.project_id}"
    }


# ==================== 시스템 정보 ====================

@router.get("/systems")
async def get_systems(
    db: AsyncSession = Depends(get_async_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    모든 시스템 목록 조회
    """
    result = await db.execute(select(System))
    systems = result.scalars().all()
    
    return {
        "count": len(systems),
        "systems": [
            {
                "id": system.id,
                "name": system.name,
                "description": system.description,
                "project_id": system.project_id
            }
            for system in systems
        ]
    }


# ==================== 초기화 (개발용) ====================

@router.post("/systems/init")
async def init_systems(db: AsyncSession = Depends(get_async_db)):
    """
    12개 시스템 초기 데이터 생성
    """
    existing = await db.execute(select(System))
    if existing.scalar_one_or_none():
        return {"message": "이미 시스템이 존재합니다"}
    
    system_names = [
        "고객관리시스템", "재고관리시스템", "주문처리시스템",
        "결제시스템", "배송관리시스템", "회원관리시스템",
        "상품관리시스템", "통계분석시스템", "로그관리시스템",
        "모니터링시스템", "알림시스템", "백업시스템"
    ]
    
    for idx, name in enumerate(system_names, start=1):
        system = System(
            name=name,
            description=f"{name} 설명",
            project_id=1
        )
        db.add(system)
    
    await db.commit()
    
    return {"status": "success", "message": f"{len(system_names)}개 시스템 생성 완료"}


@router.post("/scores/calculate")
async def calculate_scores(
    db: AsyncSession = Depends(get_async_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    모든 시스템의 적합도 계산 및 저장
    """
    results = calculation_engine.calculate_all_scores(db)
    return {
        "status": "success",
        "message": "적합도 계산 완료",
        "count": len(results),
        "results": results
    }
