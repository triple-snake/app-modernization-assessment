# 테스트 시나리오 실행 가이드

이슈 3의 모든 Task를 검증하는 통합 테스트 시나리오입니다.

## 📋 사전 요구사항

### 1. MariaDB 실행
```bash
# Ubuntu/Debian
sudo systemctl start mariadb

# macOS
brew services start mariadb

# Docker
docker run -d -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=password \
  -e MYSQL_DATABASE=modernization_db \
  mariadb:latest
```

### 2. Qdrant 실행 (옵션하지만 권장)
```bash
# Docker
docker run -d -p 6333:6333 \
  -e QDRANT_API_KEY=your-api-key \
  qdrant/qdrant:latest
```

### 3. FastAPI 서버 실행
```bash
cd backend

# 의존성 설치 (필요시)
pip install -r requirements.txt

# 서버 시작
python main.py

# 또는
uvicorn main:app --reload --port 8000
```

서버가 http://localhost:8000에서 실행 중인지 확인하세요.

## 🧪 테스트 실행

### 방법 1: Python 스크립트 (권장)

가장 상세한 테스트 결과를 제공합니다.

```bash
cd backend

# 필수 패키지 설치
pip install requests

# 테스트 실행
python test_scenario.py
```

### 방법 2: Bash 스크립트

리눅스/macOS에서 사용 가능합니다.

```bash
cd backend

# 실행 권한 부여
chmod +x test_scenario.sh

# 테스트 실행
./test_scenario.sh
```

### 방법 3: 수동 테스트 (curl)

각 엔드포인트를 직접 테스트하려면:

```bash
# 1. 헬스 체크
curl http://localhost:8000/api/v1/health

# 2. 회원가입
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username":"admin",
    "email":"admin@example.com",
    "password":"admin123",
    "full_name":"Administrator"
  }'

# 3. 로그인
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 4. 시스템 초기화
curl -X POST http://localhost:8000/api/v1/systems/init

# 5. 적합도 계산
curl -X POST http://localhost:8000/api/v1/scores/calculate \
  -H "Authorization: Bearer $TOKEN"

# 6. 점수 조회
curl http://localhost:8000/api/v1/scores \
  -H "Authorization: Bearer $TOKEN"

# 7. RMSD 평가
curl -X POST http://localhost:8000/api/v1/evaluations/rmsd/1 \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 테스트 항목

### Task 1: 서버 기초 설정 및 정적 파일 호스팅
- ✅ 헬스 체크 엔드포인트 (/api/v1/health)
- ✅ 정적 파일 호스팅 (/ 경로)
- ✅ 로그인 API 엔드포인트

### Task 2: MariaDB 연동 및 ORM 모델링
- ✅ 사용자 회원가입 & 로그인
- ✅ JWT 토큰 발급 및 검증
- ✅ 12개 시스템 초기 데이터 생성
- ✅ 시스템 목록 조회
- ✅ User, System 테이블 ORM 매핑

### Task 3: 적합도 연산 및 그룹 판별 엔진
- ✅ 적합도 계산 수행 (2.1~2.4)
- ✅ 전체 점수 조회
- ✅ 특정 시스템 점수 조회
- ✅ 12개 시스템 등수 산출 확인
- ✅ 4개 그룹 분할 및 색상 할당 확인
- ✅ LSTM 예측 추세 데이터 포함 조회

### Task 4: MLOps 파이프라인(RMSD) 연동
- ✅ RMSD 평가 수행
- ✅ RMSD, MAE, MAPE 계산
- ✅ 임계값(5%) 확인
- ✅ 임계값 초과 시 모델 재학습 트리거
- ✅ MODEL_RETRAINING_LOG 기록

## ✨ 예상 출력

Python 스크립트 실행 시:

```
╔══════════════════════════════════════════════════════════╗
║  App Modernization Assessment v2.0 - 통합 테스트        ║
║  이슈 3: 모든 Task 검증 (Task 1~4)                      ║
╚══════════════════════════════════════════════════════════╝

📋 사전 확인:
   ✓ MariaDB 실행 중 (localhost:3306)
   ✓ FastAPI 서버 실행 중 (localhost:8000)
   ✓ Qdrant 실행 중 (localhost:6333, 옵션)

============================================================
Task 1: 서버 기초 설정 및 정적 파일 호스팅
============================================================

📝 1-1. 헬스 체크 엔드포인트
✅ 성공: 헬스 체크 성공

📝 1-2. 정적 파일 호스팅 (/ 경로)
✅ 성공: 정적 파일 서빙 (HTTP 200)

... (계속)

============================================================
테스트 결과 요약
============================================================
✅ 성공: 25개
❌ 실패: 0개
📊 전체: 25개

============================================================
🎉 모든 테스트 통과! 이슈 3 완료 기준 충족
============================================================

Definition of Done 체크:
   ✅ 서버 실행 후 / 접속 시 로그인 화면 렌더링
   ✅ /api/v1/scores 호출 시 점수와 LSTM/RAG 데이터 반환
   ✅ 적합도 평가 결과가 MariaDB에 기록/업데이트
   ✅ RMSD > 5% 초과 시 모델 재학습 트리거
```

## 🔧 문제 해결

### MariaDB 연결 오류
```
ConnectionRefusedError: [Errno 111] Connection refused
```
**해결책**: MariaDB가 실행 중인지 확인
```bash
sudo systemctl status mariadb
# 또는
mysql -u root -p -e "SELECT VERSION();"
```

### API 호출 실패 (HTTP 401)
```
{"detail": "토큰이 유효하지 않습니다"}
```
**해결책**: JWT 토큰을 다시 획득하세요
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 데이터베이스 테이블 생성 안 됨
**해결책**: MariaDB에서 데이터베이스 생성
```sql
CREATE DATABASE modernization_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE modernization_db;
```

### Qdrant 연결 오류 (옵션)
RAG와 LSTM 데이터가 없어도 기본 기능은 작동합니다.
Qdrant가 필요하면 Docker로 실행하세요.

## 📈 성능 테스트 (선택사항)

적합도 계산 성능 측정:

```bash
# 시간 측정과 함께 적합도 계산
time curl -X POST http://localhost:8000/api/v1/scores/calculate \
  -H "Authorization: Bearer $TOKEN"
```

## 🔐 보안 참고사항

**프로덕션 배포 전에 다음을 확인하세요:**

1. `.env` 파일에서 `JWT_SECRET_KEY` 변경
2. MariaDB 계정 비밀번호 보안화
3. CORS 설정 제한 (`ALLOWED_ORIGINS`)
4. API 속도 제한 (Rate Limiting) 추가
5. 로깅 및 모니터링 설정

## 📚 추가 정보

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 비동기 튜토리얼](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [JWT 인증](https://fastapi.tiangolo.com/advanced/security/oauth2-jwt/)
- [Qdrant 문서](https://qdrant.tech/documentation/)

---

**주의**: 테스트 데이터는 개발용입니다. 프로덕션 환경에서는 실제 데이터로 테스트하세요.
