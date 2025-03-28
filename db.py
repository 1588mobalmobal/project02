import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS logs 
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER, 
              user_input TEXT, 
              encouragement TEXT, 
              advice TEXT, 
              physical INTEGER, 
              knowledge INTEGER, 
              mental INTEGER,
              v_index INTEGER,
              timestamp TEXT);
              ''')
    conn.commit()
    conn.execute(
    '''
    CREATE TABLE IF NOT EXISTS users
              (user_id INTEGER PRIMARY KEY NOT NULL,
              t_physical INTEGER DEFAULT 0,
              t_knowledge INTEGER DEFAULT 0,
              t_mental INTEGER DEFAULT 0,
              log_count INTEGER DEFAULT 0
              );
    ''')
    conn.commit()
    conn.close()

def save_logs(user_input, encouragement, advice, physical, knowledge, mental, v_index):
    physical = int(physical)
    knowledge = int(knowledge)
    mental = int(mental)

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute('''
              INSERT INTO logs 
              (user_id, user_input, encouragement, advice, physical, knowledge, mental, v_index, timestamp)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
              ''',
              (1, user_input, encouragement, advice, physical, knowledge, mental, v_index, timestamp)
              )
    conn.commit()
    c.execute('''
            INSERT INTO users (user_id, t_physical, t_knowledge, t_mental, log_count) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            t_physical = t_physical + ?,
            t_knowledge = t_knowledge + ?,
            t_mental = t_mental + ?,
            log_count = log_count + ?
            ''',
            (1, physical, knowledge, mental, 1, physical, knowledge, mental, 1)
            )
    conn.commit()
    conn.close()

def get_logs(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, user_input, encouragement, advice, physical, knowledge, mental, timestamp
        FROM logs
        WHERE user_id = ?;
    ''', (int(user_id),))
    result = c.fetchall()
    conn.close()
    return [row for row in result]

def get_score(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        SELECT t_physical, t_knowledge, t_mental
        FROM users
        WHERE user_id = ?;
    ''', (int(user_id),))
    result = c.fetchone()
    conn.close()
    return result

def get_score_change(user_id):
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        # 가장 최근 로그의 점수를 가져옴
        c.execute('''
            SELECT physical, knowledge, mental
            FROM logs
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 1;
        ''', (int(user_id),))
        result = c.fetchone()
        conn.close()

        if result is None:
            return (0, 0, 0)
        
        return (result[0], result[1], result[2])
    except Exception as e:
        print(f"Error in get_score_change: {e}")
        return (0, 0, 0)

def get_log_by_vector(indices):
    result = []
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    for idx in indices[0]:
        idx = int(idx)
        if idx != -1:
            c.execute("select user_input from logs where v_index = ? ;", (idx,))
            result.append(c.fetchone())
    conn.close()
    return result

def get_log_count(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try :
        c.execute('''
            SELECT log_count FROM users WHERE user_id = ?;
        ''', (int(user_id),))
        log_count = c.fetchone()
        conn.close()
        return log_count
    except Exception as e :
        print(f"Error in delete_log: {e}")
        conn.close()
        return 0
    

def delete_log(user_id, log_id):
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            SELECT physical, knowledge, mental, v_index FROM logs
            WHERE user_id = ? and id = ?;
        ''', (int(user_id), int(log_id)))
        scores = c.fetchone()
        if scores is None:
            conn.close()
            return
        
        physical = scores[0]
        knowledge = scores[1]
        mental = scores[2]
        v_index = scores[3]

        c.execute('''
            DELETE FROM logs
            WHERE user_id = ? and id = ?;
        ''', (int(user_id), int(log_id)))
        conn.commit()

        c.execute('''
            UPDATE users SET 
            t_physical = t_physical - ?,
            t_knowledge = t_knowledge - ?,
            t_mental = t_mental - ?
            WHERE user_id = ?
        ''', (physical, knowledge, mental, int(user_id)))
        conn.commit()
        conn.close()
        return v_index
    except Exception as e:
        print(f"Error in delete_log: {e}")
        conn.close()


# 일기 기록 검색 함수(1대1대화에서 쓰기위한)
def get_today_log(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''
        SELECT user_input FROM logs 
        WHERE user_id = ? AND timestamp LIKE ? 
        ORDER BY timestamp DESC LIMIT 1
    ''', (int(user_id), f"{today}%"))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_past_log_by_date(user_id, date_str):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # date_str은 "2025-03-25" 같은 형식 또는 "2025-03"처럼 월 단위도 가능
    c.execute('''
        SELECT user_input, timestamp FROM logs 
        WHERE user_id = ? AND timestamp LIKE ? 
        ORDER BY timestamp DESC LIMIT 1
    ''', (int(user_id), f"{date_str}%"))
    result = c.fetchone()
    conn.close()
    return {"content": result[0], "timestamp": result[1]} if result else None

def get_past_log_by_keyword(user_id, keyword):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        SELECT user_input, timestamp FROM logs 
        WHERE user_id = ? AND user_input LIKE ? 
        ORDER BY timestamp DESC LIMIT 1
    ''', (int(user_id), f"%{keyword}%"))
    result = c.fetchone()
    conn.close()
    return {"content": result[0], "timestamp": result[1]} if result else None