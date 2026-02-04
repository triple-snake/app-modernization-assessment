# App Modernization Assessment - Backend

FastAPI 기반 웹 서버 및 적합도 연산 엔진

## 프로젝트 구조

```
backend/
├── main.py                 # FastAPI 메인 서버
├── config/                 # 설정 파일
│   ├── settings.py        # 환경 설정
│   └── qdrant.py          # Qdrant 연동
├── models/                 # 데이터베이스 모델
│   ├── database.py        # DB 연결 및 세션
│   ├── system.py          # Systems 테이블
│   └── score.py           # Scores 테이블
├── routers/                # API 라우터
│   └── api.py             # API 엔드포인트
├── services/               # 비즈니스 로직
│   └── score_calculation.py  # 적합도 연산 엔진
├── requirements.txt        # Python 의존성
├── .env.example           # 환경 변수 예시
└── .gitignore             # Git 제외 파일
```

## 기능

### 1. 적합도 연산 엔진
- **2.1 Ops 적합도 (O)**: 로그 완전성, 접근성, 모니터링 커버리지 기반 계산
- **2.2 Sec 적합도 (S)**: 취약점 수, 인증 수준, 암호화 커버리지 기반 계산
- **2.3 Biz 적합도 (X)**: 가용률, 배포 빈도, 무중단 배포 기반 계산 (Biz 적시성 공식 적용)
- **2.4 Total 적합도**: Ops, Sec, Biz 평균
- **그룹 판별**: 12개 시스템을 Total 등수 기반으로 4개 그룹(색상)으로 분류

### 2. API 엔드포인트

#### 헬스 체크
```
GET /api/health
```

#### 시스템 관리
```
GET /api/systems              # 전체 시스템 목록 조회
POST /api/systems/init        # 12개 시스템 초기 데이터 생성
```

#### 점수 계산 및 조회
```
POST /api/scores/calculate    # 적합도 계산 및 DB 저장
GET /api/scores               # 전체 시스템 점수 조회
GET /api/scores?system_id=1   # 특정 시스템 점수 조회
GET /api/scores/{system_id}/rationale  # 측정 근거 조회 (RAG)
```

#### 정적 파일
```
GET /                         # 프론트엔드 (index.html)
```

## 설치 및 실행

### 1. 의존성 설치
```bash
cd backend
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 데이터베이스 정보 입력
```

### 3. MariaDB 데이터베이스 생성
```sql
CREATE DATABASE modernization_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 서버 실행
```bash
# 개발 모드 (자동 리로드)
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. API 테스트

서버 실행 후 다음 순서로 테스트:

1. **헬스 체크**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **시스템 초기화** (12개 시스템 생성)
   ```bash
   curl -X POST http://localhost:8000/api/systems/init
   ```

3. **적합도 계산**
   ```bash
   curl -X POST http://localhost:8000/api/scores/calculate
   ```

4. **점수 조회**
   ```bash
   curl http://localhost:8000/api/scores
   ```

5. **프론트엔드 접속**
   ```
   http://localhost:8000/
   ```

## 데이터베이스 스키마

### Systems 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | PK, 자동 증가 |
| name | VARCHAR(100) | 시스템명 (유니크) |
| description | TEXT | 시스템 설명 |
| project_id | INTEGER | 프로젝트 ID |
| created_at | DATETIME | 생성일시 |
| updated_at | DATETIME | 수정일시 |

### Scores 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | PK, 자동 증가 |
| system_id | INTEGER | FK → systems.id |
| ops_score | FLOAT | Ops 점수 |
| ops_rank | INTEGER | Ops 등수 |
| sec_score | FLOAT | Sec 점수 |
| sec_rank | INTEGER | Sec 등수 |
| biz_score | FLOAT | Biz 점수 |
| biz_rank | INTEGER | Biz 등수 |
| total_score | FLOAT | Total 점수 |
| total_rank | INTEGER | Total 등수 |
| group_number | INTEGER | 그룹 번호 (1~4) |
| group_color | VARCHAR(20) | 그룹 색상 |
| measurement_rationale | TEXT | 측정 근거 |
| created_at | DATETIME | 생성일시 |
| updated_at | DATETIME | 수정일시 |

## 환경 변수

`.env` 파일 예시:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=modernization_db

QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=modernization_rationale

DEBUG=True
```

## 아키텍처

```
[Frontend] → [FastAPI Server] → [Calculation Engine] → [MariaDB]
                  ↓
              [Qdrant]
                (RAG)
```

- **프론트엔드**: 서버 API만 호출 (DB 직접 접근 금지)
- **서버**: 연산 수행 후 결과를 DB에 저장
- **DB**: 연산 결과 및 시스템 정보 저장
- **Qdrant**: 생성형 AI 기반 측정 근거 저장/조회

## 완료 기준 (Definition of Done)

- [x] 서버 실행 후 `/` 접속 시 로그인 화면 렌더링
- [x] `/api/scores` 호출 시 12개 시스템의 점수와 그룹 정보 반환
- [x] 적합도 평가 결과가 MariaDB 테이블에 정상 기록/업데이트
- [x] 2.1~2.4 지표 연산 로직 구현
- [x] 그룹 판별 로직 구현 (4개 그룹)
- [x] Qdrant 연동 준비 완료

## 개발자 노트

### Mock 데이터
현재 `score_calculation.py`의 `calculate_all_scores()` 메서드는 Mock 데이터를 사용합니다.
실제 운영 시에는 다음 데이터 소스에서 값을 가져와야 합니다:
- **로그 데이터 (O)**: 로그 수집 시스템
- **스캔 데이터 (S)**: 보안 취약점 스캐너
- **입력 데이터 (X)**: 사용자 입력 또는 모니터링 시스템

### TODO
- [ ] 실제 로그/스캔/입력 데이터 연동
- [ ] Qdrant 벡터 검색 구현
- [ ] 생성형 AI 기반 측정 근거 생성
- [ ] 사용자 인증 및 권한 관리
- [ ] 프로젝트 다중화 지원
