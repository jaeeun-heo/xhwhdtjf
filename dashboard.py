import qrcode

url = "https://xhwhdtjf-b7n87zyelbtmnhzzjlp6kq.streamlit.app/"
img = qrcode.make(url)
img.save("qr_code.png")


import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image


# 페이지 기본 설정
st.set_page_config(page_title="교량 안전 모니터링 시스템", layout="wide")
st.title("📊 교량 안전 모니터링 대시보드")
st.write("모형 교량 위를 주행하는 차량의 스마트폰 센서 데이터를 분석하여 이상을 감지합니다.")
st.markdown("스마트폰에서 수집한 데이터를 기반으로 이상 탐지 및 시각화를 수행합니다.")

# 사이드바
st.sidebar.header("📂 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("센서 데이터를 업로드하세요 (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📄 업로드된 데이터 미리보기")
    st.dataframe(df.head())

    st.subheader("📊 기본 통계 정보")
    st.write(df.describe())
else:
    st.info("왼쪽 사이드바에서 센서 데이터를 업로드해주세요.")


# CSV 업로드
uploaded_file = st.file_uploader("📥 센서 데이터 파일 업로드 (CSV)", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ 데이터 업로드 완료!")

    # 타임스탬프가 있으면 시간 정렬
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

    # 기본적인 데이터 확인
    st.subheader("1. 원시 데이터 미리보기")
    st.dataframe(df.head())

    # 가속도 시각화
    accel_cols = [col for col in df.columns if 'accel' in col.lower()]
    if accel_cols:
        st.subheader("2. 📈 가속도 분석")
        st.line_chart(df[accel_cols])

    # 회전 및 방향 시각화
    rot_cols = [col for col in df.columns if 'gyro' in col.lower() or 'rotation' in col.lower() or 'orientation' in col.lower()]
    if rot_cols:
        st.subheader("3. 🔄 회전/방향 데이터 분석")
        st.line_chart(df[rot_cols])

    # 속도 계산 및 일정성 확인 예시
    if 'timestamp' in df.columns and 'accel_x' in df.columns:
        df['delta_time'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
        df['approx_velocity'] = df['accel_x'].cumsum() * df['delta_time']
        st.subheader("4. 🚗 속도 변화 추정 (가속도 기반)")
        st.line_chart(df[['timestamp', 'approx_velocity']].set_index('timestamp'))

    # 이상치 탐지 예시 (가속도 Z축 기준)
    st.subheader("5. ⚠️ 이상 감지 예시")
    threshold = st.slider("이상 감지 임계값 (Z축 기준)", min_value=5.0, max_value=30.0, value=15.0)
    if 'accel_z' in df.columns:
        df['anomaly'] = np.where(abs(df['accel_z']) > threshold, 1, 0)
        st.write("이상치 발생 시점:")
        st.dataframe(df[df['anomaly'] == 1][['timestamp', 'accel_z']])

        # 이상 구간 시각화
        fig, ax = plt.subplots()
        ax.plot(df['timestamp'], df['accel_z'], label='accel_z')
        ax.scatter(df[df['anomaly']==1]['timestamp'], df[df['anomaly']==1]['accel_z'], color='red', label='Anomaly')
        ax.set_xlabel('시간')
        ax.set_ylabel('Z축 가속도')
        ax.legend()
        st.pyplot(fig)

else:
    st.warning("📤 좌측 메뉴에서 센서 데이터 CSV 파일을 업로드하세요.")
