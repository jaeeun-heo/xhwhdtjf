import pandas as pd
import matplotlib.pyplot as plt

# 파일 경로 지정
file_path = 'data/2025-04-06_08-10-24/Accelerometer_1.csv'

# CSV 파일 읽기
df = pd.read_csv(file_path)

# 데이터 미리보기
print(df.head())

# 가속도 시각화
plt.figure(figsize=(10, 6))
plt.plot(df['seconds_elapsed'], df['x'], label='X-Axis Acceleration')
plt.plot(df['seconds_elapsed'], df['y'], label='Y-Axis Acceleration')
plt.plot(df['seconds_elapsed'], df['z'], label='Z-Axis Acceleration')
plt.xlabel('Time (seconds)')
plt.ylabel('Acceleration')
plt.title('Acceleration Data Over Time')
plt.legend()
plt.grid(True)
plt.show()

# 속도 추정
df['delta_time'] = df['seconds_elapsed'].diff().fillna(0)  # 시간 차이 계산
df['velocity'] = (df['x'] * df['delta_time']).cumsum()  # X축 가속도로 속도 추정

# 속도 시각화
plt.figure(figsize=(10, 6))
plt.plot(df['seconds_elapsed'], df['velocity'], label='Estimated Velocity')
plt.xlabel('Time (seconds)')
plt.ylabel('Estimated Velocity (m/s)')
plt.title('Estimated Velocity Over Time')
plt.legend()
plt.grid(True)
plt.show()




import streamlit as st
# Streamlit에서 바로 그래프 그림을 출력 (화면에 보여주기)
st.pyplot(plt)
