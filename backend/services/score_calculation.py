from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.score import Score
from models.system import System


class ScoreCalculationEngine:
    """
    적합도 연산 엔진
    2.1 ~ 2.4 지표 계산 및 그룹 판별
    """
    
    # 그룹별 색상 매핑
    GROUP_COLORS = {
        1: "red",      # 가장 높은 우선순위
        2: "orange",   # 높은 우선순위
        3: "yellow",   # 중간 우선순위
        4: "green"     # 낮은 우선순위
    }
    
    @staticmethod
    def calculate_ops_score(
        log_completeness: float,    # 로그 완전성 (0~1)
        log_accessibility: float,   # 로그 접근성 (0~1)
        monitoring_coverage: float  # 모니터링 커버리지 (0~1)
    ) -> float:
        """
        2.1 Ops 적합도 계산 (O)
        
        Args:
            log_completeness: 로그 완전성
            log_accessibility: 로그 접근성
            monitoring_coverage: 모니터링 커버리지
        
        Returns:
            Ops 적합도 점수 (0~100)
        """
        # 가중 평균 계산
        score = (
            log_completeness * 0.4 +
            log_accessibility * 0.3 +
            monitoring_coverage * 0.3
        ) * 100
        
        return round(score, 2)
    
    @staticmethod
    def calculate_sec_score(
        vulnerability_count: int,      # 취약점 개수
        authentication_level: float,   # 인증 수준 (0~1)
        encryption_coverage: float     # 암호화 커버리지 (0~1)
    ) -> float:
        """
        2.2 Sec 적합도 계산 (S)
        
        Args:
            vulnerability_count: 스캔된 취약점 개수
            authentication_level: 인증 수준
            encryption_coverage: 암호화 커버리지
        
        Returns:
            Sec 적합도 점수 (0~100)
        """
        # 취약점은 역수로 계산 (적을수록 높은 점수)
        vulnerability_score = max(0, 1 - (vulnerability_count / 100))
        
        score = (
            vulnerability_score * 0.5 +
            authentication_level * 0.3 +
            encryption_coverage * 0.2
        ) * 100
        
        return round(score, 2)
    
    @staticmethod
    def calculate_biz_score(
        availability_rate: float,      # 가용률 (0~1)
        deployment_frequency: float,   # 배포 빈도 (정규화 0~1)
        no_downtime_deploy: bool       # 무중단 배포 여부
    ) -> float:
        """
        2.3 Biz 적합도 계산 (X)
        Biz 적시성 = (무중단 + 배포과정 간소화) / 2
        
        Args:
            availability_rate: 가용률
            deployment_frequency: 배포 빈도
            no_downtime_deploy: 무중단 배포 가능 여부
        
        Returns:
            Biz 적합도 점수 (0~100)
        """
        no_downtime_score = 1.0 if no_downtime_deploy else 0.0
        deployment_simplicity = deployment_frequency  # 빈도가 높으면 프로세스가 간단함을 의미
        
        timeliness = (no_downtime_score + deployment_simplicity) / 2
        
        score = (
            availability_rate * 0.5 +
            timeliness * 0.5
        ) * 100
        
        return round(score, 2)
    
    @staticmethod
    def calculate_total_score(ops: float, sec: float, biz: float) -> float:
        """
        2.4 Total 적합도 계산
        
        Args:
            ops: Ops 점수
            sec: Sec 점수
            biz: Biz 점수
        
        Returns:
            Total 적합도 점수 (0~100)
        """
        # 가중치: 각 영역을 동등하게 평가
        total = (ops + sec + biz) / 3
        return round(total, 2)
    
    @staticmethod
    def assign_ranks(scores: List[Dict[str, Any]], score_key: str) -> List[Dict[str, Any]]:
        """
        점수 기반 등수 부여
        
        Args:
            scores: 점수 데이터 리스트
            score_key: 정렬 기준 점수 키
        
        Returns:
            등수가 부여된 데이터 리스트
        """
        # 점수 기준 내림차순 정렬
        sorted_scores = sorted(scores, key=lambda x: x[score_key], reverse=True)
        
        # 등수 부여
        for rank, item in enumerate(sorted_scores, start=1):
            item[f"{score_key.replace('_score', '_rank')}"] = rank
        
        return scores
    
    @staticmethod
    def assign_groups(scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Total 등수 기반 4개 그룹 분할
        
        Args:
            scores: 등수가 부여된 데이터 리스트
        
        Returns:
            그룹 정보가 추가된 데이터 리스트
        """
        total_systems = len(scores)
        group_size = total_systems // 4
        remainder = total_systems % 4
        
        # 등수 기준 정렬
        sorted_scores = sorted(scores, key=lambda x: x['total_rank'])
        
        # 그룹 할당
        current_idx = 0
        for group_num in range(1, 5):
            # 나머지를 앞쪽 그룹에 분배
            current_group_size = group_size + (1 if group_num <= remainder else 0)
            
            for i in range(current_group_size):
                if current_idx < total_systems:
                    sorted_scores[current_idx]['group_number'] = group_num
                    sorted_scores[current_idx]['group_color'] = ScoreCalculationEngine.GROUP_COLORS[group_num]
                    current_idx += 1
        
        return scores
    
    @classmethod
    def calculate_all_scores(cls, db: Session) -> List[Dict[str, Any]]:
        """
        모든 시스템의 적합도 계산 및 DB 저장
        
        Args:
            db: 데이터베이스 세션
        
        Returns:
            계산된 점수 리스트
        """
        # 모든 시스템 조회
        systems = db.query(System).all()
        
        if not systems:
            return []
        
        results = []
        
        for system in systems:
            # TODO: 실제 데이터는 로그, 스캔, 입력 데이터에서 가져와야 함
            # 현재는 Mock 데이터 사용
            ops_score = cls.calculate_ops_score(
                log_completeness=0.8,
                log_accessibility=0.7,
                monitoring_coverage=0.6
            )
            
            sec_score = cls.calculate_sec_score(
                vulnerability_count=5,
                authentication_level=0.8,
                encryption_coverage=0.7
            )
            
            biz_score = cls.calculate_biz_score(
                availability_rate=0.99,
                deployment_frequency=0.8,
                no_downtime_deploy=True
            )
            
            total_score = cls.calculate_total_score(ops_score, sec_score, biz_score)
            
            results.append({
                'system_id': system.id,
                'system_name': system.name,
                'ops_score': ops_score,
                'sec_score': sec_score,
                'biz_score': biz_score,
                'total_score': total_score
            })
        
        # 각 카테고리별 등수 부여
        results = cls.assign_ranks(results, 'ops_score')
        results = cls.assign_ranks(results, 'sec_score')
        results = cls.assign_ranks(results, 'biz_score')
        results = cls.assign_ranks(results, 'total_score')
        
        # 그룹 할당
        results = cls.assign_groups(results)
        
        # DB에 저장
        for result in results:
            score = db.query(Score).filter(Score.system_id == result['system_id']).first()
            
            if score:
                # 업데이트
                score.ops_score = result['ops_score']
                score.ops_rank = result['ops_rank']
                score.sec_score = result['sec_score']
                score.sec_rank = result['sec_rank']
                score.biz_score = result['biz_score']
                score.biz_rank = result['biz_rank']
                score.total_score = result['total_score']
                score.total_rank = result['total_rank']
                score.group_number = result['group_number']
                score.group_color = result['group_color']
            else:
                # 새로 생성
                score = Score(
                    system_id=result['system_id'],
                    ops_score=result['ops_score'],
                    ops_rank=result['ops_rank'],
                    sec_score=result['sec_score'],
                    sec_rank=result['sec_rank'],
                    biz_score=result['biz_score'],
                    biz_rank=result['biz_rank'],
                    total_score=result['total_score'],
                    total_rank=result['total_rank'],
                    group_number=result['group_number'],
                    group_color=result['group_color']
                )
                db.add(score)
        
        db.commit()
        
        return results


calculation_engine = ScoreCalculationEngine()
