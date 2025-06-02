import glob
import os
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
from scipy.stats import zscore
from scipy.signal import find_peaks

base_dir = 'data'

# 원본 폴더 경로
normal_dir = os.path.join(base_dir, 'normal')
anomal_dir = os.path.join(base_dir, 'anomal')

def load_files(data_type):
    folder = normal_dir if data_type == 'normal' else anomal_dir
    print(f"[INFO] Looking into folder: {folder}")

    file_list = []
    set_folders = glob.glob(os.path.join(folder, 'set10'))  # set0, set1, ...
    for set_folder in set_folders:
        files = glob.glob(os.path.join(set_folder, 'raw_anomal_*.csv'))
        file_list.extend(files)
    return file_list

def analyze_and_save(file_path, data_type):
    df = pd.read_csv(file_path)

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
    plt.close()

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
            df_len = len(df)
            safe_start = min(start, df_len - 1)
            safe_end = min(end, df_len - 1)
            plt.axvspan(df['time'].iloc[safe_start], df['time'].iloc[safe_end], color='red', alpha=0.2)


        plt.axvline(stable_start_time, color='green', linestyle='--', label='Stable Start')
        plt.axvline(stable_end_time, color='blue', linestyle='--', label='Stable End')
        plt.xlabel('Time (s)')
        plt.ylabel('Gyro Magnitude')
        plt.title('방지턱 감지로 데이터 절단')
        plt.grid(True)
        plt.legend()
        plt.close()




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
    plt.title('accel_y')
    plt.xlabel('Time')
    plt.ylabel('Acceleration')
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
    plt.title('gyro_x_y_z')
    plt.xlabel('Time')
    plt.ylabel('Gyroscope')
    plt.legend()
    plt.grid(True)

# pitch & roll (그대로 유지)
    plt.subplot(3, 1, 3)
    plt.plot(df_original['time'], df_original['pitch'], label='Original pitch', color='salmon', alpha=0.4)
    plt.plot(df_clean['time'], df_clean['pitch'], label='pitch', color='green')
    plt.plot(df_original['time'], df_original['roll'], label='Original roll', color='salmon', alpha=0.4)
    plt.plot(df_clean['time'], df_clean['roll'], label='roll', color='red')
    plt.title('pitch and roll')
    plt.xlabel('Time')
    plt.ylabel('Orientation')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()



### x축: 위치 추정
# 시간, 가속도 배열 추출
    time = df_clean['time'].to_numpy()                        # 길이: N
    accel = df_clean['accel_y'].to_numpy() * 9.81             # 길이: N

    # 시간 차이 계산
    dt = np.diff(time)                                        # 길이: N-1

    # 총 이동 거리 (고정값)과 총 시간 계산
    total_distance = 2.19  # meters
    total_time = time[-1] - time[0]  # seconds

    # --- 1차 적분: 초기속도 0 기준 속도 계산 (사다리꼴 적분법) ---
    velocity_temp = np.zeros_like(accel)                      # 길이: N
    for i in range(1, len(accel)):
        velocity_temp[i] = velocity_temp[i-1] + 0.5 * (accel[i-1] + accel[i]) * dt[i-1]

    # 측정된 평균 속도
    measured_avg_velocity = np.mean(velocity_temp)

    # 실제 평균 속도
    real_avg_velocity = total_distance / total_time

    # 초기속도 보정값 (적분 상수)
    initial_velocity = real_avg_velocity - measured_avg_velocity

    # 보정된 속도 = temp 속도 + 상수
    velocity = velocity_temp + initial_velocity

    # --- 2차 적분: 위치 계산 (사다리꼴 적분법) ---
    position = np.zeros_like(time)                            # 길이: N
    for i in range(1, len(time)):
        position[i] = position[i-1] + 0.5 * (velocity[i-1] + velocity[i]) * dt[i-1]


    #음수로 향하면 휴대폰 거꾸로 든 것
    plt.figure(figsize=(15, 10))

    plt.subplot(3, 1, 1)
    plt.plot(df_clean['time'], df_clean['accel_y'])
    plt.title('Acceleration (from accel_y)')
    plt.xlabel('Time')
    plt.ylabel('Accelerometer (m/s)')
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
    plt.close()


# 마지막 위치를 3m로 맞추기 위해 보정
### 0시작에서 3끝으로 보정한 것(반전시킴)
    position = position * (219 / position[-1])

# 시간에 따른 위치 그래프 그리기
    plt.figure(figsize=(10, 6))
    plt.plot(df_clean['time'], position, label='position (cm)', color='orange')
    plt.title('position over Time')
    plt.xlabel('Time (s)')
    plt.ylabel('position (cm)')
    plt.grid(True)
    plt.legend()
    plt.close()

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
    #plt.show()
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


    # 분석 결과 저장 경로 구성
    normal_add_dir = os.path.join(base_dir, 'normal_add')
    anomal_add_dir = os.path.join(base_dir, 'anomal_add')
    
    # 분석 결과 저장 경로 구성 (덮어쓰기)
    if data_type == 'normal':
        save_base = normal_dir
        original_base = normal_dir
    else:
        save_base = anomal_dir
        original_base = anomal_dir

    rel_path = os.path.relpath(file_path, original_base)  # 예: set0/normal_1.csv
    set_folder, filename = os.path.split(rel_path)        # ('set0', 'normal_1.csv')

    if data_type == 'anomal' and filename.startswith('raw_anomal_'):
        filename = filename.replace('raw_anomal_', 'anomal_')

    save_folder = os.path.join(save_base, set_folder)     # 원래 위치
    os.makedirs(save_folder, exist_ok=True)

    save_path = os.path.join(save_folder, filename)       # 이름 그대로 저장
    df_clean.to_csv(save_path, index=False)
    print(f"[INFO] Overwritten: {save_path}")
    
def main():
    normal_files = load_files('normal')
    for file_path in normal_files:
        print(f"[INFO] Analyzing {file_path}")
        analyze_and_save(file_path, 'normal')

    anomal_files = load_files('anomal')
    for file_path in anomal_files:
        print(f"[INFO] Analyzing {file_path}")
        analyze_and_save(file_path, 'anomal')

if __name__ == "__main__":
    main()