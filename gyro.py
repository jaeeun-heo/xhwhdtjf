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
        st.write(f"{file} 읽음, shape: {df.shape}")
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
            name=f"{fname} (Mean)",
            line=dict(width=1.5, color='gray'),
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

    fig.update_layout(
        title='📈 Gyro Summary by Position (from Summary Files)',
        xaxis_title='Position (m)',
        yaxis_title='Gyro',
        width=900,
        height=500,
        xaxis=dict(range=[0, 220]),
        yaxis=dict(range=[0, 0.5]),
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
    combined_df['range'] = (combined_df['position_bin'] // 0.5) * 0.5

    iqr_summary = combined_df.groupby('range')['upper'].mean()
    mean_summary = combined_df.groupby('range')['mean'].mean()

    overall_iqr = iqr_summary.mean()
    overall_mean = mean_summary.mean()

    range_labels = sorted(iqr_summary.index)
    range_str_labels = [f"{r:.1f}~{r+0.5:.1f}" for r in range_labels]

    iqr_values = list(iqr_summary.loc[range_labels]) + [overall_iqr]
    mean_values = list(mean_summary.loc[range_labels]) + [overall_mean]

    summary_table = pd.DataFrame(
        [iqr_values, mean_values],
        index=['Mean of IQR Upper Bound', 'Mean of Gyro'],
        columns=range_str_labels + ['Overall (0.0~2.2)']
    )
    summary_table.index.name = 'Position(m)'

    st.dataframe(summary_table.style.format("{:.3f}"), width=900)

# ------------------
# 업로드 데이터
    if uploaded_data is not None:
        add_df = uploaded_data.copy()
        