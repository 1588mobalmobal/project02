import sqlite3
from datetime import datetime

# 최초 실행 시 DB 초기화 
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
              t_mental INTEGER DEFAULT 0
              );
    ''')
    conn.commit()
    conn.close()

# 사용자의 일기와 조언 및 점수를 저장하는 기능 
def save_logs(user_input, encouragement, advice, physical, knowledge, mental, v_index):
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
            INSERT INTO users (user_id, t_physical, t_knowledge, t_mental) VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            t_physical = t_physical + ?,
            t_knowledge = t_knowledge + ?,
            t_mental = t_mental + ?
            ''',
            (1, physical, knowledge, mental, physical, knowledge, mental)
            )
    conn.commit()
    conn.close()

# 사용자의 기록을 가져오는 기능 
def get_logs(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        SELECT user_input, encouragement, advice, physical, knowledge, mental, timestamp
        FROM logs
        WHERE user_id = ?;
    ''', user_id)
    result = c.fetchall()
    conn.close()

    return [row for row in result]

# 사용자의 점수를 가져오는 기능 
def get_score(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        SELECT t_physical, t_knowledge, t_mental
        FROM users
        WHERE user_id = ?;
    ''', user_id)
    result = c.fetchone()
    conn.close()

    return result

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

# 사용자의 기록을 삭제하고 점수를 환원하는 기능 
def delete_log(user_id, log_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        SELECT physical, knowledge, mental FROM logs
        WHERE user_id = ? and id = ?;
    ''',(user_id, log_id))
    scores = c.fetchone()
    physical = scores[0]
    knowledge = scores[1]
    mental = scores[2]

    c.execute('''
        DELETE FROM logs
        WHERE user_id = ? and id = ?;
    ''', (user_id, log_id))
    conn.commit()

    c.execute('''
        UPDATE users SET 
        t_physical = t_physical - ?,
        t_knowledge = t_knowledge - ?,
        t_mental = t_mental - ?
        WHERE user_id = ?
    ''', (physical, knowledge, mental, user_id))
    conn.commit()
    conn.close()

