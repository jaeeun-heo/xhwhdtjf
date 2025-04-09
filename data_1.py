import pandas as pd
import matplotlib.pyplot as plt

# 파일 경로 지정
accel_path = 'data/2025-04-06_08-10-24/Accelerometer_1.csv'
gyro_path = "data/2025-04-06_08-10-24/Gyroscope_1.csv"
orient_path = "data/2025-04-06_08-10-24/Orientation_1.csv"


# CSV 파일 읽기
accel_df = pd.read_csv(accel_path)
gyro_df = pd.read_csv(gyro_path)
orient_df = pd.read_csv(orient_path)

# 데이터 미리보기
print("Accelerometer Data:")
print(accel_df.head())

print("\nGyroscope Data:")
print(gyro_df.head())

print("\nOrientation Data:")
print(orient_df.head())

# time 열이 존재하는지 확인하고 필요 시 float 변환
for df in [accel_df, gyro_df, orient_df]:
    df['time'] = df['time'].astype(float)

# time 기준으로 병합 (inner join을 사용하여 공통 시간만 유지)
merged_df = pd.merge(accel_df, gyro_df, on="time", suffixes=('_accel', '_gyro'))
merged_df = pd.merge(merged_df, orient_df, on="time", suffixes=('', '_orient'))

# 결과 확인
print("통합 데이터프레임 (앞부분):")
print(merged_df.head())

# 시간 기준 정렬
merged_df = merged_df.sort_values("time").reset_index(drop=True)

# 시간 기준 경과 시간 (초) 계산
start_time = merged_df['time'].iloc[0]
merged_df['elapsed_sec'] = (merged_df['time'] - start_time) / 1e9  # 나노초 → 초

import matplotlib.pyplot as plt

# 가속도 시각화
plt.figure(figsize=(12, 4))
plt.plot(merged_df['elapsed_sec'], merged_df['x_accel'], label='Accel X')
plt.plot(merged_df['elapsed_sec'], merged_df['y_accel'], label='Accel Y')
plt.plot(merged_df['elapsed_sec'], merged_df['z_accel'], label='Accel Z')
plt.title('Accelerometer Data')
plt.xlabel('Time (sec)')
plt.ylabel('Acceleration (m/s²)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 자이로 시각화
plt.figure(figsize=(12, 4))
plt.plot(merged_df['elapsed_sec'], merged_df['x_gyro'], label='Gyro X')
plt.plot(merged_df['elapsed_sec'], merged_df['y_gyro'], label='Gyro Y')
plt.plot(merged_df['elapsed_sec'], merged_df['z_gyro'], label='Gyro Z')
plt.title('Gyroscope Data')
plt.xlabel('Time (sec)')
plt.ylabel('Angular Velocity (rad/s)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# pitch, roll, yaw 시각화
plt.figure(figsize=(12, 4))
plt.plot(merged_df['elapsed_sec'], merged_df['pitch'], label='Pitch')
plt.plot(merged_df['elapsed_sec'], merged_df['roll'], label='Roll')
plt.plot(merged_df['elapsed_sec'], merged_df['yaw'], label='Yaw')
plt.title('Orientation (Euler Angles)')
plt.xlabel('Time (sec)')
plt.ylabel('Angle (radians)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()



import numpy as np

# 가속도 크기 계산 (벡터의 크기)
merged_df['accel_magnitude'] = np.sqrt(
    merged_df['x_accel']**2 + merged_df['y_accel']**2 + merged_df['z_accel']**2
)

# 기준값 설정 (예: 12 m/s² 이상은 이상치로 가정)
threshold = 12
merged_df['accel_anomaly'] = merged_df['accel_magnitude'] > threshold


plt.figure(figsize=(12, 5))
plt.plot(merged_df['elapsed_sec'], merged_df['accel_magnitude'], label='Accel Magnitude')
plt.axhline(y=threshold, color='red', linestyle='--', label='Threshold')
plt.scatter(merged_df['elapsed_sec'][merged_df['accel_anomaly']], 
            merged_df['accel_magnitude'][merged_df['accel_anomaly']], 
            color='red', label='Anomaly')
plt.title('Acceleration Magnitude with Anomaly Detection')
plt.xlabel('Time (sec)')
plt.ylabel('Acceleration Magnitude (m/s²)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# 자이로 크기 계산
merged_df['gyro_magnitude'] = np.sqrt(
    merged_df['x_gyro']**2 + merged_df['y_gyro']**2 + merged_df['z_gyro']**2
)

# 기준값 설정 (예: 급회전 등 판단 기준)
gyro_threshold = 3.0  # rad/s
merged_df['gyro_anomaly'] = merged_df['gyro_magnitude'] > gyro_threshold


plt.figure(figsize=(12, 5))
plt.plot(merged_df['elapsed_sec'], merged_df['gyro_magnitude'], label='Gyro Magnitude')
plt.axhline(y=gyro_threshold, color='orange', linestyle='--', label='Threshold')
plt.scatter(merged_df['elapsed_sec'][merged_df['gyro_anomaly']], 
            merged_df['gyro_magnitude'][merged_df['gyro_anomaly']], 
            color='orange', label='Anomaly')
plt.title('Gyroscope Magnitude with Anomaly Detection')
plt.xlabel('Time (sec)')
plt.ylabel('Angular Velocity (rad/s)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


anomalies_accel = merged_df[merged_df['accel_anomaly']]
anomalies_accel[['elapsed_sec', 'accel_magnitude']]


anomalies_gyro = merged_df[merged_df['gyro_anomaly']]
anomalies_gyro[['elapsed_sec', 'gyro_magnitude']]



from scipy.stats import zscore

# Z-score로 이상 판단
merged_df['accel_zscore'] = zscore(merged_df['accel_magnitude'])

# Z-score가 ±3 이상이면 극단값
merged_df['accel_z_anomaly'] = merged_df['accel_zscore'].abs() > 3

# 확인
merged_df[merged_df['accel_z_anomaly']][['elapsed_sec', 'accel_magnitude', 'accel_zscore']]

# 이상 지점만 추출
anomalies = merged_df[merged_df['accel_z_anomaly']]

# 이상 지점 출력 (최대 10개만 보기)
print("이상으로 감지된 지점:")
print(anomalies[['elapsed_sec', 'accel_magnitude', 'accel_zscore']].head(10))

# 이상 점들의 개수와 전체 대비 비율
print(f"\n총 이상 탐지 지점 수: {len(anomalies)}")
print(f"전체 중 이상 비율: {len(anomalies) / len(merged_df) * 100:.2f}%")

# 이상 확률(이상 정도)은 z-score의 절댓값으로 대체
anomalies['anomaly_severity'] = anomalies['accel_zscore'].abs()


import matplotlib.pyplot as plt

plt.figure(figsize=(14, 6))
plt.plot(merged_df['elapsed_sec'], merged_df['accel_magnitude'], label='가속도 크기')
plt.scatter(anomalies['elapsed_sec'], anomalies['accel_magnitude'], color='red', label='이상 지점')
plt.title('가속도 기반 이상 탐지')
plt.xlabel('Elapsed Time (sec)')
plt.ylabel('Acceleration Magnitude')
plt.legend()
plt.grid(True)
plt.show()
