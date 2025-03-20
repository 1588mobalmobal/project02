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

def save_logs(user_input, encouragement, advice, physical, knowledge, mental):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute('''
              INSERT INTO logs 
              (user_id, user_input, encouragement, advice, physical, knowledge, mental, timestamp)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?)
              ''',
              (1, user_input, encouragement, advice, physical, knowledge, mental, timestamp)
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
        t_knowledge = t_knowledge-+ ?,
        t_mental = t_mental - ?
        WHERE user_id = ?
    ''', (physical, knowledge, mental, user_id))
    conn.commit()
    conn.close()

