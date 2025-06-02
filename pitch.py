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

    # 1. summary_pitch_tilt_set 파일들 로딩
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


    # 2. 유효한 구간으로 자르기 (0~2.5m 기준, 0.1 bin당 25개 구간)
    combined_df = combined_df[(combined_df['position_bin'] >= 0.0) & (combined_df['position_bin'] <= 220)]

    # 3. 평균 pitch 및 tilt 계산
    pitch_df = combined_df.groupby('position_bin')['pitch'].mean().reset_index(name='pitch_mean').round(3)
    tilt_df = combined_df.groupby('position_bin')['tilt'].mean().reset_index(name='tilt_mean').round(3)

    merged_df = pd.merge(pitch_df, tilt_df, on='position_bin')
    scale = 0.25  # tilt 스케일 조정
    merged_df['tilt_upper'] = merged_df['pitch_mean'] + merged_df['tilt_mean'] * scale
    merged_df['tilt_lower'] = merged_df['pitch_mean'] - merged_df['tilt_mean'] * scale




## 업로드 파일 9개 이상이면 pitch, tilt 그리기
    pitch_mean_uploaded = None
    if uploaded_data is not None and len(uploaded_data) >= 9:
        combined_df_list = []
        for df in uploaded_data:
            # position_bin 처리 (1단위 반올림)
            df['position_bin'] = (df['position'] / 1).round() * 1
            # 범위 필터링
            df = df[(df['position_bin'] >= 0) & (df['position_bin'] <= 220)]
            combined_df_list.append(df[['position_bin', 'cumulative_pitch']])
        combined_uploaded_df = pd.concat(combined_df_list, axis=0)
        pitch_mean_uploaded = combined_uploaded_df.groupby('position_bin')['cumulative_pitch'].mean().reset_index()

    # 4. Plotly 그래프 생성
    fig = go.Figure()

    # --- 개별 summary 파일 토글 ---
    with st.expander("📁 개별 Summary 파일 보기 (Toggle)", expanded=False):
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

    # 평균 pitch 선 추가
    fig.add_trace(go.Scatter(
        x=merged_df['position_bin'],
        y=merged_df['pitch_mean'],
        mode='lines',
        name='Pitch Mean',
        line=dict(color='lightskyblue', width=2.5)
    ))

    # Tilt 음영 영역 추가
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
    
    
    # 업로드 데이터가 있으면 같은 그래프에 추가 (항상 보임, 토글 없음)
    if uploaded_data is not None:
        fig.add_trace(go.Scatter(
            x=pitch_mean_uploaded['position_bin'],
            y=pitch_mean_uploaded['cumulative_pitch'],
            mode='lines',
            name='Uploaded Data Mean Pitch',
            line=dict(color='red', width=2, dash='dash')
        ))
            
    # 레이아웃 설정
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

    # 5. Streamlit 출력
    st.plotly_chart(fig, use_container_width=True)

# ------------------
    # 1) 업로드 데이터 9개인지 확인
    if uploaded_data is None or len(uploaded_data) == 0:
        st.warning("📂 왼쪽 사이드바에서 CSV 파일을 업로드하세요.")
        return
    elif len(uploaded_data) < 9:
        st.warning(f"⚠️ 데이터 부족: 업로드된 데이터가 9개 미만입니다. (현재 업로드:{len(uploaded_data)}개)")
        return
    else:
        st.success("✅ 데이터 충분: 분석을 시행합니다.")