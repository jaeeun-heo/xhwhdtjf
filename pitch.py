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

    # 2. 유효 구간 필터링
    combined_df = combined_df[(combined_df['position'] >= 0) & (combined_df['position'] <= 2.5)]

    # 3. position_bin 별 평균 계산
    mean_df = combined_df.groupby('position_bin').agg({
        'cumulative_pitch': 'mean',
        'tilt': 'mean'
    }).reset_index()

    # 상하한 계산
    mean_df['upper'] = mean_df['cumulative_pitch'] + mean_df['tilt']
    mean_df['lower'] = mean_df['cumulative_pitch'] - mean_df['tilt']

    # 4. Plotly 그래프 생성
    fig = go.Figure()

    # (1) tilt 영역: 상한/하한을 채운 band
    fig.add_trace(go.Scatter(
        x=pd.concat([mean_df['position_bin'], mean_df['position_bin'][::-1]]),
        y=pd.concat([mean_df['upper'], mean_df['lower'][::-1]]),
        fill='toself',
        fillcolor='rgba(0, 100, 255, 0.2)',  # pitch 색과 어울리게
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name='Tilt Band'
    ))

    # (2) pitch 평균선
    fig.add_trace(go.Scatter(
        x=mean_df['position_bin'],
        y=mean_df['cumulative_pitch'],
        mode='lines',
        name='Cumulative Pitch',
        line=dict(color='royalblue', width=3)
    ))

    # 5. 레이아웃
    fig.update_layout(
        title='📈 Cumulative Pitch with Tilt Band',
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