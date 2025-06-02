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


        combined_tilt_list = []
        for df in uploaded_data:
            df['position_bin'] = (df['position'] / 1).round() * 1
            df = df[(df['position_bin'] >= 0) & (df['position_bin'] <= 220)]
            if 'tilt' in df.columns:
                combined_tilt_list.append(df[['position_bin', 'tilt']])

        tilt_band_uploaded = None
        if combined_tilt_list:
            df_uploaded_tilt_all = pd.concat(combined_tilt_list, axis=0)
            tilt_mean_uploaded = df_uploaded_tilt_all.groupby('position_bin')['tilt'].mean().reset_index(name='tilt_mean')
            pitch_mean_uploaded = pitch_mean_uploaded.rename(columns={'cumulative_pitch': 'pitch_mean'})
            uploaded_merged = pd.merge(pitch_mean_uploaded, tilt_mean_uploaded, on='position_bin', how='inner')
            uploaded_merged['tilt_upper'] = uploaded_merged['pitch_mean'] + uploaded_merged['tilt_mean'] * 0.25
            uploaded_merged['tilt_lower'] = uploaded_merged['pitch_mean'] - uploaded_merged['tilt_mean'] * 0.25
        else:
            uploaded_merged = pitch_mean_uploaded.copy()
            
            
            
            
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
            y=pitch_mean_uploaded['pitch_mean'],
            mode='lines',
            name='Uploaded Data Mean Pitch',
            line=dict(color='Green', width=1.5, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=uploaded_merged['position_bin'],
            y=uploaded_merged.get('tilt_upper', [None]*len(uploaded_merged)),
            mode='lines',
            name='Uploaded Tilt Upper',
            line=dict(width=0),
            fillcolor='rgba(144, 238, 144, 0.4)',
            showlegend=False
        ))

        fig.add_trace(go.Scatter(
            x=uploaded_merged['position_bin'],
            y=uploaded_merged.get('tilt_lower', [None]*len(uploaded_merged)),
            mode='lines',
            name='Uploaded Tilt Lower',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(144, 238, 144, 0.4)',
            showlegend=True
        ))

    # --- 레이아웃 ---
    fig.update_layout(
        title='🎯 Cumulative Pitch (Mean) with Tilt Band',
        xaxis_title='Position (m)',
        yaxis_title='Pitch',
        width=900,
        height=500,
        xaxis=dict(range=[-5, 225]),
        yaxis=dict(range=[-0.04, 0.06]),
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

    if uploaded_data is not None and len(uploaded_data) >= 9:

        # 1. 구간 범위 (0~220, 20 단위)
        bins = list(range(0, 221, 20))

        # 2. Summary 데이터 구간별 tilt 평균과 std 계산
        summary_df = load_summary_data()
        summary_df = summary_df[(summary_df['position_bin'] >= 0) & (summary_df['position_bin'] <= 220)]

        # 구간별로 position_bin을 20단위로 그룹핑하기 위한 열 생성
        summary_df['bin_group'] = pd.cut(summary_df['position_bin'], bins=bins, right=False, include_lowest=True)

        summary_group = summary_df.groupby('bin_group')['tilt'].agg(['mean', 'std']).reset_index()

        # 3. 업로드된 데이터 tilt 평균 구간별 계산
        combined_tilt_list = []
        for df in uploaded_data:
            df['position_bin'] = (df['position'] / 1).round() * 1
            df = df[(df['position_bin'] >= 0) & (df['position_bin'] <= 220)]
            if 'tilt' in df.columns:
                combined_tilt_list.append(df[['position_bin', 'tilt']])

        df_uploaded_tilt_all = pd.concat(combined_tilt_list, axis=0)
        df_uploaded_tilt_all['bin_group'] = pd.cut(df_uploaded_tilt_all['position_bin'], bins=bins, right=False, include_lowest=True)

        # 구간별 업로드 데이터 tilt 평균 계산 (파일별 평균 필요시 추가 가능)
        uploaded_group_mean = df_uploaded_tilt_all.groupby(['bin_group', 'position_bin']).mean().reset_index()
        # 여기선 단순 구간별 tilt 평균 (전체 평균)로 사용
        uploaded_bin_mean = df_uploaded_tilt_all.groupby('bin_group')['tilt'].mean().reset_index()

        # 4. 이상치 탐지: 업로드 tilt 평균이 summary 평균 ± 3*std 벗어나는 구간 찾기
        abnormal_bins = []
        for idx, row in uploaded_bin_mean.iterrows():
            bin_label = row['bin_group']
            upload_mean_tilt = row['tilt']
            summary_stats = summary_group[summary_group['bin_group'] == bin_label]

            if not summary_stats.empty:
                mean_tilt = summary_stats['mean'].values[0]
                std_tilt = summary_stats['std'].values[0]
                if pd.isna(std_tilt) or std_tilt == 0:
                    std_tilt = 1e-6  # 0일 때 나누기 방지용 아주 작은 수

                upper_limit = mean_tilt + 3 * std_tilt
                lower_limit = mean_tilt - 3 * std_tilt

                if upload_mean_tilt > upper_limit or upload_mean_tilt < lower_limit:
                    # 이상치 구간 기록 (bin 시작값, 이상치 개수는 대략 1개 이상으로 임의 설정 가능)
                    bin_start = bins[idx]
                    # 이상치 개수는 간단히 1로 처리 (정확히는 파일별 이상 개수 집계 필요 시 로직 추가)
                    abnormal_bins.append((bin_start, 1))
                    
        # 5) 이상치 메시지 출력 (전체 구간은 11개 구간으로 나누어 검사)
        if abnormal_bins:
            detected_bins = len(abnormal_bins)
            msg_lines = [f"🚨 이상 예측 구간 발견: 11개 구간 중 {detected_bins}개 구간"]
            total_files = len(uploaded_data)

            for bin_start, count, max_deviation in abnormal_bins:
                percent = (count / total_files) * 100
                msg_lines.append(
                    f"- 구간 {bin_start}~{bin_start + 19} m: 총 {total_files}개 중 {count}개 상한선 초과 "
                    f"({percent:.1f}%), 최대 초과량: {max_deviation:.2f}"
                )
            st.error("\n".join(msg_lines))
        else:
            st.success("✅ 이상 예측 구간 없음")