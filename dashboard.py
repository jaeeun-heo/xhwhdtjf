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
combined_df = combined_df[combined_df['position_bin'] <= 2.5]



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




# 0.5 단위 구간 생성
mean_line['bin_group'] = (mean_line['position_bin'] // 0.5) * 0.5
iqr_df['bin_group'] = (iqr_df['position_bin'] // 0.5) * 0.5

mean_by_bin = mean_line.groupby('bin_group')['mean'].mean()
iqr_by_bin = iqr_df.groupby('bin_group')['upper'].mean()

bin_starts = mean_by_bin.index.values
bin_ends = bin_starts + 0.5

x_vals = mean_line['position_bin']
mean_vals = mean_line['mean']
iqr_vals = iqr_df['upper']

# 전체 평균 계산
overall_mean = mean_line['mean'].mean()
overall_iqr_upper = iqr_df['upper'].mean()

fig = go.Figure()

# 평균선, 범례에 전체 평균 포함
fig.add_trace(go.Scatter(
    x=x_vals,
    y=mean_vals,
    mode='lines',
    name=f'Mean Gyro (Overall: {overall_mean:.3f})',
    line=dict(color='sky blue')
))

# IQR 상한선, 범례에 전체 평균 포함
fig.add_trace(go.Scatter(
    x=iqr_df['position_bin'],
    y=iqr_vals,
    mode='lines',
    name=f'IQR Upper Bound (Overall: {overall_iqr_upper:.3f})',
    line=dict(color='orange')
))

# 구간별 평균값 annotation 추가 (글씨 크기 키움)
for start, end, mean_val, iqr_val in zip(bin_starts, bin_ends, mean_by_bin.values, iqr_by_bin.values):
    x_pos = (start + end) / 2
    
    fig.add_annotation(
        x=x_pos, y=mean_val,
        text=f"Mean: {mean_val:.2f}",
        showarrow=False,
        yshift=15,
        font=dict(color='blue', size=16, family="Arial"),
        align='center',
        bgcolor='rgba(255,255,255,0.7)',
        bordercolor='sky blue',
        borderwidth=1,
        borderpad=4
    )
    fig.add_annotation(
        x=x_pos, y=iqr_val,
        text=f"IQR Upper: {iqr_val:.2f}",
        showarrow=False,
        yshift=-20,
        font=dict(color='orange', size=16, family="Arial"),
        align='center',
        bgcolor='rgba(255,255,255,0.7)',
        bordercolor='orange',
        borderwidth=1,
        borderpad=4
    )

fig.update_layout(
    title='Gyro Mean and IQR Upper Bound by Position with Interval Labels',
    xaxis_title='Position (m)',
    yaxis_title='Gyro',
    template='plotly_white',
    yaxis=dict(range=[0, 1.0]),  # y축 범위 0~1.0으로 고정
    legend=dict(y=0.99, x=0.01, font=dict(size=14))
        legend=dict(
        x=1.02,
        y=1,
        xanchor='left',
        yanchor='top',
        font=dict(size=14)
    )
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
