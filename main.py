import qrcode
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

# Gyro 분석 모듈 import
from gyro import show_gyro

# QR코드 생성
url = "https://xhwhdtjf-b7n87zyelbtmnhzzjlp6kq.streamlit.app/"
img = qrcode.make(url)
img.save("qr_code.png")

# 초기 상태 설정
if 'alarm_active' not in st.session_state:
    st.session_state.alarm_active = False

# 오른쪽 상단 버튼 배치
col1, col2 = st.columns([8, 2])
with col2:
    if st.button("\U0001F6A8 경보 울리기"):
        st.session_state.alarm_active = not st.session_state.alarm_active

    if st.session_state.alarm_active:
        st.markdown("\U0001F4E2 <strong>경보를 울리는 중입니다.</strong></div>", unsafe_allow_html=True)
    else:
        st.markdown("\u2705 <strong>경보가 꺼져 있습니다.</strong></div>", unsafe_allow_html=True)

# 사이드바 - 데이터 업로드
st.sidebar.header("\U0001F4C2 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("센서 데이터를 업로드하세요 (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("\U0001F4C4 업로드된 데이터 미리보기")
    st.dataframe(df.head())

    st.subheader("\U0001F4CA 기본 통계 정보")
    st.write(df.describe())
else:
    st.info("왼쪽 사이드바에서 센서 데이터를 업로드해주세요.")

# 모의 데이터 다운로드 버튼
st.sidebar.markdown("---")
st.sidebar.subheader("\U0001F4C1 모의 데이터 다운로드")

def create_mock_data(index):
    np.random.seed(index)
    mock_df = pd.DataFrame({
        '시간': pd.date_range(start='2024-01-01', periods=100, freq='S'),
        '가속도_X': np.random.normal(0, 0.5, 100),
        '가속도_Y': np.random.normal(0, 0.5, 100),
        '가속도_Z': np.random.normal(9.8, 0.5, 100),
    })
    return mock_df

for i in range(1, 4):
    df_mock = create_mock_data(i)
    csv = df_mock.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label=f"\U0001F4E5 모의 데이터 {i} 다운로드",
        data=csv,
        file_name=f"mock_data_{i}.csv",
        mime='text/csv'
    )

# --- 분석 탭 버튼 ---
st.subheader("\U0001F4CB 분석 항목 선택")
analysis_option = st.radio("분석할 항목을 선택하세요:", ["None", "Gyro"], horizontal=True)

# --- 버튼 선택 시 해당 분석 화면 실행 ---
if analysis_option == "Gyro":
    show_gyro()
else:
    st.markdown("\n
    ### 분석 항목을 선택하면 결과가 여기에 표시됩니다.")
