import pandas as pd
import sqlite3
import os  # os 모듈 추가
from data_generator import generate_data

def save_dataframe_to_sqlite(df, db_path):
    """데이터프레임을 SQLite 데이터베이스에 저장"""
    # 데이터베이스 파일이 존재하면 삭제
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    df.to_sql('logs', conn, if_exists='replace', index=False)
    conn.close()

if __name__ == "__main__":
    df = generate_data()
    db_path = 'database.db'
    save_dataframe_to_sqlite(df, db_path)
    print(f"데이터가 '{db_path}'에 성공적으로 저장되었습니다.")