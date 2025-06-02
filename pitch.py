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

def show_pitch(uploaded_data=None):
    st.header("📈 Pitch Analysis")

    # --- 기존 summary 파일 로드 ---
    def load_summary_data():
        data_dir = "data/normal/summary"
        file_list = glob.glob(os.path.join(data_dir, "summary_pitch_tilt_set[0-5].csv"))

        combined_df = pd.DataFrame()
        for file in file_list:
            df = pd.read_csv(file)
            df['file'] = os.path.basename(file).split('.')[0]
            df.rename(columns={
                'position_bin_pitch_tilt': 'position_bin',
                'mean_pitch': 'pitch',
                'mean_tilt': 'tilt'
            }, inplace=True)
            combined_df = pd.concat([combined_df, df[['position_bin', 'pitch', 'tilt', 'file']]], ignore_index=True)

        return combined_df

    combined_df = load_summary_data()

    # --- 기본 그래프 생성 ---
    fig = go.Figure()

    for fname in combined_df['file'].unique():
        file_data = combined_df[combined_df['file'] == fname]
        fig.add_trace(go.Scatter(
            x=file_data['position_bin'],
            y=file_data['pitch'],
            mode='lines',
            name=fname,
            line=dict(width=1, color='rgba(100,100,100,1)'),
            visible='legendonly'
        ))

        # tilt band
        fig.add_trace(go.Scatter(
            x=file_data['position_bin'],
            y=file_data['pitch'] + file_data['tilt'],
            mode='lines',
            line=dict(width=0),
            name=fname + ' (upper)',
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=file_data['position_bin'],
            y=file_data['pitch'] - file_data['tilt'],
            fill='tonexty',
            mode='lines',
            line=dict(width=0),
            name=fname + ' (lower)',
            fillcolor='rgba(100,100,100,0.1)',
            showlegend=False
        ))

    # --- 업로드 파일 처리 ---
    if uploaded_data and len(uploaded_data) >= 9:
        uploaded_combined = pd.DataFrame()

        for i, df in enumerate(uploaded_data):
            df = df.copy()
            df['file'] = f"uploaded_{i}"
            if 'tilt' in df.columns:
                df.rename(columns={'tilt': 'cumulative_tilt'}, inplace=True)
            if 'pitch' in df.columns:
                df.rename(columns={'pitch': 'cumulative_pitch'}, inplace=True)

            if 'position' in df.columns:
                df['position_bin'] = df['position']

            uploaded_combined = pd.concat([
                uploaded_combined,
                df[['position_bin', 'cumulative_pitch', 'cumulative_tilt', 'file']]
            ], ignore_index=True)

        mean_pitch = uploaded_combined.groupby('position_bin')['cumulative_pitch'].mean()
        std_pitch = uploaded_combined.groupby('position_bin')['cumulative_pitch'].std()
        mean_tilt = uploaded_combined.groupby('position_bin')['cumulative_tilt'].mean()

        fig.add_trace(go.Scatter(
            x=mean_pitch.index,
            y=mean_pitch.values,
            mode='lines',
            name='업로드 평균 pitch',
            line=dict(width=2, color='firebrick')
        ))

        fig.add_trace(go.Scatter(
            x=mean_pitch.index,
            y=mean_pitch + mean_tilt,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=mean_pitch.index,
            y=mean_pitch - mean_tilt,
            fill='tonexty',
            mode='lines',
            line=dict(width=0),
            name='업로드 tilt 범위',
            fillcolor='rgba(255,0,0,0.1)'
        ))

    # --- 시각화 출력 ---
    fig.update_layout(
        title="Pitch with Tilt Band",
        xaxis_title="Position Bin",
        yaxis_title="Pitch",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)


    # ✅ 업로드 데이터 수에 대한 메시지
    if uploaded_data is None or len(uploaded_data) == 0:
        st.warning("📂 왼쪽 사이드바에서 CSV 파일을 업로드하세요.")
    elif len(uploaded_data) < 9:
        st.warning(f"⚠️ 데이터 부족: 업로드된 데이터가 9개 미만입니다. (현재 업로드:{len(uploaded_data)}개)")
    else:
        st.success("✅ 데이터 충분: 업로드 평균 피치를 그래프에 추가했습니다.")