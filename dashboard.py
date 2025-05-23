import qrcode

url = "https://xhwhdtjf-b7n87zyelbtmnhzzjlp6kq.streamlit.app/"
img = qrcode.make(url)
img.save("qr_code.png")


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




# 페이지 기본 설정
st.set_page_config(page_title="교량 안전 모니터링 시스템", layout="wide")
st.title("📊 교량 안전 모니터링 대시보드")
st.write("모형 교량 위를 주행하는 차량의 스마트폰 센서 데이터를 분석하여 이상을 감지합니다.")
st.markdown("스마트폰에서 수집한 데이터를 기반으로 이상 탐지 및 시각화를 수행합니다.")

# 데이터 디렉토리 설정

data_dir = "data/demo_add"
file_list = glob.glob(os.path.join(data_dir, "demo_*_add.csv"))

combined_df = pd.DataFrame()

for file in file_list:
    df = pd.read_csv(file)
    df['file'] = os.path.basename(file).split('.')[0]
    if 'position' in df.columns and 'gyro' in df.columns:
        df['position_bin'] = (df['position'] / 0.1).round() * 0.1
        combined_df = pd.concat([combined_df, df[['position_bin', 'gyro', 'file']]], ignore_index=True)

# 2. position_bin별 평균선 계산
mean_line = combined_df.groupby('position_bin')['gyro'].mean().reset_index(name='mean')

# 3. IQR 상한선 계산 함수
def calc_iqr_upper_bound(group):
    q1 = group.quantile(0.25)
    q3 = group.quantile(0.75)
    iqr = q3 - q1
    return q3 + 1.5 * iqr

iqr_df = combined_df.groupby('position_bin')['gyro'].apply(calc_iqr_upper_bound).reset_index(name='upper')

# --- 0.5 단위 구간 생성 ---
# 0.5 단위 bin_group 생성 (ex: 0~0.5 구간은 0.0, 0.5~1.0 구간은 0.5 ...)
mean_line['bin_group'] = (mean_line['position_bin'] // 0.5) * 0.5
iqr_df['bin_group'] = (iqr_df['position_bin'] // 0.5) * 0.5

# 구간별 평균 계산
mean_by_bin = mean_line.groupby('bin_group')['mean'].mean()
iqr_by_bin = iqr_df.groupby('bin_group')['upper'].mean()

# 구간별 이름 생성 (ex: "0.0 ~ 0.5")
ranges = [f"{start:.1f} ~ {start + 0.5:.1f}" for start in mean_by_bin.index]

# 구간별 데이터프레임 (summary_table)
summary_table = pd.DataFrame({
    'Mean of Gyro': mean_by_bin.values,
    'Mean of IQR Upper Bound': iqr_by_bin.values
}, index=ranges)

# 전체 평균 추가
summary_table['Overall Mean'] = summary_table.mean(axis=1)

# Streamlit에 표 출력
st.markdown("### 📊 구간별 평균 값 요약 (0.5m 간격)")
st.dataframe(summary_table.style.format("{:.3f}"))

# 그래프용 x축 좌표: 각 구간의 중간값 (ex: 0.25, 0.75 ...)
mid_points = mean_by_bin.index + 0.25

# Plotly 그래프 생성
fig = go.Figure()

# 평균선 + 라벨
fig.add_trace(go.Scatter(
    x=mid_points,
    y=mean_by_bin.values,
    mode='lines+markers+text',
    name='Mean Gyro',
    line=dict(color='red'),
    text=[f"{v:.2f}" for v in mean_by_bin.values],
    textposition='top center'
))

# IQR 상한선 + 라벨
fig.add_trace(go.Scatter(
    x=mid_points,
    y=iqr_by_bin.values,
    mode='lines+markers+text',
    name='IQR Upper Bound',
    line=dict(color='orange', dash='dash'),
    text=[f"{v:.2f}" for v in iqr_by_bin.values],
    textposition='bottom center'
))

fig.update_layout(
    title='Gyro Mean and IQR Upper Bound by Position with Labels',
    xaxis_title='Position (m)',
    yaxis_title='Gyro',
    yaxis=dict(range=[0, max(iqr_by_bin.values)*1.2]),
    template='plotly_white',
    legend=dict(y=0.99, x=0.01)
)

st.plotly_chart(fig, use_container_width=True)


# 같은 방식으로 pitch, roll, tilt 등 추가 그래프도 반복해서 구성









# 초기 상태 설정
if 'alarm_active' not in st.session_state:
    st.session_state.alarm_active = False

# 오른쪽 상단 버튼 배치
col1, col2 = st.columns([8, 2])
with col2:
    # 버튼 클릭 시 상태 토글
    if st.button("🚨 경보 울리기"):
        st.session_state.alarm_active = not st.session_state.alarm_active

    # 상태에 따라 시각적 피드백
    if st.session_state.alarm_active:
        st.markdown(
            "📢 <strong>경보를 울리는 중입니다.</strong></div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "✅ <strong>경보가 꺼져 있습니다.</strong></div>",
            unsafe_allow_html=True
        )

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


# 모의 데이터 생성 함수
def create_mock_data(index):
    np.random.seed(index)
    mock_df = pd.DataFrame({
        '시간': pd.date_range(start='2024-01-01', periods=100, freq='S'),
        '가속도_X': np.random.normal(0, 0.5, 100),
        '가속도_Y': np.random.normal(0, 0.5, 100),
        '가속도_Z': np.random.normal(9.8, 0.5, 100),
    })
    return mock_df


# 모의 데이터 다운로드 버튼
st.sidebar.markdown("---")
st.sidebar.subheader("📁 모의 데이터 다운로드")
for i in range(1, 4):
    df_mock = create_mock_data(i)
    csv = df_mock.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label=f"📥 모의 데이터 {i} 다운로드",
        data=csv,
        file_name=f"mock_data_{i}.csv",
        mime='text/csv'
    )

# 업로드 처리
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
