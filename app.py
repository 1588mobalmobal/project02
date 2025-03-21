from flask import Flask, request, jsonify, render_template
import json
import db
import llm
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3

import io
import base64

app = Flask(__name__)

# 데이터베이스 초기화
db.init_db()

@app.route('/', methods = ['GET'])
def home():
    user_id = request.args.get('user_id')
    score = db.get_score(user_id)
    return render_template('home.html', score=score)

@app.route('/log', methods = ['GET'])
def log():
    return render_template('log.html')

@app.route('/browse', methods = ['GET'])
def browse():
    user_id = request.args.get('user_id')
    logs = db.get_logs(user_id)
    # print(logs)
    return render_template('browse.html', logs=logs)

@app.route('/api/llm', methods=['POST'])
def handle_llm_request():
    # 클라이언트로부터 JSON 데이터 받기
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({"error": "No input provided"}), 400
    
    user_input = data['input']
    
    # LLM 모델 실행
    llm_output = llm.get_llm_response(user_input)
    print(llm_output)

    encouragement = json.loads(llm_output)['격려']
    advice = json.loads(llm_output)['조언']
    physical = json.loads(llm_output)['체력']
    knowledge = json.loads(llm_output)['지식']
    mental = json.loads(llm_output)['정신력']

    # DB에 저장
    db.save_logs(user_input, encouragement, advice, physical, knowledge, mental)
    
    # 클라이언트에 JSON 응답 반환
    response = {
        "encouragement": encouragement,
        "advice": advice,
        "physical": physical,
        "knowledge": knowledge,
        "mental": mental,
        "timestamp": db.datetime.now().isoformat()
    }
    return jsonify(response), 200

@app.route('/weekly_chart')
def weekly_chart():
    
    data = db.get_weekly_data(1)
    # if not data:
    #     return "No data available for this user."

    # df = pd.DataFrame(data, columns=['physical', 'knowledge', 'mental', 'week'])
    # df = df.groupby('week').sum().reset_index()

    # chart_data = [["Week", "Physical", "Knowledge", "Mental"]]
    # for index, row in df.iterrows():
    #     chart_data.append([row['week'], row['physical'], row['knowledge'], row['mental']])
    
    
    return render_template('weekly_chart.html', data=data)


@app.route('/delete')
def delete_log():
    user_id = request.args.get('user_id')
    log_id = request.args.get('log_id')
    db.delete_log(user_id=user_id, log_id=log_id)
    return 'delete'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5252, debug=True)