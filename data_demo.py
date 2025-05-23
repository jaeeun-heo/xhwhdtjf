import glob
import os
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
from scipy.stats import zscore
from scipy.signal import find_peaks


# 경로 설정
data_dir = "C:/Users/yello/OneDrive/문서/경기대/25-1/캡스톤/xhwhdtjf/data/"
file_list = glob.glob(os.path.join(data_dir, "demo_*.csv"))  # demo_1.csv, demo_2.csv, ...

# 파일 반복 처리
for file_path in file_list:
    # 파일 이름 추출
    filename = os.path.basename(file_path).split('.')[0]

    # 파일 불러오기
    df = pd.read_csv(file_path)
    print(df.columns.tolist())
    df_original = df.copy()



# time을 기준으로 그래프를 그림
    plt.figure(figsize=(15, 10))

# accel_y
    plt.subplot(3, 1, 1)
    plt.plot(df['time'], df['accel_y'], label='accel_y', color='blue')
    plt.title('accel_y over time')
    plt.xlabel('Time')
    plt.ylabel('Acceleration Y')
    plt.grid(True)

# gyro_x_y_z
    plt.subplot(3, 1, 2)
    plt.plot(df['time'], df['gyro_x'], label='gyro_x', color='red')
    plt.plot(df['time'], df['gyro_y'], label='gyro_y', color='green')
    plt.plot(df['time'], df['gyro_z'], label='gyro_z', color='purple')
    plt.title('Gyroscope (x, y, z) over time')
    plt.xlabel('Time')
    plt.ylabel('Gyro')
    plt.legend()
    plt.grid(True)

# pitch & roll
    plt.subplot(3, 1, 3)
    plt.plot(df['time'], df['pitch'], label='pitch', color='green')
    plt.plot(df['time'], df['roll'], label='roll', color='red')
    plt.title('pitch and roll over time')
    plt.xlabel('Time')
    plt.ylabel('Angle (degrees)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()

#    plt.show()
    plt.show()


    df_original = df.copy()



# 1. gyro x, y, z 벡터 크기 계산
    gyro_combined = np.sqrt(df['gyro_x']**2 + df['gyro_y']**2 + df['gyro_z']**2)

# 2. 초기 2초간 baseline 평균 및 std
    initial_duration = 2.0
    start_time = df['time'].iloc[0]
    initial_idx = df['time'] - start_time < initial_duration
    baseline_mean = gyro_combined[initial_idx].mean()
    baseline_std = gyro_combined[initial_idx].std()

# 3. 임계값 설정
    threshold = 0.3  # 예시 값

# 4. 0.2초 이동평균 smoothing
    sampling_interval = np.mean(np.diff(df['time']))
    window_size = int(0.2 / sampling_interval)
    gyro_smooth = gyro_combined.rolling(window=window_size, center=True).mean().bfill().ffill()

# 5. 임계값 초과 여부 판단
    above_threshold = gyro_smooth > threshold

# 6. 연속 구간 찾기 함수
    def get_continuous_regions(bool_array, min_length):
        regions = []
        start = None
        for i, val in enumerate(bool_array):
            if val and start is None:
                start = i
            elif not val and start is not None:
                if i - start >= min_length:
                    regions.append((start, i))
                start = None
        if start is not None and len(bool_array) - start >= min_length:
            regions.append((start, len(bool_array)))
        return regions

# 7. 충격 감지 구간 (0.05초 이상 지속된 경우만)
    min_len = int(0.05 / sampling_interval)
    shock_regions = get_continuous_regions(above_threshold.values, min_len)

    if len(shock_regions) < 1:
        print("충격 구간 없음")
        df_cut = df.copy()
    else:
    # 첫 충격 끝 이후 안정 구간 시작
        first_shock_end = shock_regions[0][1]
    # 마지막 충격 시작 이전 안정 구간 끝
        last_shock_start = shock_regions[-1][0]

    # 여유 버퍼 (0.3초) 추가
        buffer_samples = int(0.05 / sampling_interval)
        stable_start_idx = min(first_shock_end + buffer_samples, len(df)-1)
        stable_end_idx = max(last_shock_start - buffer_samples, 0)

    # 시간 기준으로 변환
        stable_start_time = df['time'].iloc[stable_start_idx]
        stable_end_time = df['time'].iloc[stable_end_idx]

    # 안정 구간 추출
        df_cut = df[(df['time'] >= stable_start_time) & (df['time'] <= stable_end_time)].reset_index(drop=True)

        print(f"남긴 안정 구간: {stable_start_time:.3f}s ~ {stable_end_time:.3f}s")
        print(f"샘플 수: {len(df_cut)}")

    # 시각화
        plt.figure(figsize=(12, 6))
        plt.plot(df['time'], gyro_combined, label='Gyro Combined')
        plt.plot(df['time'], gyro_smooth, label='Gyro Smooth', alpha=0.7)
        plt.axhline(y=threshold, color='r', linestyle='--', label='Threshold')

        for start, end in shock_regions:
            plt.axvspan(df['time'].iloc[start], df['time'].iloc[end], color='red', alpha=0.2)

        plt.axvline(stable_start_time, color='green', linestyle='--', label='Stable Start')
        plt.axvline(stable_end_time, color='blue', linestyle='--', label='Stable End')
        plt.xlabel('Time (s)')
        plt.ylabel('Gyro Magnitude')
        plt.title('방지턱 충격 이후 안정 구간 추출')
        plt.grid(True)
        plt.legend()
        plt.show()




# 이상치 제거 함수 (Z-score 기준)
### 정상 수치에만 적용할 것


    zscore_columns = ['accel_y', 'gyro_x', 'gyro_y', 'gyro_z', 'pitch', 'roll']
    zscore_columns = [col for col in zscore_columns if col in df_cut.columns]


### 정규분포 +-3시그마 적용함 (전체 데이터에서 99.7% 까지 취급함) / +-2시그마는 95%
    def remove_outliers_z(df, cols, threshold=3):
        for col in cols:
            z_scores = zscore(df[col].dropna())
            outliers = abs(z_scores) > threshold
            df.loc[df[col].dropna().index[outliers], col] = np.nan
        return df

### tilt 값도 전처리 추가할 것
# 이상치 제거 대상 열
    df_clean = df_cut.copy()

# 이상치 제거 및 선형 보간
    df_clean = remove_outliers_z(df_clean, zscore_columns)
    df_clean.interpolate(method='linear', inplace=True)


## 이상치 제거 전후 시각화
    plt.figure(figsize=(15, 10))

# accel_y 비교
    plt.subplot(3, 1, 1)
    plt.plot(df_original['time'], df_original['accel_y'], label='Original accel_y', color='orange', alpha=0.5)
    plt.plot(df_clean['time'], df_clean['accel_y'], label='Cleaned accel_y', color='blue')
    plt.title('accel_y: Original vs Z-score Cleaned')
    plt.xlabel('Time')
    plt.ylabel('Acceleration Y')
    plt.legend()
    plt.grid(True)

# gyro 비교
    plt.subplot(3, 1, 2)
    plt.plot(df_original['time'], df_original['gyro_x'], label='Original gyro_x', color='salmon', alpha=0.4)
    plt.plot(df_clean['time'], df_clean['gyro_x'], label='Cleaned gyro_x', color='red')
    plt.plot(df_original['time'], df_original['gyro_y'], label='Original gyro_y', color='lightgreen', alpha=0.4)
    plt.plot(df_clean['time'], df_clean['gyro_y'], label='Cleaned gyro_y', color='green')
    plt.plot(df_original['time'], df_original['gyro_z'], label='Original gyro_z', color='plum', alpha=0.4)
    plt.plot(df_clean['time'], df_clean['gyro_z'], label='Cleaned gyro_z', color='purple')
    plt.title('Gyroscope (x, y, z): Original vs Cleaned')
    plt.xlabel('Time')
    plt.ylabel('Gyro')
    plt.legend()
    plt.grid(True)

# pitch & roll (그대로 유지)
    plt.subplot(3, 1, 3)
    plt.plot(df_original['time'], df_original['pitch'], label='Original pitch', color='salmon', alpha=0.4)
    plt.plot(df_clean['time'], df_clean['pitch'], label='pitch', color='green')
    plt.plot(df_original['time'], df_original['roll'], label='Original roll', color='salmon', alpha=0.4)
    plt.plot(df_clean['time'], df_clean['roll'], label='roll', color='red')
    plt.title('pitch and roll (not cleaned)')
    plt.xlabel('Time')
    plt.ylabel('Angle (degrees)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()



### x축: 위치 추정
### 이 부분 나중에 방지턱 감지하는 것으로 수정 필요###
# 시간 간격 (시간이 일정하지 않다면 각 시간 간격을 구해줘야 함)
    dt = np.diff(df_clean['time'])

# 가속도(accel_y) 적분하여 속도 계산 (속도는 적분 값이므로, 초기 속도를 0으로 설정)
    velocity = np.cumsum(df_clean['accel_y'].iloc[:-1] * dt)  # 첫 번째 값은 누락되어 있으므로 dt만큼 길이를 맞춰줍니다.
    velocity = np.insert(velocity, 0, 0)  # 초기 속도는 0으로 설정

# 속도 적분하여 위치 계산 (위치는 적분 값)
    position = np.cumsum(velocity[:-1] * dt)  # 마찬가지로 길이를 맞추기 위해 적분합니다.
    position = np.insert(position, 0, 0)  # 초기 위치는 0으로 설정

#음수로 향하면 휴대폰 거꾸로 든 것
    plt.figure(figsize=(15, 10))

    plt.subplot(3, 1, 1)
    plt.plot(df_clean['time'], df_clean['accel_y'])
    plt.title('Velocity (from accel_y)')
    plt.xlabel('Time')
    plt.ylabel('Velocity (m/s)')
    plt.grid()

    plt.subplot(3, 1, 2)
    plt.plot(df_clean['time'], velocity)
    plt.title('Velocity (from accel_y)')
    plt.xlabel('Time')
    plt.ylabel('Velocity (m/s)')
    plt.grid()

    plt.subplot(3, 1, 3)
    plt.plot(df_clean['time'], position)
    plt.title('position (from accel_y)')
    plt.xlabel('Time')
    plt.ylabel('position (m/s)')
    plt.grid()

    plt.tight_layout()
    plt.show()


# 마지막 위치를 3m로 맞추기 위해 보정
### 0시작에서 3끝으로 보정한 것(반전시킴)
    position = position * (2.5 / position[-1])

# 시간에 따른 위치 그래프 그리기
    plt.figure(figsize=(10, 6))
    plt.plot(df_clean['time'], position, label='position (m)', color='orange')
    plt.title('position over Time')
    plt.xlabel('Time (s)')
    plt.ylabel('position (m)')
    plt.grid(True)
    plt.legend()
    plt.show()

# 새로운 'position' 열 추가
    df_clean['position'] = position








### y_1축: 진동 추정
# 자이로 합성 벡터 크기 계산
    df_clean['gyro'] = np.sqrt(
        df_clean['gyro_x']**2 + df_clean['gyro_y']**2 + df_clean['gyro_z']**2
    )

# 시각화
    plt.figure(figsize=(10, 4))
    plt.plot(df_clean['time'], df_clean['gyro'], label='Gyro Magnitude', color='purple')
    plt.xlabel('Time (s)')
    plt.ylabel('Gyro Magnitude (deg/s)')
    plt.title('Combined Gyroscope Magnitude Over Time')
    plt.grid(True)
    plt.legend()
#    plt.show()
    plt.close()





### y2축: 침하 감지


## 1. pitch - 높이 추정
# 1.1 pitch 기울기 변화량
    df_clean['pitch_delta'] = df_clean['pitch'].diff().fillna(0)  # 첫 번째 값은 NaN이므로 0으로 채운다

# 1.2 pitch 기울기 변화량 누적합
    df_clean['cumulative_pitch'] = df_clean['pitch_delta'].cumsum()


## 2. roll
# 2.1 roll 기울기 변화량
    df_clean['roll_delta'] = df_clean['roll'].diff().fillna(0)  # 첫 번째 값은 NaN이므로 0으로 채운다

# 2.2 roll 기울기 변화량 누적합
    df_clean['cumulative_roll'] = df_clean['roll_delta'].cumsum()


## 3. pitch-roll 누적합 종합
    df_clean['tilt'] = np.sqrt(df_clean['cumulative_pitch']**2 + df_clean['cumulative_roll']**2)


## 시각화
    plt.figure(figsize=(12, 9))

    plt. subplot(3, 1, 1)
    plt.plot(df_clean['time'], df_clean['cumulative_pitch'], label='Cumulative Pitch', color='blue')
    plt.xlabel('time')
    plt.ylabel('Cumulative Pitch (Relative Change)')
    plt.title('Cumulative Pitch Change Based on Position')
    plt.grid(True)
    plt.ylim(-0.2, 0.2)
    plt.legend()

    plt. subplot(3, 1, 2)
    plt.plot(df_clean['time'], df_clean['cumulative_roll'], label='Cumulative Roll', color='green')
    plt.xlabel('Time')
    plt.ylabel('Cumulative Roll (Relative Change)')
    plt.title('Cumulative Roll Change Based on Position')
    plt.grid(True)
    plt.ylim(-0.2, 0.2)
    plt.legend()

    plt. subplot(3, 1, 3)
    plt.plot(df_clean['time'], df_clean['tilt'], label='tilt', color='red')
    plt.xlabel('Time')
    plt.ylabel('Tilt')
    plt.title('tilt')
    plt.grid(True)
    plt.legend()
    plt.ylim(0, 0.2)
    plt.tight_layout()
    plt.show()


### 새로운 파일로 저장
# 저장할 폴더 경로 지정
    output_dir = "C:/Users/yello/OneDrive/문서/경기대/25-1/캡스톤/xhwhdtjf/data/demo_add"

# 저장 파일 이름 생성 및 경로 지정
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    new_name = f"{base_name}_add.csv"
    output_path = os.path.join(output_dir, new_name)

# 저장
    df_clean.to_csv(output_path, index=False)
