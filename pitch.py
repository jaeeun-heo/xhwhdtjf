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
        if 'position' in df.columns and 'pitch' in df.columns and 'tilt' in df.columns:
            df['position_bin'] = (df['position'] / 0.1).round() * 0.1
            combined_df = pd.concat([combined_df, df[['position', 'pitch', 'tilt', 'position_bin', 'file']]], ignore_index=True)



    # 2. 범위 필터 (예: position 0~2.5m)
    combined_df = combined_df[(combined_df['position'] >= 0) & (combined_df['position'] <= 2.5)]

    mean_pitch = combined_df.groupby('position_bin')['pitch'].mean().reset_index()
    mean_tilt = combined_df.groupby('position_bin')['tilt'].mean().reset_index()

    fig = go.Figure()

    
    # 개별 파일 pitch 데이터 (legendonly, alpha 0.3)
    for fname in combined_df['file'].unique():
        file_data = combined_df[combined_df['file'] == fname]
        fig.add_trace(go.Scatter(
            x=file_data['position'],
            y=file_data['pitch'],
            mode='lines',
            name=f"{fname} - pitch",
            line=dict(width=1, color='rgba(31,119,180,0.3)'),
            visible='legendonly'
        ))

    # 개별 파일 tilt 데이터 (legendonly, alpha 0.3)
    for fname in combined_df['file'].unique():
        file_data = combined_df[combined_df['file'] == fname]
        fig.add_trace(go.Scatter(
            x=file_data['position'],
            y=file_data['tilt'],
            mode='lines',
            name=f"{fname} - tilt",
            line=dict(width=1, color='rgba(255,127,14,0.3)'),
            visible='legendonly'
        ))

    # 평균 pitch 선
    fig.add_trace(go.Scatter(
        x=mean_pitch['position_bin'],
        y=mean_pitch['pitch'],
        mode='lines',
        name='Mean Pitch',
        line=dict(color='blue', width=3)
    ))

    # 평균 tilt 선
    fig.add_trace(go.Scatter(
        x=mean_tilt['position_bin'],
        y=mean_tilt['tilt'],
        mode='lines',
        name='Mean Tilt',
        line=dict(color='orange', width=3)
    ))

    fig.update_layout(
        title='📈 Pitch and Tilt Summary by Position',
        xaxis_title='Position (m)',
        yaxis_title='Value',
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