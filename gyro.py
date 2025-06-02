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
    data_dir = "data/normal/set0"
    file_list = glob.glob(os.path.join(data_dir, "normal_*.csv"))

    combined_df = pd.DataFrame()

    for file in file_list:
        df = pd.read_csv(file)
        df['file'] = os.path.basename(file).split('.')[0]
        if 'position' in df.columns and 'gyro' in df.columns:
            df['position_bin'] = (df['position'] / 0.1).round() * 0.1
            combined_df = pd.concat([combined_df, df[['position', 'gyro', 'position_bin', 'file']]], ignore_index=True)

    # 2. 통합 평균 및 IQR 계산
    combined_df = combined_df[(combined_df['position'] >= 0) & (combined_df['position'] <= 2.5)]

    def calc_iqr_upper(group):
        q1 = group.quantile(0.25)
        q3 = group.quantile(0.75)
        return q3 + 1.5 * (q3 - q1)

    iqr_df = combined_df.groupby('position_bin')['gyro'].apply(calc_iqr_upper).reset_index(name='upper').round(3)
    mean_df = combined_df.groupby('position_bin')['gyro'].mean().reset_index(name='mean').round(3)

    overall_iqr = iqr_df['upper'].mean()
    overall_mean = mean_df['mean'].mean()


    # 3. Plotly 그래프 생성
    fig = go.Figure()

    # 개별 파일 데이터 (legendonly, alpha 0.8)
    for fname in combined_df['file'].unique():
        file_data = combined_df[combined_df['file'] == fname]
        fig.add_trace(go.Scatter(
            x=file_data['position'],
            y=file_data['gyro'],
            mode='lines',
            name=fname,
            line=dict(width=1, color='rgba(100,100,100,0.8)'),
            visible='legendonly'
        ))

    # 평균선 추가
    fig.add_trace(go.Scatter(
        x=mean_df['position_bin'],
        y=mean_df['mean'],
        mode='lines',
        name=f"Mean Gyro",
        line=dict(color='skyblue', width=3)
    ))

    # IQR 상한선 추가
    fig.add_trace(go.Scatter(
        x=iqr_df['position_bin'],
        y=iqr_df['upper'],
        mode='lines',
        name=f"IQR Upper Bound",
        line=dict(color='orange', width=1.5, dash='dash')
    ))

    fig.update_layout(
        title='📈 Gyro Summary by Position',
        xaxis_title='Position (m)',
        yaxis_title='Gyro',
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



    # 4. 표 생성 (0.5m 단위, 0~2.5m 필터 후 데이터 기준)
    iqr_df['range'] = (iqr_df['position_bin'] // 0.5) * 0.5
    mean_df['range'] = (mean_df['position_bin'] // 0.5) * 0.5

    # 구간별 평균 계산
    iqr_summary = iqr_df.groupby('range')['upper'].mean()
    mean_summary = mean_df.groupby('range')['mean'].mean()

    # 전체 평균 (0~2.5 필터 후)
    overall_iqr = iqr_summary.mean()
    overall_mean = mean_summary.mean()

    # 구간 레이블 생성 (열 인덱스용)
    range_labels = sorted(iqr_summary.index)
    range_str_labels = [f"{r:.1f}~{r+0.5:.1f}" for r in range_labels]

    # 구간별 값 리스트 생성 (구간별 + 전체 평균)
    iqr_values = list(iqr_summary.loc[range_labels]) + [overall_iqr]
    mean_values = list(mean_summary.loc[range_labels]) + [overall_mean]

    # 데이터프레임 생성 (행: IQR, Mean / 열: 구간들 + Overall)
    summary_table = pd.DataFrame(
        [iqr_values, mean_values],
        index=['Mean of IQR Upper Bound', 'Mean of Gyro'],
        columns=range_str_labels + ['Overall (0.0~2.5)']
    )

    summary_table.index.name = 'Position(m)'

    # 결과 출력
    st.dataframe(summary_table.style.format("{:.3f}"), width=900)





# ------------------
# 업로드 데이터
    if uploaded_data is not None:
        add_df = uploaded_data.copy()
        