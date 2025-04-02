import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import datetime

def create_dash_app(app):
    """Dash 앱을 생성하고 레이아웃과 콜백 함수를 정의합니다."""
    background_color = '#fcfcfc'
    
    dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dashboard/')

    # 레이아웃 정의
    dash_app.layout = html.Div([
        html.H1("상태 변화 시각화"),
        dcc.DatePickerSingle(
            id='date-picker',
            display_format='YYYY-MM-DD'  # 날짜 표시 형식 변경
        ),
        html.Div(id='date-range-display'),  # 선택된 날짜 범위 표시
        dcc.Graph(id="bar-chart", style={'width': '100%', 'height': '400px'}),  # 막대 그래프 추가
        dcc.Graph(id="cumulative-plot", style={'width': '100%', 'height': '400px'}),  # 누적 선 그래프
        html.Div([  # 도넛 차트와 스타 차트를 감싸는 div 추가
            dcc.Graph(id="donut-chart", style={'width': '100%', 'display': 'inline-block'}),  # 도넛 차트
            dcc.Graph(id="radar-chart", style={'width': '100%', 'display': 'block'})  # 스타 차트를 아래로 내림
        ])
    ], style={'backgroundColor': background_color})  # 대시보드 배경 색상 설정

    # 콜백 함수 정의
    @dash_app.callback(
        Output("bar-chart", "figure"),
        Output("cumulative-plot", "figure"),
        Output("donut-chart", "figure"),
        Output("radar-chart", "figure"),
        Output("date-range-display", "children"),
        Output("date-picker", "date"),  # 날짜 선택기 기본값 설정 추가
        Input("date-picker", "date")
    )
    def update_graph(selected_date):
        # 데이터베이스 연결
        conn = sqlite3.connect('database.db')
        query = "SELECT physical, knowledge, mental, timestamp FROM logs"
        df = pd.read_sql_query(query, conn)
        conn.close()

        # timestamp를 datetime 형식으로 변환
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # 가장 최근 날짜 설정
        latest_date = df['timestamp'].max().date()

        # 선택된 날짜를 기준으로 1주일 전까지의 데이터 필터링
        if selected_date:
            end_date = pd.to_datetime(selected_date).date()
            start_date = end_date - datetime.timedelta(days=6)
            filtered_df = df[(df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)]
            date_range = f"{start_date} ~ {end_date}"
        else:
            # 페이지 처음 로딩 시 가장 최근 날짜로 설정
            selected_date = latest_date
            end_date = pd.to_datetime(selected_date).date()
            start_date = end_date - datetime.timedelta(days=6)
            filtered_df = df[(df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)]
            date_range = f"{start_date} ~ {end_date}"

        # 막대 그래프 생성
        bar_data = filtered_df[filtered_df['timestamp'].dt.date == pd.to_datetime(selected_date).date()]
        if not bar_data.empty:
            fig_bar = go.Figure(data=[
                go.Bar(x=['Physical', 'Knowledge', 'Mental'], y
                       =[bar_data['physical'].values[0], 
                         bar_data['knowledge'].values[0], 
                         bar_data['mental'].values[0]], 
                       marker_color=['#98ddde', '#d99694', '#b3de69'])
            ])
            fig_bar.update_layout(title=f"{selected_date}"+"\n"+ "일일 성장 변화", 
                                  yaxis=dict(tickvals=[0, 1, 2], 
                                             ticktext=['0', '1', '2'],
                                             range=[0, 2])) # y 라벨 변경
        else:
            fig_bar = go.Figure(data=[go.Bar(x=[], y=[])])
        
        
        # 그래프 및 배경 색상 설정
        background_color = '#fcfcfc'
        # 막대 그래프 배경 색상 설정
        fig_bar.update_layout(
            plot_bgcolor=background_color,
            paper_bgcolor=background_color
        )

        # 누적 합계 계산 (선택된 날짜까지 또는 전체 데이터)
        df_cumsum = filtered_df.set_index('timestamp').cumsum().reset_index()

        # Plotly 누적 선 그래프 생성
        fig_cumulative = go.Figure()
        fig_cumulative.add_trace(go.Scatter(x=df_cumsum['timestamp'], y=df_cumsum['physical'], mode='lines+markers', name='Physical', marker_color='#98ddde'))
        fig_cumulative.add_trace(go.Scatter(x=df_cumsum['timestamp'], y=df_cumsum['knowledge'], mode='lines+markers', name='Knowledge', marker_color='#d99694'))
        fig_cumulative.add_trace(go.Scatter(x=df_cumsum['timestamp'], y=df_cumsum['mental'], mode='lines+markers', name='Mental', marker_color='#b3de69'))

        fig_cumulative.update_layout(title='일주일 변화 살펴보기', xaxis_title='Date', yaxis_title='Score', xaxis=dict(tickformat='%Y-%m-%d'), xaxis_tickangle=-45) # x축 라벨 형식 변경

        # 누적 선 그래프 배경 및 그리드 제거
        fig_cumulative.update_layout(
            plot_bgcolor=background_color,
            paper_bgcolor=background_color,
            yaxis=dict(showgrid=False),
            xaxis=dict(showgrid=False)
        )

        # 누적 도넛 차트 생성 (선택된 날짜까지 또는 전체 데이터)
        total_physical = filtered_df['physical'].sum()
        total_knowledge = filtered_df['knowledge'].sum()
        total_mental = filtered_df['mental'].sum()

        fig_donut = go.Figure(data=[go.Pie(labels=['Physical', 'Knowledge', 'Mental'],
                                         values=[total_physical, total_knowledge, total_mental],
                                         hole=.3,
                                         marker_colors=['#98ddde', '#d99694', '#b3de69'],
                                         texttemplate='%{value}점')])

        fig_donut.update_layout(title='지덕체 비교해보기1')

        # 누적 도넛 차트 배경 색상 설정
        fig_donut.update_layout(
            plot_bgcolor=background_color,
            paper_bgcolor=background_color
        )

        # 누적 스타 차트 생성 (선택된 날짜까지 또는 전체 데이터)
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=[total_physical, total_knowledge, total_mental],
            theta=['Physical', 'Knowledge', 'Mental'],
            fill='toself',
            marker_color=['#98ddde', '#d99694', '#b3de69']
        ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=False,
            title='지덕체 비교해보기2'
        )

        # 누적 스타 차트 배경 색상 설정
        fig_radar.update_layout(
            plot_bgcolor='#fcfcfc',
            paper_bgcolor='#fcfcfc'
        )

        return fig_bar, fig_cumulative, fig_donut, fig_radar, date_range, latest_date

    return dash_app