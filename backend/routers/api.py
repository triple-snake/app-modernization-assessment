from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import get_db, System, Score
from services import calculation_engine
from config import qdrant_service

router = APIRouter(prefix="/api", tags=["API"])


@router.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트
    """
    return {"status": "ok", "message": "Server is running"}


@router.get("/systems")
async def get_systems(db: Session = Depends(get_db)):
    """
    모든 시스템 목록 조회
    """
    systems = db.query(System).all()
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


@router.post("/scores/calculate")
async def calculate_scores(db: Session = Depends(get_db)):
    """
    모든 시스템의 적합도 계산 및 DB 저장
    
    서버에서 연산을 수행하고 결과를 DB에 저장합니다.
    """
    try:
        results = calculation_engine.calculate_all_scores(db)
        return {
            "status": "success",
            "message": "적합도 계산 완료",
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"계산 오류: {str(e)}")


@router.get("/scores")
async def get_scores(
    system_id: int = None,
    db: Session = Depends(get_db)
):
    """
    적합도 평가 결과 조회
    
    Args:
        system_id: 특정 시스템 ID (옵션). 없으면 전체 조회
    """
    try:
        if system_id:
            # 특정 시스템 조회
            score = db.query(Score).filter(Score.system_id == system_id).first()
            if not score:
                raise HTTPException(status_code=404, detail="점수 정보를 찾을 수 없습니다")
            
            system = db.query(System).filter(System.id == system_id).first()
            
            return {
                "system_id": score.system_id,
                "system_name": system.name if system else "Unknown",
                "ops": {
                    "score": score.ops_score,
                    "rank": score.ops_rank
                },
                "sec": {
                    "score": score.sec_score,
                    "rank": score.sec_rank
                },
                "biz": {
                    "score": score.biz_score,
                    "rank": score.biz_rank
                },
                "total": {
                    "score": score.total_score,
                    "rank": score.total_rank
                },
                "group": {
                    "number": score.group_number,
                    "color": score.group_color
                },
                "measurement_rationale": score.measurement_rationale
            }
        else:
            # 전체 조회
            scores = db.query(Score).join(System).all()
            
            results = []
            for score in scores:
                system = db.query(System).filter(System.id == score.system_id).first()
                results.append({
                    "system_id": score.system_id,
                    "system_name": system.name if system else "Unknown",
                    "ops": {
                        "score": score.ops_score,
                        "rank": score.ops_rank
                    },
                    "sec": {
                        "score": score.sec_score,
                        "rank": score.sec_rank
                    },
                    "biz": {
                        "score": score.biz_score,
                        "rank": score.biz_rank
                    },
                    "total": {
                        "score": score.total_score,
                        "rank": score.total_rank
                    },
                    "group": {
                        "number": score.group_number,
                        "color": score.group_color
                    }
                })
            
            return {
                "count": len(results),
                "scores": results
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 오류: {str(e)}")


@router.get("/scores/{system_id}/rationale")
async def get_rationale(system_id: int, db: Session = Depends(get_db)):
    """
    특정 시스템의 측정 근거 조회 (RAG 기반)
    
    Args:
        system_id: 시스템 ID
    """
    try:
        # DB에 저장된 근거 조회
        score = db.query(Score).filter(Score.system_id == system_id).first()
        if not score:
            raise HTTPException(status_code=404, detail="점수 정보를 찾을 수 없습니다")
        
        # Qdrant에서 추가 근거 조회
        qdrant_rationale = await qdrant_service.get_rationale(system_id)
        
        return {
            "system_id": system_id,
            "db_rationale": score.measurement_rationale,
            "rag_rationale": qdrant_rationale
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조회 오류: {str(e)}")


@router.post("/systems/init")
async def init_systems(db: Session = Depends(get_db)):
    """
    12개 시스템 초기 데이터 생성 (개발용)
    """
    try:
        # 기존 데이터 확인
        existing = db.query(System).count()
        if existing > 0:
            return {"message": f"이미 {existing}개의 시스템이 존재합니다"}
        
        # 12개 시스템 생성
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
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"{len(system_names)}개 시스템 생성 완료"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"생성 오류: {str(e)}")
