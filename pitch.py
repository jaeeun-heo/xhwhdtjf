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

def show_pitch(uploaded_data=None):
    # ✅ 기본 summary 데이터 불러오기
    summary_df = load_summary_data()

    # ✅ 유효 범위로 필터링
    summary_df = summary_df[(summary_df['position_bin'] >= 0.0) & (summary_df['position_bin'] <= 220)]

    # ✅ 평균 계산
    pitch_df = summary_df.groupby('position_bin')['pitch'].mean().reset_index(name='pitch_mean').round(3)
    tilt_df = summary_df.groupby('position_bin')['tilt'].mean().reset_index(name='tilt_mean').round(3)

    merged_df = pd.merge(pitch_df, tilt_df, on='position_bin')
    scale = 0.25
    merged_df['tilt_upper'] = merged_df['pitch_mean'] + merged_df['tilt_mean'] * scale
    merged_df['tilt_lower'] = merged_df['pitch_mean'] - merged_df['tilt_mean'] * scale

    # ✅ 업로드된 데이터 평균 추가 계산 (있고, 9개 이상일 때만)
    pitch_mean_uploaded = None
    if uploaded_data is not None and len(uploaded_data) >= 9:
        combined_df_list = []
        for df in uploaded_data:
            df['position_bin'] = (df['position'] / 1).round() * 1
            df = df[(df['position_bin'] >= 0) & (df['position_bin'] <= 220)]
            combined_df_list.append(df[['position_bin', 'cumulative_pitch']])

        df_uploaded_all = pd.concat(combined_df_list, axis=0)
        pitch_mean_uploaded = df_uploaded_all.groupby('position_bin')['cumulative_pitch'].mean().reset_index()

    # ✅ 그래프 그리기
    fig = go.Figure()

    # --- 개별 summary 파일들 (토글로 숨김 처리) ---
    with st.expander("📁 개별 Summary 파일 보기 (Toggle)", expanded=False):
        for fname in summary_df['file'].unique():
            file_data = summary_df[summary_df['file'] == fname]
            fig.add_trace(go.Scatter(
                x=file_data['position_bin'],
                y=file_data['pitch'],
                mode='lines',
                name=fname,
                line=dict(width=1, color='rgba(100,100,100,1)'),
                visible='legendonly'
            ))

    # --- 평균 pitch ---
    fig.add_trace(go.Scatter(
        x=merged_df['position_bin'],
        y=merged_df['pitch_mean'],
        mode='lines',
        name='Pitch Mean',
        line=dict(color='lightskyblue', width=2.5)
    ))

    # --- Tilt 음영 영역 ---
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
        fill='tonexty',
        fillcolor='rgba(123, 104, 238, 0.6)',
        showlegend=True
    ))

    # --- 업로드 데이터 결과 겹쳐 그리기 ---
    if pitch_mean_uploaded is not None:
        fig.add_trace(go.Scatter(
            x=pitch_mean_uploaded['position_bin'],
            y=pitch_mean_uploaded['cumulative_pitch'],
            mode='lines',
            name='Uploaded Data Mean Pitch',
            line=dict(color='red', width=2, dash='dash')
        ))

    # --- 레이아웃 ---
    fig.update_layout(
        title='🎯 Cumulative Pitch (Mean) with Tilt Band',
        xaxis_title='Position (m)',
        yaxis_title='Pitch',
        width=900,
        height=500,
        xaxis=dict(range=[-5, 225]),
        yaxis=dict(range=[-0.03, 0.03]),
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

    # ✅ 출력
    st.plotly_chart(fig, use_container_width=True)

    # ✅ 업로드 데이터 수에 대한 메시지
    if uploaded_data is None or len(uploaded_data) == 0:
        st.warning("📂 왼쪽 사이드바에서 CSV 파일을 업로드하세요.")
    elif len(uploaded_data) < 9:
        st.warning(f"⚠️ 데이터 부족: 업로드된 데이터가 9개 미만입니다. (현재 업로드:{len(uploaded_data)}개)")
    else:
        st.success("✅ 데이터 충분: 업로드 평균 피치를 그래프에 추가했습니다.")