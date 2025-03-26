from flask import Flask, request, jsonify, render_template, make_response
import json
import db
import llm
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3


###########대시보드 생성을 위한 라이브러리 호출
import dash
# import dash_core_components as dcc
# import dash_html_components as html
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
############

import io
import base64

import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

user_id = 1

db.init_db()

@app.route('/', methods=['GET'])
def home():
    score = db.get_score(user_id)
    if score is None:
        score = (0, 0, 0)
    
    # 가장 최근 로그의 추가 점수
    change = db.get_score_change(user_id) or (0, 0, 0)
    
    sign_physical = '+' if change[0] >= 0 else ''
    sign_knowledge = '+' if change[1] >= 0 else ''
    sign_mental = '+' if change[2] >= 0 else ''
    
    response = make_response(render_template('index.html', 
                                             physical=score[0], 
                                             knowledge=score[1], 
                                             mental=score[2], 
                                             change_physical=change[0], 
                                             change_knowledge=change[1], 
                                             change_mental=change[2], 
                                             sign_physical=sign_physical, 
                                             sign_knowledge=sign_knowledge, 
                                             sign_mental=sign_mental, 
                                             user_id=user_id))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.route('/write', methods=['GET'])
def log():
    return render_template('write.html')

@app.route('/browse', methods=['GET'])
def browse():
    logs = db.get_logs(user_id)
    return render_template('browse.html', logs=logs)

@app.route('/history', methods=['GET'])
def history():
    return render_template('history.html')

@app.route('/api/log', methods=['POST'])
def handle_llm_request():
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({"error": "No input provided"}), 400
    
    user_input = data['input']
    embedding = embed.get_embedding(user_input)
    v_index = embed.store_vector(embedding)
    llm_output = llm.get_log_response(user_input)

    encouragement = json.loads(llm_output)['격려']
    advice = json.loads(llm_output)['조언']
    physical = json.loads(llm_output)['체력']
    knowledge = json.loads(llm_output)['지식']
    mental = json.loads(llm_output)['정신력']

    print(f"LLM Output: physical={physical}, knowledge={knowledge}, mental={mental}, types: {type(physical)}, {type(knowledge)}, {type(mental)}")

    physical = int(physical)
    knowledge = int(knowledge)
    mental = int(mental)

    db.save_logs(user_input, encouragement, advice, physical, knowledge, mental, v_index)
    
    response = {
        "encouragement": encouragement,
        "advice": advice,
        "physical": physical,
        "knowledge": knowledge,
        "mental": mental,
        "timestamp": db.datetime.now().isoformat()
    }
    return jsonify(response), 200

@app.route('/chat', methods=['GET'])
def chat():
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chatting():
    data = request.get_json()
    if not data or 'chat' not in data:
        return jsonify({"error": "No chat provided"}), 400
    
    chat = data['chat']
    embedding = embed.get_embedding(chat)
    _, indices = embed.search_vector_store(embedding)
    logs = db.get_log_by_vector(indices)
    llm_output = llm.get_chat_response(user_input=chat, prompt_input=logs)
    return jsonify(llm_output), 200

###Plotly와 Dash를 이용하여 웹에서 시각화 띄우기
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')

# 레이아웃 정의
dash_app.layout = html.Div([
    html.H1("상태 변화 시각화"),
    dcc.Graph(id="state-plot"),
])

# 콜백 함수 정의
@dash_app.callback(
    Output("state-plot", "figure"),
    Input("state-plot", "id")
)
### 시각화 해주는 함수
def update_graph(id):
    # 데이터베이스 연결
    conn = sqlite3.connect('database.db')
    query = "SELECT physical, knowledge, mental, timestamp FROM logs" # 테이블명 변경필요
    df = pd.read_sql_query(query, conn)
    conn.close()

    # timestamp를 datetime 형식으로 변환
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 누적 합계 계산
    df_cumsum = df.set_index('timestamp').cumsum().reset_index()

    # Plotly 누적 선 그래프 생성
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_cumsum['timestamp'], y=df_cumsum['physical'], mode='lines+markers', name='Physical'))
    fig.add_trace(go.Scatter(x=df_cumsum['timestamp'], y=df_cumsum['knowledge'], mode='lines+markers', name='Knowledge'))
    fig.add_trace(go.Scatter(x=df_cumsum['timestamp'], y=df_cumsum['mental'], mode='lines+markers', name='Mental'))

    fig.update_layout(title='Cumulative Scores by Date', xaxis_title='Date', yaxis_title='Score')

    return fig

# lask 라우팅 추가
@app.route('/dashboard')
def dashboard():
    user_id = request.args.get('user_id')
    # user_id를 사용하여 필요한 데이터 필터링 또는 사용자별 데이터 로딩 로직 추가
    # 예시: user_id에 따라 데이터 필터링
    # filtered_df = df[df['user_id'] == user_id]

    # Dash 앱의 레이아웃을 HTML로 렌더링
    dash_app_html = dash_app.index()
    return dash_app_html

@app.route('/delete')
def delete_log():
    user_id = int(request.args.get('user_id', 1))
    log_id = int(request.args.get('log_id', 0))
    db.delete_log(user_id=user_id, log_id=log_id)
    return 'delete'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5252, debug=True)