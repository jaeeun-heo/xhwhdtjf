import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from PIL import Image
import os
import glob

def show_pitch():

    # 1. 파일 로딩
    data_dir = "data/demo_add"
    file_list = glob.glob(os.path.join(data_dir, "demo_*_add.csv"))

    combined_df = pd.DataFrame()

    for file in file_list:
        df = pd.read_csv(file)
        df['file'] = os.path.basename(file).split('.')[0]
        if 'position' in df.columns and 'cumulative_pitch' in df.columns:
            df['position_bin'] = (df['position'] / 0.1).round() * 0.1
            combined_df = pd.concat([combined_df, df[['position', 'cumulative_pitch', 'position_bin', 'file']]], ignore_index=True)



    # 2. 범위 필터 (예: position 0~2.5m)
    combined_df = combined_df[(combined_df['position'] >= 0) & (combined_df['position'] <= 2.5)]

    # 3. 그룹별 요약 계산 (평균, 최대, 최소)
    mean_df = combined_df.groupby('position_bin')['cumulative_pitch'].mean().reset_index()
    max_df = combined_df.groupby('position_bin')['cumulative_pitch'].max().reset_index()
    min_df = combined_df.groupby('position_bin')['cumulative_pitch'].min().reset_index()

    # 4. Plotly 그래프 생성
    fig = go.Figure()

    # 개별 파일 데이터 (legendonly, alpha 0.35 효과는 색상 opacity로 표현)
    for fname in combined_df['file'].unique():
        file_data = combined_df[combined_df['file'] == fname]
        fig.add_trace(go.Scatter(
            x=file_data['position'],
            y=file_data['cumulative_pitch'],
            mode='lines',
            name=fname,
            line=dict(width=1, color='rgba(100,100,100,0.8)'),
            visible='legendonly'
        ))

    # 평균선 추가
    fig.add_trace(go.Scatter(
        x=mean_df['position_bin'],
        y=mean_df['cumulative_pitch'],
        mode='lines',
        name='Mean Pitch',
        line=dict(color='red', width=3)
    ))

    # 최대선 추가
    fig.add_trace(go.Scatter(
        x=max_df['position_bin'],
        y=max_df['cumulative_pitch'],
        mode='lines',
        name='Max Pitch',
        line=dict(color='green', width=1, dash='dash')
    ))

    # 최소선 추가
    fig.add_trace(go.Scatter(
        x=min_df['position_bin'],
        y=min_df['cumulative_pitch'],
        mode='lines',
        name='Min Pitch',
        line=dict(color='green', width=1, dash='dash')
    ))

    # 고점-저점 음영 (Fill_between 효과 - Plotly에서는 Scatter + fill='tonexty' 사용)
    fig.add_trace(go.Scatter(
        x=max_df['position_bin'],
        y=max_df['cumulative_pitch'],
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=min_df['position_bin'],
        y=min_df['cumulative_pitch'],
        mode='lines',
        fill='tonexty',
        fillcolor='rgba(0,255,0,0.1)',
        line=dict(width=0),
        name='Max-Min Range',
        hoverinfo='skip'
    ))

    fig.update_layout(
        title='📈 Pitch Summary by Position',
        xaxis_title='Position (m)',
        yaxis_title='Cumulative Pitch',
        width=900,
        height=500,
        xaxis=dict(range=[0, 2.6]),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.3,
            xanchor='center',
            x=0.5
        ),
        template='plotly_white',
        margin=dict(b=80)
    )

    st.plotly_chart(fig, use_container_width=True)