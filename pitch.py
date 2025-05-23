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

    # 대표 하나의 평균곡선만 그리되, tilt로 굵기 표현
    mean_df = combined_df.groupby('position_bin').agg({
        'cumulative_pitch': 'mean',
        'tilt': 'mean'
    }).reset_index()

    # 각 점을 선분으로 연결하면서 굵기 표현
    for i in range(len(mean_df) - 1):
        fig.add_trace(go.Scatter(
            x=[mean_df.loc[i, 'position_bin'], mean_df.loc[i + 1, 'position_bin']],
            y=[mean_df.loc[i, 'cumulative_pitch'], mean_df.loc[i + 1, 'cumulative_pitch']],
            mode='lines',
            line=dict(
                color='royalblue',
                width=max(1, min(10, mean_df.loc[i, 'tilt'] * 10))  # tilt 기준 굵기 제한 (1~10)
            ),
            showlegend=False
        ))

    # 범례용 평균 선 (보이게만)
    fig.add_trace(go.Scatter(
        x=mean_df['position_bin'],
        y=mean_df['cumulative_pitch'],
        mode='lines',
        name='Mean Cumulative Pitch (Width = Tilt)',
        line=dict(color='royalblue', width=3, dash='dot')
    ))

    fig.update_layout(
        title='📈 Cumulative Pitch (Line Width = Tilt)',
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