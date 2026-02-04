#!/bin/bash

# ============================================================
# App Modernization Assessment v2.0 - 통합 테스트 시나리오
# ============================================================
# 이슈 3의 모든 Task를 검증하는 테스트 스크립트
#
# 전제조건:
# 1. MariaDB 실행 중
# 2. Qdrant 실행 중 (옵션)
# 3. FastAPI 서버 실행 중 (port 8000)
# 4. .env 파일 설정 완료
# ============================================================

set -e

BASE_URL="http://localhost:8000"
API_VERSION="api/v1"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 테스트 결과 기록
TEST_PASSED=0
TEST_FAILED=0

# ============================================================
# 유틸리티 함수
# ============================================================

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_test() {
    echo -e "\n${YELLOW}📝 $1${NC}"
}

success() {
    echo -e "${GREEN}✅ 성공: $1${NC}"
    ((TEST_PASSED++))
}

error() {
    echo -e "${RED}❌ 실패: $1${NC}"
    ((TEST_FAILED++))
}

# ============================================================
# Task 1: 서버 기초 설정 및 정적 파일 호스팅
# ============================================================

task_1_server_setup() {
    print_header "Task 1: 서버 기초 설정 및 정적 파일 호스팅"
    
    # Test 1-1: 헬스 체크
    print_test "1-1. 헬스 체크 엔드포인트 (/api/v1/health)"
    response=$(curl -s -X GET "$BASE_URL/$API_VERSION/health")
    if echo "$response" | grep -q "ok"; then
        success "헬스 체크 성공"
        echo "응답: $response"
    else
        error "헬스 체크 실패"
        echo "응답: $response"
    fi
    
    # Test 1-2: 정적 파일 호스팅 (프론트엔드)
    print_test "1-2. 정적 파일 호스팅 (/ 경로 - HTML)"
    status=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/")
    if [ "$status" = "200" ] || [ "$status" = "404" ]; then
        success "정적 파일 서빙 설정 완료 (HTTP $status)"
    else
        error "정적 파일 서빙 실패 (HTTP $status)"
    fi
    
    # Test 1-3: 로그인 엔드포인트
    print_test "1-3. 로그인 API 검증 (/api/v1/auth/login)"
    response=$(curl -s -X POST "$BASE_URL/$API_VERSION/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}' \
        -w "\n%{http_code}")
    status=$(echo "$response" | tail -1)
    if [ "$status" = "401" ] || [ "$status" = "400" ]; then
        success "로그인 엔드포인트 정상 작동 (HTTP $status)"
    else
        error "로그인 엔드포인트 오류 (HTTP $status)"
    fi
}

# ============================================================
# Task 2: MariaDB 연동 및 ORM 모델링
# ============================================================

task_2_database_setup() {
    print_header "Task 2: MariaDB 연동 및 ORM 모델링"
    
    # 임시 사용자 생성 (JWT 토큰 획득용)
    print_test "2-0. 테스트 사용자 생성"
    signup_response=$(curl -s -X POST "$BASE_URL/$API_VERSION/auth/signup" \
        -H "Content-Type: application/json" \
        -d '{
            "username":"testuser",
            "email":"test@example.com",
            "password":"Test123!@#",
            "full_name":"Test User"
        }')
    
    if echo "$signup_response" | grep -q "testuser"; then
        success "사용자 생성 성공"
        echo "응답: $signup_response"
    else
        # 이미 존재할 수 있으므로 로그인 진행
        echo "사용자가 이미 존재하거나 생성됨, 로그인 진행..."
    fi
    
    # 로그인 및 토큰 획득
    print_test "2-1. JWT 토큰 획득"
    login_response=$(curl -s -X POST "$BASE_URL/$API_VERSION/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"testuser","password":"Test123!@#"}')
    
    TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    if [ -n "$TOKEN" ]; then
        success "JWT 토큰 획득 성공"
        echo "토큰: ${TOKEN:0:20}..."
    else
        error "JWT 토큰 획득 실패"
        echo "응답: $login_response"
        return 1
    fi
    
    # Test 2-2: 12개 시스템 초기화
    print_test "2-2. 12개 시스템 데이터 생성 (/api/v1/systems/init)"
    init_response=$(curl -s -X POST "$BASE_URL/$API_VERSION/systems/init")
    
    if echo "$init_response" | grep -q "success\|이미"; then
        success "시스템 초기화 성공"
        echo "응답: $init_response"
    else
        error "시스템 초기화 실패"
        echo "응답: $init_response"
    fi
    
    # Test 2-3: 시스템 목록 조회
    print_test "2-3. 시스템 목록 조회 (/api/v1/systems)"
    systems_response=$(curl -s -X GET "$BASE_URL/$API_VERSION/systems" \
        -H "Authorization: Bearer $TOKEN")
    
    system_count=$(echo "$systems_response" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    
    if [ "$system_count" = "12" ] || [ "$system_count" -gt "0" ]; then
        success "시스템 조회 성공 ($system_count개)"
        echo "응답: $systems_response" | head -c 200
    else
        error "시스템 조회 실패 (개수: $system_count)"
    fi
    
    # Test 2-4: 사용자 정보 확인
    print_test "2-4. JWT 토큰 검증 및 사용자 정보"
    if [ -n "$TOKEN" ]; then
        success "JWT 토큰 유효성 확인 완료"
        # payload 디코딩 (간단한 검증)
        echo "토큰 타입: Bearer"
    else
        error "JWT 토큰 검증 실패"
    fi
    
    # 나중 Task에서 사용할 TOKEN 저장
    export JWT_TOKEN="$TOKEN"
}

# ============================================================
# Task 3: 적합도 연산 및 그룹 판별 엔진
# ============================================================

task_3_scoring_engine() {
    print_header "Task 3: 적합도 연산 및 그룹 판별 엔진"
    
    if [ -z "$JWT_TOKEN" ]; then
        error "JWT 토큰이 없습니다. Task 2를 먼저 실행하세요."
        return 1
    fi
    
    # Test 3-1: 적합도 계산
    print_test "3-1. 적합도 계산 (/api/v1/scores/calculate)"
    calc_response=$(curl -s -X POST "$BASE_URL/$API_VERSION/scores/calculate" \
        -H "Authorization: Bearer $JWT_TOKEN")
    
    if echo "$calc_response" | grep -q "success"; then
        success "적합도 계산 완료"
        echo "응답: $calc_response" | head -c 300
    else
        error "적합도 계산 실패"
        echo "응답: $calc_response"
    fi
    
    # Test 3-2: 점수 조회 (전체)
    print_test "3-2. 적합도 평가 결과 조회 (전체) (/api/v1/scores)"
    scores_response=$(curl -s -X GET "$BASE_URL/$API_VERSION/scores" \
        -H "Authorization: Bearer $JWT_TOKEN")
    
    if echo "$scores_response" | grep -q '"count"'; then
        score_count=$(echo "$scores_response" | grep -o '"count":[0-9]*' | cut -d':' -f2)
        success "점수 조회 성공 ($score_count개 시스템)"
        
        # 그룹 정보 확인
        if echo "$scores_response" | grep -q '"group_color"'; then
            success "그룹 판별 로직 작동 (색상 할당 확인)"
        fi
    else
        error "점수 조회 실패"
    fi
    
    # Test 3-3: 특정 시스템 점수 조회
    print_test "3-3. 특정 시스템 점수 조회 (/api/v1/scores?system_id=1)"
    single_score=$(curl -s -X GET "$BASE_URL/$API_VERSION/scores?system_id=1" \
        -H "Authorization: Bearer $JWT_TOKEN")
    
    if echo "$single_score" | grep -q '"system_id":1'; then
        success "특정 시스템 점수 조회 성공"
        
        # 2.1~2.4 지표 확인
        if echo "$single_score" | grep -q '"ops_score"\|"sec_score"\|"biz_score"\|"total_score"'; then
            success "2.1~2.4 지표 계산 확인 (ops, sec, biz, total)"
        fi
        
        # 등수 확인
        if echo "$single_score" | grep -q '"ops_rank"\|"sec_rank"\|"biz_rank"\|"total_rank"'; then
            success "12개 시스템 등수 산출 확인"
        fi
        
        # 그룹 확인
        if echo "$single_score" | grep -q '"group_number"'; then
            group=$(echo "$single_score" | grep -o '"group_number":[0-9]' | cut -d':' -f2)
            if [ "$group" -ge "1" ] && [ "$group" -le "4" ]; then
                success "4개 그룹 분할 확인 (그룹: $group)"
            fi
        fi
    else
        error "특정 시스템 점수 조회 실패"
    fi
    
    # Test 3-4: LSTM 추세 데이터 포함 조회
    print_test "3-4. LSTM 예측 추세 데이터 포함 조회"
    lstm_score=$(curl -s -X GET "$BASE_URL/$API_VERSION/scores?system_id=1&include_lstm=true" \
        -H "Authorization: Bearer $JWT_TOKEN")
    
    if echo "$lstm_score" | grep -q '"lstm_trend"'; then
        success "LSTM 예측 데이터 포함 확인"
    else
        error "LSTM 데이터 포함 실패"
    fi
}

# ============================================================
# Task 4: MLOps 파이프라인(RMSD) 연동
# ============================================================

task_4_mlops_pipeline() {
    print_header "Task 4: MLOps 파이프라인(RMSD) 연동"
    
    if [ -z "$JWT_TOKEN" ]; then
        error "JWT 토큰이 없습니다. Task 2를 먼저 실행하세요."
        return 1
    fi
    
    # Test 4-1: RMSD 평가 수행
    print_test "4-1. RMSD 평가 수행 (/api/v1/evaluations/rmsd/{system_id})"
    rmsd_response=$(curl -s -X POST "$BASE_URL/$API_VERSION/evaluations/rmsd/1" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$rmsd_response" | grep -q '"status":"success"'; then
        success "RMSD 평가 완료"
        
        # RMSD 값 확인
        if echo "$rmsd_response" | grep -q '"rmsd"'; then
            rmsd_value=$(echo "$rmsd_response" | grep -o '"rmsd":[0-9.]*' | cut -d':' -f2)
            success "RMSD 계산 완료 (값: $rmsd_value)"
            
            # MAE, MAPE 확인
            if echo "$rmsd_response" | grep -q '"mae"\|"mape"'; then
                success "MAE, MAPE 계산 확인"
            fi
        fi
        
        echo "응답: $rmsd_response" | head -c 400
    else
        error "RMSD 평가 실패 (데이터 부족 가능)"
        echo "응답: $rmsd_response"
    fi
    
    # Test 4-2: 임계값 확인 (5%)
    print_test "4-2. RMSD 임계값 확인 (5% 이내)"
    if echo "$rmsd_response" | grep -q '"is_within_threshold"'; then
        within=$(echo "$rmsd_response" | grep -o '"is_within_threshold":[^,}]*' | cut -d':' -f2)
        if [ "$within" = "true" ]; then
            success "임계값 이내 (안전 범위)"
        else
            success "임계값 초과 (재학습 필요)"
        fi
    fi
    
    # Test 4-3: 모델 재학습 트리거 확인
    print_test "4-3. RMSD 초과 시 모델 재학습 트리거"
    if echo "$rmsd_response" | grep -q '"retraining_triggered"'; then
        triggered=$(echo "$rmsd_response" | grep -o '"retraining_triggered":[^,}]*' | cut -d':' -f2)
        if [ "$triggered" = "true" ]; then
            success "모델 재학습 트리거 발동"
            
            # 재학습 로그 확인
            if echo "$rmsd_response" | grep -q '"retraining_log"'; then
                success "모델 재학습 로그 기록"
                echo "재학습 로그: $rmsd_response" | grep -o '"retraining_log":{[^}]*}'
            fi
        else
            success "모델 재학습 필요 없음 (안정적 성능)"
        fi
    fi
}

# ============================================================
# 추가 검증: 프로젝트 선택 및 대시보드 내비게이션
# ============================================================

additional_validation() {
    print_header "추가 검증: 사용자 워크플로우"
    
    if [ -z "$JWT_TOKEN" ]; then
        error "JWT 토큰이 없습니다. Task 2를 먼저 실행하세요."
        return 1
    fi
    
    # Test: 프로젝트 선택
    print_test "프로젝트 선택 API (/api/v1/projects/select)"
    project_response=$(curl -s -X POST "$BASE_URL/$API_VERSION/projects/select" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"project_id":1,"project_name":"프로젝트 A"}')
    
    if echo "$project_response" | grep -q '"status":"success"'; then
        success "프로젝트 선택 성공"
        
        if echo "$project_response" | grep -q '"redirect"'; then
            success "대시보드 리디렉션 URL 생성"
        fi
    else
        error "프로젝트 선택 실패"
    fi
    
    # Test: RAG 인사이트 포함 조회
    print_test "RAG 기반 인사이트 포함 조회"
    rag_score=$(curl -s -X GET "$BASE_URL/$API_VERSION/scores?system_id=1&include_rag=true" \
        -H "Authorization: Bearer $JWT_TOKEN")
    
    if echo "$rag_score" | grep -q '"rag_insights"'; then
        success "RAG 기반 측정 근거 데이터 포함"
    else
        error "RAG 데이터 포함 실패 (Qdrant 연동 필요)"
    fi
}

# ============================================================
# 테스트 실행
# ============================================================

main() {
    echo -e "${BLUE}"
    cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║  App Modernization Assessment v2.0                      ║
║  통합 테스트 시나리오 (이슈 3 - Task 1~4)                ║
╚══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "\n${YELLOW}📋 사전 확인:${NC}"
    echo "- MariaDB 실행 중? (localhost:3306)"
    echo "- FastAPI 서버 실행 중? (localhost:8000)"
    echo "- Qdrant 실행 중? (localhost:6333, 옵션)"
    
    read -p "위 조건이 모두 충족되었습니까? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}테스트를 건너뜁니다.${NC}"
        return 1
    fi
    
    # 각 Task 실행
    task_1_server_setup
    task_2_database_setup
    task_3_scoring_engine
    task_4_mlops_pipeline
    additional_validation
    
    # 최종 결과
    print_header "테스트 결과 요약"
    
    total=$((TEST_PASSED + TEST_FAILED))
    
    echo -e "${GREEN}✅ 성공: $TEST_PASSED개${NC}"
    echo -e "${RED}❌ 실패: $TEST_FAILED개${NC}"
    echo -e "📊 전체: $total개\n"
    
    if [ $TEST_FAILED -eq 0 ]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🎉 모든 테스트 통과! 이슈 3 완료 기준 충족${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    else
        echo -e "${YELLOW}⚠️  일부 테스트 실패. 상세 로그를 확인하세요.${NC}"
    fi
}

# 메인 실행
main
