from flask import Flask, request, jsonify, render_template, make_response
import json
import db
import llm
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3


###########대시보드 생성을 위한 라이브러리 호출
import datetime
import dash
# import dash_core_components as dcc
# import dash_html_components as html
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import plotly.express as px
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
    dcc.DatePickerSingle(
        id='date-picker',
        date=datetime.date.today(),
        display_format='YYYY-MM-DD'  # 날짜 표시 형식 변경
    ),
    html.Div(id='date-range-display'),  # 선택된 날짜 범위 표시
    dcc.Graph(id="cumulative-plot", style={'width': '100%', 'height': '400px'}),  # 누적 선 그래프
    html.Div([  # 도넛 차트와 스타 차트를 감싸는 div 추가
        dcc.Graph(id="donut-chart", style={'width': '50%', 'display': 'inline-block'}),  # 도넛 차트
        dcc.Graph(id="radar-chart", style={'width': '50%', 'display': 'inline-block'})  # 스타 차트
    ])
])

# 콜백 함수 정의
@dash_app.callback(
    Output("cumulative-plot", "figure"),
    Output("donut-chart", "figure"),
    Output("radar-chart", "figure"),
    Output("date-range-display", "children"),  # 날짜 범위 표시 출력 추가
    Input("date-picker", "date")  # 선택된 날짜 입력 추가
)
def update_graph(selected_date):
    # 데이터베이스 연결
    conn = sqlite3.connect('database.db')
    query = "SELECT physical, knowledge, mental, timestamp FROM logs"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # timestamp를 datetime 형식으로 변환
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 선택된 날짜를 기준으로 1주일 전까지의 데이터 필터링
    if selected_date:
        end_date = pd.to_datetime(selected_date).date()
        start_date = end_date - datetime.timedelta(days=6)
        filtered_df = df[(df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)]
        date_range = f"{start_date} ~ {end_date}"  # 날짜 범위 표시
    else:
        filtered_df = df  # 모든 데이터 사용
        date_range = "전체 기간"

    # 누적 합계 계산 (선택된 날짜까지 또는 전체 데이터)
    df_cumsum = filtered_df.set_index('timestamp').cumsum().reset_index()

    # Plotly 누적 선 그래프 생성
    fig_cumulative = go.Figure()
    fig_cumulative.add_trace(go.Scatter(x=df_cumsum['timestamp'], y=df_cumsum['physical'], mode='lines+markers', name='Physical'))
    fig_cumulative.add_trace(go.Scatter(x=df_cumsum['timestamp'], y=df_cumsum['knowledge'], mode='lines+markers', name='Knowledge'))
    fig_cumulative.add_trace(go.Scatter(x=df_cumsum['timestamp'], y=df_cumsum['mental'], mode='lines+markers', name='Mental'))

    fig_cumulative.update_layout(title='Cumulative Scores by Date', xaxis_title='Date', yaxis_title='Score')

    # 누적 도넛 차트 생성 (선택된 날짜까지 또는 전체 데이터)
    total_physical = filtered_df['physical'].sum()
    total_knowledge = filtered_df['knowledge'].sum()
    total_mental = filtered_df['mental'].sum()

    fig_donut = go.Figure(data=[go.Pie(labels=['Physical', 'Knowledge', 'Mental'],
                                     values=[total_physical, total_knowledge, total_mental],
                                     hole=.3)])  # 도넛 모양

    fig_donut.update_layout(title='누적 점수 비율')

    # 누적 스타 차트 생성 (선택된 날짜까지 또는 전체 데이터)
    fig_radar = go.Figure(data=go.Scatterpolar(
        r=[total_physical, total_knowledge, total_mental],
        theta=['Physical', 'Knowledge', 'Mental'],
        fill='toself'
    ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        title='누적 점수 스타 차트'
    )

    return fig_cumulative, fig_donut, fig_radar, date_range


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