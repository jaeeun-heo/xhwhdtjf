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
        if 'position' in df.columns and 'cumulative_pitch' in df.columns and 'tilt' in df.columns:
            df['position_bin'] = (df['position'] / 0.1).round() * 0.1
            combined_df = pd.concat([
                combined_df,
                df[['position', 'cumulative_pitch', 'tilt', 'position_bin', 'file']]
            ], ignore_index=True)

    # 2. 분석 범위 필터링
    combined_df = combined_df[(combined_df['position'] >= 0) & (combined_df['position'] <= 2.5)]

    # 3. Plotly 그래프 생성
    fig = go.Figure()

    # 개별 파일의 pitch/tilt (투명도 적용, legendonly)
    for fname in combined_df['file'].unique():
        file_data = combined_df[combined_df['file'] == fname]

        # cumulative_pitch
        fig.add_trace(go.Scatter(
            x=file_data['position'],
            y=file_data['cumulative_pitch'],
            mode='lines',
            name=f"{fname} - cumulative_pitch",
            line=dict(width=1, color='rgba(100,100,200,0.4)'),
            visible='legendonly'
        ))

        # tilt
        fig.add_trace(go.Scatter(
            x=file_data['position'],
            y=file_data['tilt'],
            mode='lines',
            name=f"{fname} - tilt",
            line=dict(width=1, color='rgba(200,100,100,0.4)', dash='dot'),
            visible='legendonly'
        ))

    # 평균선 계산
    mean_pitch = combined_df.groupby('position_bin')['cumulative_pitch'].mean().reset_index(name='mean_pitch')
    mean_tilt = combined_df.groupby('position_bin')['tilt'].mean().reset_index(name='mean_tilt')

    # 평균선 추가
    fig.add_trace(go.Scatter(
        x=mean_pitch['position_bin'],
        y=mean_pitch['mean_pitch'],
        mode='lines',
        name="Mean Cumulative Pitch",
        line=dict(color='royalblue', width=3)
    ))

    fig.add_trace(go.Scatter(
        x=mean_tilt['position_bin'],
        y=mean_tilt['mean_tilt'],
        mode='lines',
        name="Mean Tilt",
        line=dict(color='tomato', width=3, dash='dash')
    ))

    # 레이아웃 설정
    fig.update_layout(
        title="📈 Cumulative Pitch & Tilt Summary by Position",
        xaxis_title="Position (m)",
        yaxis_title="Value",
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