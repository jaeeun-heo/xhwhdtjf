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

# 2. 평균선 계산
mean_line = combined_df.groupby('position_bin')['gyro'].mean().reset_index(name='mean')

# 3. IQR 상한선 계산
def calc_iqr_upper_bound(group):
    q1 = group.quantile(0.25)
    q3 = group.quantile(0.75)
    iqr = q3 - q1
    return q3 + 1.5 * iqr

iqr_df = combined_df.groupby('position_bin')['gyro'].apply(calc_iqr_upper_bound).reset_index(name='upper')

# 4. Plotly 시각화
fig = go.Figure()
fig.add_trace(go.Scatter(x=mean_line['position_bin'], y=mean_line['mean'],
                         mode='lines', name='Mean Gyro', line=dict(color='sky blue')))
fig.add_trace(go.Scatter(x=iqr_df['position_bin'], y=iqr_df['upper'],
                         mode='lines', name='IQR Upper Bound', line=dict(color='orange')))

fig.update_layout(title='📈 Gyro Mean & IQR Upper Bound by Position',
                  xaxis_title='Position',
                  yaxis_title='Gyro',
                  template='plotly_white')

st.plotly_chart(fig, use_container_width=True)


# 1. 구간 단위 설정 (0.5m 간격)
mean_line['bin_group'] = (mean_line['position_bin'] // 0.5) * 0.5
iqr_df['bin_group'] = (iqr_df['position_bin'] // 0.5) * 0.5

# 2. 구간별 평균값 계산
mean_by_bin = mean_line.groupby('bin_group')['mean'].mean()
iqr_by_bin = iqr_df.groupby('bin_group')['upper'].mean()

# 3. 구간 이름 만들기 (0~0.5, 0.5~1.0 ...)
ranges = [f"{start:.1f} ~ {start + 0.5:.1f}" for start in mean_by_bin.index]

# 4. 바로 원하는 형태(행: 지표, 열: 구간)로 데이터프레임 생성
summary_table = pd.DataFrame({
    'Mean of Gyro': mean_by_bin.values,
    'Mean of IQR Upper Bound': iqr_by_bin.values
}, index=ranges).T

# 5. 전체 평균(열 기준) 추가
summary_table['Overall Mean'] = summary_table.mean(axis=1)

# 6. Streamlit에 출력
st.markdown("### 📊 구간별 평균 값 요약 (0.5m 간격, 행/열 맞춤 및 전체 평균 포함)")
st.dataframe(summary_table.style.format("{:.3f}"))


# 예시 데이터 (원래 네 combined_df, mean_line, iqr_df 등에서 유도된 것 가정)
# 아래는 구간별 (0~0.5, 0.5~1.0 ...) 평균과 IQR 상한선 평균값 데이터라고 생각해줘
summary_table = pd.DataFrame({
    'bin_group': [0.0, 0.5, 1.0, 1.5, 2.0],
    'Mean of Gyro': [1.1, 1.2, 1.3, 1.25, 1.4],
    'Mean of IQR Upper Bound': [1.5, 1.6, 1.7, 1.65, 1.8]
})

# x 축을 각 구간의 중앙값으로 계산 (ex: 0~0.5 구간은 0.25)
summary_table['mid_point'] = summary_table['bin_group'] + 0.25

# 그래프용 summary 생성 (기존 summary에서 필요한 부분만)
summary = pd.DataFrame({
    'position_bin': np.repeat(summary_table['mid_point'].values, 1),
    'mean': summary_table['Mean of Gyro'],
    'upper': summary_table['Mean of IQR Upper Bound']
})

fig = go.Figure()

# 평균선 그리기
fig.add_trace(go.Scatter(
    x=summary_table['mid_point'],
    y=summary_table['Mean of Gyro'],
    mode='lines+markers',
    name='Mean Gyro',
    line=dict(color='red')
))

# IQR 상한선 그리기
fig.add_trace(go.Scatter(
    x=summary_table['mid_point'],
    y=summary_table['Mean of IQR Upper Bound'],
    mode='lines+markers',
    name='IQR Upper Bound',
    line=dict(color='orange', dash='dash')
))

# 텍스트 라벨 추가: 평균선 값
fig.add_trace(go.Scatter(
    x=summary_table['mid_point'],
    y=summary_table['Mean of Gyro'],
    mode='text',
    text=[f"{v:.2f}" for v in summary_table['Mean of Gyro']],
    textposition='top center',
    showlegend=False
))

# 텍스트 라벨 추가: IQR 상한선 값
fig.add_trace(go.Scatter(
    x=summary_table['mid_point'],
    y=summary_table['Mean of IQR Upper Bound'],
    mode='text',
    text=[f"{v:.2f}" for v in summary_table['Mean of IQR Upper Bound']],
    textposition='bottom center',
    showlegend=False
))

fig.update_layout(
    title='Gyro Mean and IQR Upper Bound by Position with Labels',
    xaxis_title='Position (m)',
    yaxis_title='Gyro',
    yaxis=dict(range=[0, max(summary_table['Mean of IQR Upper Bound']) * 1.1]),
    legend=dict(y=0.99, x=0.01)
)

fig.show()


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
