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

def show_gyro(uploaded_data=None):

    # 1. 파일 로딩
    data_dir = "data/normal/summary"
    file_list = glob.glob(os.path.join(data_dir, "summary_gyro_set[0-5].csv"))
    combined_df = pd.DataFrame()

    for file in file_list:
        df = pd.read_csv(file)
        df['file'] = os.path.basename(file).split('.')[0]
        df.rename(columns={
            'position_bin_gyro': 'position_bin',
            'mean_gyro': 'mean',
            'upper_bound_gyro': 'upper'
        }, inplace=True)
        combined_df = pd.concat([combined_df, df[['position_bin', 'mean', 'upper', 'file']]], ignore_index=True)

    # 2. 필터링
    combined_df = combined_df[(combined_df['position_bin'] >= 0) & (combined_df['position_bin'] <= 220)]

    # 3. Plotly 그래프 생성
    fig = go.Figure()

    # 개별 summary 파일 데이터 (legendonly)
    for fname in combined_df['file'].unique():
        file_data = combined_df[combined_df['file'] == fname]
        fig.add_trace(go.Scatter(
            x=file_data['position_bin'],
            y=file_data['mean'],
            mode='lines',
            name=f"{fname} (mean)",
            line=dict(width=1, color='rgba(135, 206, 235, 0.8)'),
            visible='legendonly'
        ))
        fig.add_trace(go.Scatter(
            x=file_data['position_bin'],
            y=file_data['upper'],
            mode='lines',
            name=f"{fname} (upper)",
            line=dict(width=1, color='rgba(255, 165, 0, 0.8)', dash='dash'),
            visible='legendonly'
        ))
    

    # 평균선 추가
    mean_df = combined_df.groupby('position_bin')['mean'].mean().reset_index()
    fig.add_trace(go.Scatter(
        x=mean_df['position_bin'],
        y=mean_df['mean'],
        mode='lines',
        name='Mean Gyro',
        line=dict(color='skyblue', width=3)
    ))

    # Upper Bound 추가
    upper_df = combined_df.groupby('position_bin')['upper'].mean().reset_index()
    fig.add_trace(go.Scatter(
        x=upper_df['position_bin'],
        y=upper_df['upper'],
        mode='lines',
        name='Upper Bound (IQR)',
        line=dict(color='orange', width=2, dash='dash')
    ))

    # 업로드 데이터가 있으면 같은 그래프에 추가 (항상 보임, 토글 없음)
    if uploaded_data is not None:
        for i, df in enumerate(uploaded_data):
            label = df.attrs.get('filename', f'Uploaded {i+1}')
            fig.add_trace(go.Scatter(
                x=df['position'],   # position 그대로 사용 (필요시 버킷 처리 가능)
                y=df['gyro'],
                mode='lines',
                name=label,
                line=dict(width=1, dash='dot'),
                opacity=0.7
            ))

    fig.update_layout(
        title='📈 Gyro Summary by Position (from Summary Files)',
        xaxis_title='Position (m)',
        yaxis_title='Gyro',
        width=900,
        height=500,
        xaxis=dict(range=[-5, 225]),
        yaxis=dict(range=[0, 0.8]),
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

    # 4. 표 생성 (0.5m 구간별 요약)
    combined_df['range'] = (combined_df['position_bin'] // 20) * 20
    iqr_summary = combined_df.groupby('range')['upper'].mean()
    mean_summary = combined_df.groupby('range')['mean'].mean()

    overall_iqr = iqr_summary.mean()
    overall_mean = mean_summary.mean()

    range_labels = sorted(iqr_summary.index)
    range_str_labels = [f"{r:.1f}~{r+20:.1f}" for r in range_labels]

    iqr_values = list(iqr_summary.loc[range_labels]) + [overall_iqr]
    mean_values = list(mean_summary.loc[range_labels]) + [overall_mean]

    summary_table = pd.DataFrame(
        [iqr_values, mean_values],
        index=['Mean of IQR Upper Bound', 'Mean of Gyro'],
        columns=range_str_labels + ['Overall (0.0~2.2)']
    )
    summary_table.index.name = 'Position(m)'

    st.dataframe(summary_table.style.format("{:.3f}"))

    # 1) 업로드 데이터 9개인지 확인
    if uploaded_data is None or len(uploaded_data) == 0:
        st.warning("📂 왼쪽 사이드바에서 CSV 파일을 업로드하세요.")
        return
    elif len(uploaded_data) < 9:
        st.warning(f"⚠️ 데이터 부족: 업로드된 데이터가 9개 미만입니다. (현재 업로드:{len(uploaded_data)}개)")
        return

    # 2) IQR 상한선 (summary에서 전체 평균 사용)
    # combined_df에는 summary 파일 데이터 있음
    # position_bin 20 단위로 묶인 upper 평균값을 구함
    iqr_summary = combined_df.groupby('position_bin')['upper'].mean()
    # 20단위 구간 라벨로 변환 (ex: 0,20,40,...)
    iqr_20bins = {}
    for pos_bin, upper_val in iqr_summary.items():
        bin_20 = (pos_bin // 20) * 20
        if bin_20 not in iqr_20bins:
            iqr_20bins[bin_20] = []
        iqr_20bins[bin_20].append(upper_val)
    # 각 20단위 구간별 평균 upper 값 계산
    iqr_20bins = {k: sum(v)/len(v) for k, v in iqr_20bins.items()}

    # 3) 구간별로 9개 데이터에서 상한선 넘은 횟수 세기
    exceed_counts = {}
    for bin_start in sorted(iqr_20bins.keys()):
        count_exceed = 0
        upper_limit = iqr_20bins[bin_start]
        bin_end = bin_start + 20
        for df in uploaded_data:
            # 해당 구간 position 값 필터링
            sub_df = df[(df['position'] >= bin_start) & (df['position'] < bin_end)]
            if sub_df.empty:
                continue
            # 해당 구간 gyro값이 upper_limit 넘은 점이 있는지 검사
            if (sub_df['gyro'] > upper_limit).any():
                count_exceed += 1
        exceed_counts[bin_start] = count_exceed

    # 4) 6개 이상 넘으면 이상 예측 구간
    abnormal_bins = []
    for bin_start, count in exceed_counts.items():
        if count >= 6:
            abnormal_bins.append((bin_start, count))

    # 5) 메시지 출력
    if abnormal_bins:
        detected_bins = len(abnormal_bins)  # 발견한 이상 구간 수
        msg_lines = [f"🚨 이상 예측 구간 발견: 11개 구간 중 {detected_bins}개"]
        total_files = len(uploaded_data)
        for bin_start, count in abnormal_bins:
            percent = (count / total_files) * 100
            msg_lines.append(
                f"- 구간 {bin_start}~{bin_start + 19} cm: 총 {total_files}개 중 {count}개 상한선 초과 ({percent:.1f}%)"
            )
        st.error("\n".join(msg_lines))
    else:
        st.success("✅ 이상 예측 구간 없음")