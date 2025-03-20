import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit as st

def create_visualizations(df):
    """데이터프레임을 기반으로 다양한 시각화 생성"""
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 1. 선 그래프 (시간에 따른 능력치 변화)
    fig_line = px.line(df, x='timestamp', y=['physical', 'knowledge', 'mental'], title='능력치 변화 추이')

    # 2. 막대 그래프 (일별 능력치 비교)
    fig_bar = px.bar(df, x='timestamp', y=['physical', 'knowledge', 'mental'], title='일별 능력치 비교')

    # 3. 워드 클라우드 (user_input 빈도 분석)
    text = ' '.join(df['user_input'].tolist())
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(8, 4))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    img_wordcloud = BytesIO()
    plt.savefig(img_wordcloud, format='png')
    img_wordcloud_base64 = base64.b64encode(img_wordcloud.getvalue()).decode('utf-8')
    plt.close()

    # 4. 히트맵 (능력치 상관관계)
    corr_matrix = df[['physical', 'knowledge', 'mental']].corr()
    fig_heatmap = go.Figure(data=go.Heatmap(z=corr_matrix.values, x=corr_matrix.columns, y=corr_matrix.index, colorscale='Viridis'))

    return fig_line, fig_bar, img_wordcloud_base64, fig_heatmap