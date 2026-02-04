-- Cloud Native Readiness Assessment Database Schema (PoC)
-- 초기 테이블만 생성 (데이터는 별도 스크립트로 로드)

CREATE DATABASE IF NOT EXISTS appdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE appdb;

-- ============================================================================
-- Core Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS USER (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS SYSTEM (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    system_name VARCHAR(255) NOT NULL,
    owner_team VARCHAR(255),
    system_type VARCHAR(100),
    business_criticality VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES USER(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS INPUT_DATA (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_id BIGINT NOT NULL,
    input_source VARCHAR(100) DEFAULT 'DOCUMENT',
    raw_text TEXT,
    extracted_fields JSON NOT NULL COMMENT '12개 문서 지표 key-value',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES SYSTEM(id) ON DELETE CASCADE,
    INDEX idx_system (system_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS RAW_LOG (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_id VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    log_type VARCHAR(100),
    level VARCHAR(50),
    message TEXT,
    ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_system_time (system_id, timestamp)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS LOG_BATCH (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_id BIGINT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    log_count INT DEFAULT 0,
    merged_log_text LONGTEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES SYSTEM(id) ON DELETE CASCADE,
    INDEX idx_system_date (system_id, start_time)
) ENGINE=InnoDB;

-- ============================================================================
-- LLM & Scoring Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS LLM_EVALUATION (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_id BIGINT NOT NULL,
    log_batch_id BIGINT,
    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_grades JSON NOT NULL COMMENT '22개 지표 Grade 1~3',
    evaluation_reason TEXT,
    llm_model VARCHAR(100),
    prompt_version VARCHAR(50),
    FOREIGN KEY (system_id) REFERENCES SYSTEM(id) ON DELETE CASCADE,
    FOREIGN KEY (log_batch_id) REFERENCES LOG_BATCH(id),
    INDEX idx_system_date (system_id, evaluated_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS METRIC_SCORE (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_id BIGINT NOT NULL,
    metric_code VARCHAR(100) NOT NULL,
    grade INT NOT NULL COMMENT 'Grade 1/2/3',
    score FLOAT NOT NULL COMMENT '(3-grade)/2',
    weight FLOAT DEFAULT 1.0,
    score_source VARCHAR(100) DEFAULT 'PYTHON',
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES SYSTEM(id) ON DELETE CASCADE,
    INDEX idx_system_metric (system_id, metric_code, calculated_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS SYSTEM_SCORE (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_id BIGINT NOT NULL,
    value_score FLOAT NOT NULL,
    ease_score FLOAT NOT NULL,
    total_score FLOAT NOT NULL,
    final_grade VARCHAR(10),
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES SYSTEM(id) ON DELETE CASCADE,
    INDEX idx_system_date (system_id, calculated_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS LLM_SUMMARY (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_id BIGINT NOT NULL,
    system_score_id BIGINT,
    prediction_id BIGINT,
    summary_type VARCHAR(100),
    summary_text TEXT,
    key_recommendation TEXT,
    risk_notes TEXT,
    llm_model VARCHAR(100),
    prompt_version VARCHAR(50),
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES SYSTEM(id) ON DELETE CASCADE,
    FOREIGN KEY (system_score_id) REFERENCES SYSTEM_SCORE(id)
) ENGINE=InnoDB;

-- ============================================================================
-- Time Series & RMSD Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS TIMESERIES_PREDICTION (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_id BIGINT NOT NULL,
    predicted_at DATETIME NOT NULL,
    metric_code VARCHAR(100) NOT NULL,
    prediction_horizon DATETIME NOT NULL,
    predicted_value FLOAT NOT NULL,
    model_version VARCHAR(100),
    FOREIGN KEY (system_id) REFERENCES SYSTEM(id) ON DELETE CASCADE,
    INDEX idx_system_metric (system_id, metric_code, prediction_horizon)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS METRIC_ACTUAL (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    system_id BIGINT NOT NULL,
    metric_code VARCHAR(100) NOT NULL,
    actual_time DATETIME NOT NULL,
    actual_value FLOAT NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (system_id) REFERENCES SYSTEM(id) ON DELETE CASCADE,
    INDEX idx_system_metric (system_id, metric_code, actual_time)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS PREDICTION_EVALUATION (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prediction_id BIGINT NOT NULL,
    actual_id BIGINT NOT NULL,
    prediction_error FLOAT,
    rmsd_value FLOAT,
    is_threshold_exceeded BOOLEAN DEFAULT FALSE COMMENT 'RMSD >= 10.0',
    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES TIMESERIES_PREDICTION(id),
    FOREIGN KEY (actual_id) REFERENCES METRIC_ACTUAL(id)
) ENGINE=InnoDB;

-- ============================================================================
-- 초기 테스트 사용자 (1명)
-- ============================================================================

INSERT INTO USER (email, name) VALUES ('admin@example.com', 'Admin User');

COMMIT;

-- 초기화 완료
SELECT '============================================' AS '';
SELECT 'Database Schema Created Successfully!' AS '';
SELECT '============================================' AS '';
SELECT CONCAT('Total Tables: ', COUNT(*)) AS 'Status' 
FROM information_schema.tables 
WHERE table_schema = 'appdb';
SELECT '============================================' AS '';
SELECT 'Next: Run load_sample_data.py to import Excel data' AS '';
SELECT '============================================' AS '';
