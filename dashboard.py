


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



# gyro_dashboard.py

import os
import glob
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(layout="wide")

with st.expander("Gyro"):
    # 1. 파일 로딩
    data_dir = "data/demo_add"
    file_list = glob.glob(os.path.join(data_dir, "demo_*_add.csv"))

    combined_df = pd.DataFrame()

    for file in file_list:
        df = pd.read_csv(file)
        df['file'] = os.path.basename(file).split('.')[0]
        if 'position' in df.columns and 'gyro' in df.columns:
            df['position_bin'] = (df['position'] / 0.1).round() * 0.1
            combined_df = pd.concat([combined_df, df[['position', 'gyro', 'position_bin', 'file']]], ignore_index=True)

    # 2. 통합 평균 및 IQR 계산
    mean_df = combined_df.groupby('position_bin')['gyro'].mean().reset_index(name='mean')

    def calc_iqr_upper(group):
        q1 = group.quantile(0.25)
        q3 = group.quantile(0.75)
        return q3 + 1.5 * (q3 - q1)

    iqr_df = combined_df.groupby('position_bin')['gyro'].apply(calc_iqr_upper).reset_index(name='upper')

    # 전체 평균
    overall_mean = mean_df['mean'].mean()
    overall_iqr = iqr_df['upper'].mean()

    # 3. Plotly 그래프 생성
    fig = go.Figure()

    # 개별 파일 데이터 (legendonly, alpha 0.5)
    for fname in combined_df['file'].unique():
        file_data = combined_df[combined_df['file'] == fname]
        fig.add_trace(go.Scatter(
            x=file_data['position'],
            y=file_data['gyro'],
            mode='lines',
            name=fname,
            line=dict(width=1, color='rgba(100,100,100,0.5)'),
            visible='legendonly'
        ))

    # 평균선 추가
    fig.add_trace(go.Scatter(
        x=mean_df['position_bin'],
        y=mean_df['mean'],
        mode='lines',
        name=f"Mean Gyro (Overall: {overall_mean:.3f})",
        line=dict(color='skyblue', width=3)
    ))

    # IQR 상한선 추가
    fig.add_trace(go.Scatter(
        x=iqr_df['position_bin'],
        y=iqr_df['upper'],
        mode='lines',
        name=f"IQR Upper Bound (Overall: {overall_iqr:.3f})",
        line=dict(color='orange', width=3, dash='dash')
    ))

    fig.update_layout(
        title='📈 Gyro Summary by Position',
        xaxis_title='Position (m)',
        yaxis_title='Gyro',
        legend=dict(x=1.02, y=1),
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # 4. 표 생성 (0.5m 단위로, 범위를 열로)
    mean_df['range'] = (mean_df['position_bin'] // 0.5) * 0.5
    iqr_df['range'] = (iqr_df['position_bin'] // 0.5) * 0.5

    range_labels = sorted(mean_df['range'].unique())
    range_str_labels = [f"{r:.1f}~{r+0.5:.1f}" for r in range_labels]

    mean_summary = mean_df.groupby('range')['mean'].mean()
    iqr_summary = iqr_df.groupby('range')['upper'].mean()

    # 전체 평균 계산 (0.0~2.5)
    overall_mean = mean_summary.mean()
    overall_iqr = iqr_summary.mean()

    # 데이터프레임 형태 맞추기
    data = {
        'Mean of Gyro': [mean_summary.get(r, np.nan) for r in range_labels] + [overall_mean],
        'Mean of IQR Upper Bound': [iqr_summary.get(r, np.nan) for r in range_labels] + [overall_iqr]
    }

    # 열 이름에 전체 평균 범위 추가
    columns = range_str_labels + ['Overall (0.0~2.5)']

    summary_table = pd.DataFrame(data, index=columns).T

    # 결과 출력
    st.markdown("### 📊 Summary Table (per 0.5m interval, transposed)")
    st.dataframe(summary_table.round(3))

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
