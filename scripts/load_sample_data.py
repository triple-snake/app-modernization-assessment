#!/usr/bin/env python3
"""
Excel 데이터를 MariaDB에 로드하는 스크립트
sample_system_logs_6000.xlsx 파일의 6000개 로그를 RAW_LOG 테이블에 삽입
"""

import pandas as pd
import pymysql
from datetime import datetime
import sys
import os

# MariaDB 연결 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'appuser',
    'password': 'apppassword',
    'database': 'appdb',
    'charset': 'utf8mb4'
}

def load_excel_to_db(excel_file='sample_system_logs_6000.xlsx'):
    """Excel 파일을 읽어서 MariaDB에 삽입"""
    
    # 파일 존재 확인
    if not os.path.exists(excel_file):
        print(f"❌ Error: {excel_file} 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    print(f"📂 Excel 파일 읽는 중: {excel_file}")
    
    try:
        # Excel 파일 읽기
        df = pd.read_excel(excel_file)
        print(f"✅ Excel 파일 로드 완료: {len(df)} 행")
        
        # 컬럼명 확인 및 표준화
        print(f"📋 컬럼: {df.columns.tolist()}")
        
        # 필수 컬럼 매핑 (Excel 파일의 실제 컬럼명에 맞춰 조정)
        # 예상 컬럼: system_id, timestamp, log_type, level, message
        column_mapping = {
            'system_id': 'system_id',
            'timestamp': 'timestamp',
            'log_type': 'log_type',
            'level': 'level',
            'message': 'message'
        }
        
        # 컬럼명 변경 (대소문자 무시)
        df.columns = df.columns.str.lower().str.strip()
        
    except Exception as e:
        print(f"❌ Excel 파일 읽기 실패: {e}")
        sys.exit(1)
    
    # MariaDB 연결
    print(f"\n🔌 MariaDB 연결 중: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ MariaDB 연결 성공")
        
        # 기존 RAW_LOG 데이터 삭제 (재실행 시)
        cursor.execute("DELETE FROM RAW_LOG")
        connection.commit()
        print("🗑️  기존 RAW_LOG 데이터 삭제")
        
        # SYSTEM 테이블에 12개 시스템 등록
        print("\n📝 SYSTEM 테이블에 시스템 등록 중...")
        unique_systems = df['system_id'].unique()
        print(f"발견된 시스템 수: {len(unique_systems)}")
        
        for system_id in unique_systems:
            cursor.execute("""
                INSERT IGNORE INTO SYSTEM (user_id, system_name, owner_team, system_type, business_criticality)
                VALUES (1, %s, 'Test Team', 'Backend', 'High')
            """, (f'System {system_id}',))
        
        connection.commit()
        print(f"✅ {len(unique_systems)}개 시스템 등록 완료")
        
        # RAW_LOG 삽입
        print(f"\n💾 RAW_LOG 테이블에 데이터 삽입 중... (총 {len(df)}개)")
        
        insert_query = """
            INSERT INTO RAW_LOG (system_id, timestamp, log_type, level, message)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            values = []
            for _, row in batch.iterrows():
                # timestamp 변환 (문자열이면 datetime으로 변환)
                timestamp = row['timestamp']
                if isinstance(timestamp, str):
                    timestamp = pd.to_datetime(timestamp)
                
                values.append((
                    str(row['system_id']),
                    timestamp,
                    row.get('log_type', 'unknown'),
                    row.get('level', 'INFO'),
                    str(row.get('message', ''))
                ))
            
            cursor.executemany(insert_query, values)
            connection.commit()
            total_inserted += len(values)
            
            if total_inserted % 500 == 0:
                print(f"  진행: {total_inserted}/{len(df)} 행 삽입...")
        
        print(f"✅ 총 {total_inserted}개 로그 삽입 완료")
        
        # 검증
        print("\n🔍 데이터 검증 중...")
        cursor.execute("SELECT COUNT(*) FROM RAW_LOG")
        count = cursor.fetchone()[0]
        print(f"✅ RAW_LOG 테이블 총 행 수: {count}")
        
        cursor.execute("SELECT system_id, COUNT(*) as cnt FROM RAW_LOG GROUP BY system_id ORDER BY system_id")
        results = cursor.fetchall()
        print("\n📊 시스템별 로그 수:")
        for system_id, cnt in results:
            print(f"  - {system_id}: {cnt}개")
        
        cursor.close()
        connection.close()
        print("\n✅ 모든 작업 완료!")
        
    except pymysql.Error as e:
        print(f"❌ MariaDB 오류: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("=" * 60)
    print("Excel 데이터 → MariaDB 로드 스크립트")
    print("=" * 60)
    load_excel_to_db()
