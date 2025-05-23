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

    # 2. 유효한 구간으로 자르기
    combined_df = combined_df[(combined_df['position'] >= 0) & (combined_df['position'] <= 2.5)]

    # 3. 평균 pitch 및 tilt 계산
    pitch_df = combined_df.groupby('position_bin')['cumulative_pitch'].mean().reset_index(name='pitch_mean').round(3)
    tilt_df = combined_df.groupby('position_bin')['tilt'].mean().reset_index(name='tilt_mean').round(3)

    merged_df = pd.merge(pitch_df, tilt_df, on='position_bin')
    merged_df['tilt_upper'] = merged_df['pitch_mean'] + merged_df['tilt_mean'] / 2
    merged_df['tilt_lower'] = merged_df['pitch_mean'] - merged_df['tilt_mean'] / 2

    # 4. Plotly 그래프 생성
    fig = go.Figure()

    # 개별 파일 데이터는 생략 가능 (필요시 아래 주석 해제)
    # for fname in combined_df['file'].unique():
    #     file_data = combined_df[combined_df['file'] == fname]
    #     fig.add_trace(go.Scatter(
    #         x=file_data['position'],
    #         y=file_data['cumulative_pitch'],
    #         mode='lines',
    #         name=fname,
    #         line=dict(width=1, color='rgba(100,100,100,0.4)'),
    #         visible='legendonly'
    #     ))

    # 평균 pitch 선 추가
    fig.add_trace(go.Scatter(
        x=merged_df['position_bin'],
        y=merged_df['pitch_mean'],
        mode='lines',
        name='Cumulative Pitch (Mean)',
        line=dict(color='mediumslateblue', width=3)
    ))

    # tilt 기반 상하한 범위 영역 추가
    fig.add_trace(go.Scatter(
        x=merged_df['position_bin'],
        y=merged_df['tilt_upper'],
        mode='lines',
        name='Tilt Upper',
        line=dict(color='mediumslateblue', width=0),
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=merged_df['position_bin'],
        y=merged_df['tilt_lower'],
        mode='lines',
        name='Tilt Lower',
        line=dict(color='mediumslateblue', width=0),
        fill='tonexty',  # 상하 사이 영역을 채움
        fillcolor='rgba(123, 104, 238, 0.3)',  # mediumslateblue with alpha
        showlegend=True
    ))

    # 레이아웃 설정
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

    # Streamlit 출력
    st.plotly_chart(fig, use_container_width=True)