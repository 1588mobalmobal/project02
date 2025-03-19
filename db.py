import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_input TEXT, 
                  llm_output TEXT, 
                  timestamp TEXT);
              ''')
    conn.commit()
    conn.close()

def save_interaction(user_input, llm_output):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT INTO logs (user_input, llm_output, timestamp) VALUES (?, ?, ?)",
              (user_input, llm_output, timestamp))
    conn.commit()
    conn.close()