# Database Architecture (PoC)

## 📋 개요

Cloud Native 적합성 평가 시스템을 위한 데이터베이스 아키텍처

## 🗄️ 데이터베이스 선택 이유

### MariaDB
**선택 이유:**
- **관계형 데이터 저장**: 시스템, 사용자, 로그 등의 구조화된 데이터 관리
- **트랜잭션 지원**: 점수 계산 및 예측 결과의 일관성 보장
- **SQL 쿼리**: 복잡한 분석 쿼리 및 집계 작업에 유리
- **성숙도**: 안정적이고 검증된 오픈소스 RDBMS

**주요 용도:**
- 로그 데이터 저장 (RAW_LOG)
- 시스템 및 사용자 관리 (SYSTEM, USER)
- LLM 평가 결과 저장 (LLM_EVALUATION, METRIC_SCORE)
- 시계열 예측 및 실제값 저장 (TIMESERIES_PREDICTION, METRIC_ACTUAL)

### Qdrant (Vector Database)
**선택 이유:**
- **벡터 유사도 검색**: RAG(Retrieval-Augmented Generation)를 위한 문서 검색
- **고속 검색**: Cosine Similarity 기반 빠른 유사 문서 탐색
- **임베딩 저장**: LLM 임베딩 벡터의 효율적인 저장 및 검색
- **확장성**: 대량의 벡터 데이터 처리에 최적화

**주요 용도:**
- **Modernization_RAG**: LLM Grade 판정 시 참조할 평가 기준 문서 저장
- **System_Metrics_Grade**: 22개 지표의 Grade 벡터 저장 (LSTM 학습용)

---

## 📊 테이블 구조 (12개)

### Core Tables (5개)

#### 1. USER
**역할**: B2B 고객사 사용자 정보
```sql
- id: 사용자 고유 ID
- email: 이메일 (로그인)
- name: 사용자 이름
- created_at: 생성일시
```

#### 2. SYSTEM
**역할**: 평가 대상 시스템 정보
```sql
- id: 시스템 고유 ID
- user_id: 소유자 (USER FK)
- system_name: 시스템 이름
- owner_team: 담당 팀
- system_type: 시스템 유형 (Backend/Frontend)
- business_criticality: 비즈니스 중요도 (High/Medium/Low)
```

#### 3. INPUT_DATA
**역할**: 문서 기반 지표 12개 저장 (JSON)
```sql
- id: 데이터 ID
- system_id: 시스템 (SYSTEM FK)
- input_source: 데이터 소스 (DOCUMENT)
- extracted_fields: 12개 지표 key-value (JSON)
  예: {"EXPANSION_NEEDS": "1년 뒤 글로벌 확장", ...}
```

#### 4. RAW_LOG
**역할**: B2B API로 수신한 원본 로그
```sql
- id: 로그 고유 ID
- system_id: 시스템 ID (문자열)
- timestamp: 로그 발생 시간
- log_type: 로그 유형 (apm/web/alert/deploy/infra/network)
- level: 로그 레벨 (INFO/WARN/ERROR)
- message: 로그 메시지
```

#### 5. LOG_BATCH
**역할**: 24시간 로그 병합 (LLM 입력용)
```sql
- id: 배치 ID
- system_id: 시스템 (SYSTEM FK)
- start_time, end_time: 배치 시간 범위
- log_count: 로그 건수
- merged_log_text: 병합된 로그 텍스트 (LONGTEXT)
```

---

### LLM & Scoring Tables (4개)

#### 6. LLM_EVALUATION
**역할**: LLM이 판정한 22개 지표 Grade
```sql
- id: 평가 ID
- system_id: 시스템 (SYSTEM FK)
- log_batch_id: 로그 배치 (LOG_BATCH FK)
- metric_grades: 22개 지표 Grade 1~3 (JSON)
  예: {"TRAFFIC_VOLATILITY": 2, "REDUNDANCY_CONFIG": 1, ...}
- evaluation_reason: 평가 근거
- llm_model: 사용한 LLM 모델
```

#### 7. METRIC_SCORE
**역할**: Grade → 정규화 점수 변환
```sql
- id: 점수 ID
- system_id: 시스템 (SYSTEM FK)
- metric_code: 지표 코드 (예: TRAFFIC_VOLATILITY)
- grade: Grade 1/2/3
- score: 정규화 점수 (3-grade)/2
- weight: 가중치
```

#### 8. SYSTEM_SCORE
**역할**: 일별 종합 점수 (0~100)
```sql
- id: 점수 ID
- system_id: 시스템 (SYSTEM FK)
- value_score, ease_score: 세부 점수
- total_score: 종합 점수 (0~100)
- final_grade: 최종 등급 (A/B/C/D/F)
```

#### 9. LLM_SUMMARY
**역할**: LLM 생성 요약 및 권장사항
```sql
- id: 요약 ID
- system_id: 시스템 (SYSTEM FK)
- system_score_id: 점수 (SYSTEM_SCORE FK)
- summary_text: 요약 텍스트
- key_recommendation: 주요 권장사항
- risk_notes: 위험 요소
```

---

### Time Series & RMSD Tables (3개)

#### 10. TIMESERIES_PREDICTION
**역할**: LSTM 모델의 미래 예측값
```sql
- id: 예측 ID
- system_id: 시스템 (SYSTEM FK)
- metric_code: 지표 코드
- prediction_horizon: 예측 시점 (D+1)
- predicted_value: 예측값
- model_version: 모델 버전
```

#### 11. METRIC_ACTUAL
**역할**: 실제 관측값 (예측 검증용)
```sql
- id: 실측값 ID
- system_id: 시스템 (SYSTEM FK)
- metric_code: 지표 코드
- actual_time: 관측 시간
- actual_value: 실제값
```

#### 12. PREDICTION_EVALUATION
**역할**: RMSD 계산 및 재학습 트리거
```sql
- id: 평가 ID
- prediction_id: 예측 (TIMESERIES_PREDICTION FK)
- actual_id: 실측 (METRIC_ACTUAL FK)
- rmsd_value: RMSD 값
- is_threshold_exceeded: 임계치 초과 여부 (RMSD >= 10.0)
```

**RMSD 재학습 로직:**
```
IF is_threshold_exceeded = TRUE:
    1. 전체 로그 데이터 수집 (서비스 시작~현재)
    2. 전체 문서 데이터 수집 (INPUT_DATA)
    3. LSTM 모델 재학습
    4. 새 모델로 서빙
```

---

## 🔄 데이터 흐름

### 1. 로그 수집 (실시간)
```
B2B 고객사 → API → RAW_LOG 테이블
```

### 2. 일일 배치 (매일 자정)
```
RAW_LOG (24h) → LOG_BATCH
              ↓
    LLM 평가 (로그 + 문서)
              ↓
    LLM_EVALUATION (22개 Grade)
              ↓
    METRIC_SCORE (정규화)
              ↓
    SYSTEM_SCORE (종합 점수)
```

### 3. 시계열 예측 (매일 02:00)
```
METRIC_SCORE (30일 히스토리)
              ↓
    LSTM 모델 실행
              ↓
    TIMESERIES_PREDICTION (D+1)
```

### 4. RMSD 검증 (매일 03:00)
```
TIMESERIES_PREDICTION (어제 예측)
         +
METRIC_ACTUAL (오늘 실제)
              ↓
    PREDICTION_EVALUATION
              ↓
    IF RMSD >= 10.0 → 모델 재학습
```

---

## 🎯 Qdrant 컬렉션

### Collection 1: Modernization_RAG
**크기**: 1536차원 (OpenAI text-embedding-ada-002)  
**용도**: LLM Grade 판정 시 참조할 평가 기준 문서  
**예시 문서:**
```json
{
  "text": "트래픽 변동량이 시간당 300% 이상이면 Grade 3 (오토스케일링 필수)",
  "metadata": {"metric": "TRAFFIC_VOLATILITY", "grade": 3}
}
```

### Collection 2: System_Metrics_Grade
**크기**: 22차원 (22개 지표의 Grade 벡터)  
**용도**: LSTM 학습용 시계열 벡터 저장  
**예시 벡터:**
```json
{
  "id": "SYS-001-2026-02-04",
  "vector": [2, 1, 3, 2, ...],  // 22개 지표의 Grade
  "payload": {"system_id": "SYS-001", "date": "2026-02-04", "score": 73.5}
}
```

---

## 📈 22개 평가 지표

### 로그 기반 (10개)
1. TRAFFIC_VOLATILITY - 트래픽 변동량
2. REDUNDANCY_CONFIG - 이중화 구성
3. SESSION_MANAGEMENT - 세션 관리
4. EXTERNAL_INTEGRATION - 외부 연동
5. OS_DB_MIDDLEWARE - OS/DB/미들웨어
6. NON_STANDARD_PROTOCOL - 비표준 프로토콜
7. FAILURE_FREQUENCY - 장애 빈도
8. REQUIREMENT_FREQUENCY - 요구사항 빈도
9. DEPLOYMENT_TIME - 배포 시간
10. INSTANCE_BATCH_PROCESS - 인스턴스/배치 프로세스

### 문서 기반 (12개)
11. EXPANSION_NEEDS - 확장 필요성
12. TOTAL_BRANCHES - 전체 본 수
13. SYSTEM_DESCRIPTION - 시스템 설명
14. USER_INFO - 사용자 정보
15. OS_SOLUTION_DEPENDENCY - OS/솔루션 종속성
16. COMMERCIAL_LICENSE - 상용 라이선스
17. FRAMEWORK_VERSION - 프레임워크 버전
18. DEPENDENCY_TOOLS - 의존성 도구
19. CONFIG_LOG_FILESYSTEM - 설정/로그/파일시스템
20. SYSTEM_COMPLEXITY - 시스템 복잡도
21. FAILURE_SENSITIVITY - 장애 민감도
22. DEPLOYMENT_PROCEDURE - 배포 절차

---

## 🔧 Grade 기반 점수 계산

### Grade 체계
- **Grade 1**: 매우 적합 (클라우드 네이티브 준비 완료)
- **Grade 2**: 개선 필요 (일부 마이그레이션 작업 필요)
- **Grade 3**: 높은 위험 (대규모 리팩토링 필요)

### 정규화 공식
```
normalized_score = (3 - grade) / 2

Grade 1 → (3-1)/2 = 1.0
Grade 2 → (3-2)/2 = 0.5
Grade 3 → (3-3)/2 = 0.0
```

### 종합 점수
```
total_score = (Σ normalized_score × weight) / Σ weight × 100
```

---

## 🎯 PoC 범위

**포함:**
- ✅ MariaDB 12개 테이블
- ✅ Qdrant 2개 컬렉션
- ✅ Excel 데이터 로드 (6000개 로그)
- ✅ 기본 스키마 및 인덱스

**제외 (향후 구현):**
- ❌ LLM 평가 자동화
- ❌ LSTM 모델 학습
- ❌ 대시보드 UI
- ❌ 성능 최적화 (파티셔닝, 샤딩)
