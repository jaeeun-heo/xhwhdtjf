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
import zipfile
from io import BytesIO

# QR코드 생성
url = "https://xhwhdtjf-b7n87zyelbtmnhzzjlp6kq.streamlit.app/"
img = qrcode.make(url)
img.save("qr_code.png")


st.set_page_config(layout="wide")
# --------------------------
# 💡 대시보드 상단 제목 + 경보 버튼 한 줄 배치
title_col, button_col = st.columns([9, 1])
with title_col:
    st.markdown("### 스마트폰 센서 기반<br>교량 안전 모니터링 시스템", unsafe_allow_html=True)
    st.markdown("###### 토목공학종합설계 7조")

if 'alarm_active' not in st.session_state:
    st.session_state.alarm_active = False
    
with button_col:
    if st.button("\U0001F6A8"):
        st.session_state.alarm_active = not st.session_state.alarm_active

    if st.session_state.alarm_active:
        st.markdown("<span style='color:red;font-weight:bold;'>📢 경보 ON</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color:green;font-weight:bold;'>✅ 경보 OFF</span>", unsafe_allow_html=True)
# --------------------------
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
def make_zip_from_files(file_paths):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                zf.writestr(file_name, f.read())
    zip_buffer.seek(0)
    return zip_buffer

# 경로 설정
normal_dir = "data/normal/set6"
anomal_dir = "data/anomal/set13"

# normal_1: normal_67.csv ~ normal_79.csv (9개)
normal_1_files = [os.path.join(normal_dir, f"normal_{i}.csv") for i in [67, 69, 70, 74, 75, 76, 77, 78, 79]]
# normal_2: normal_80.csv ~ normal_88.csv (9개)
normal_2_files = [os.path.join(normal_dir, f"normal_{i}.csv") for i in [80, 81, 82, 83, 84, 85, 86, 87, 89]]

# anomal_1: anomal_131.csv ~ anomal_139.csv (9개)
anomal_1_files = [os.path.join(anomal_dir, f"anomal_{i}.csv") for i in range(131, 139)]
# anomal_2: anomal_140.csv ~ anomal_148.csv (9개)
anomal_2_files = [os.path.join(anomal_dir, f"anomal_{i}.csv") for i in range(140, 149)]

st.sidebar.markdown("---")
st.sidebar.subheader("\U0001F4C1 데이터 다운로드")

# 버튼 1: normal_1.zip
zip_buffer = make_zip_from_files(normal_1_files)
st.sidebar.download_button(
    label="⬇️ 정상 데이터 다운로드 1",
    data=zip_buffer,
    file_name="normal_1.zip",
    mime="application/zip"
)

# 버튼 2: normal_2.zip
zip_buffer = make_zip_from_files(normal_2_files)
st.sidebar.download_button(
    label="⬇️ 정상 데이터 다운로드 2",
    data=zip_buffer,
    file_name="normal_2.zip",
    mime="application/zip"
)

# 버튼 3: anomal_1.zip
zip_buffer = make_zip_from_files(anomal_1_files)
st.sidebar.download_button(
    label="⬇️ 이상 데이터 다운로드 1",
    data=zip_buffer,
    file_name="anomal_1.zip",
    mime="application/zip"
)

# 버튼 4: anomal_2.zip
zip_buffer = make_zip_from_files(anomal_2_files)
st.sidebar.download_button(
    label="⬇️ 이상 데이터 다운로드 2",
    data=zip_buffer,
    file_name="anomal_2.zip",
    mime="application/zip"
)

# --- 분석 탭 버튼 ---
analysis_option = st.radio("분석 항목 선택", ["Gyro", "Pitch"], horizontal=True)

# Gyro 분석 모듈 import
from gyro import show_gyro
from pitch import show_pitch

# --- 버튼 선택 시 해당 분석 화면 실행 ---
#if analysis_option == "Gyro":
#    show_gyro()
#elif analysis_option == "Pitch":
#    show_pitch()