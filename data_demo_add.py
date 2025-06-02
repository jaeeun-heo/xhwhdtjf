import pandas as pd
import os
import glob
import matplotlib.pyplot as plt
##통합본 파일11111##
base_dir = 'data'

def load_add_files(data_type):  # data_type: 'normal_add' or 'anomal_add'
    folder = os.path.join(base_dir, data_type)
    print(f"[INFO] Looking into folder: {folder}")

    file_list = []
    set_folders = glob.glob(os.path.join(folder, 'set*'))
    for set_folder in set_folders:
        files = glob.glob(os.path.join(set_folder, f'{data_type}_*.csv'))
        file_list.extend(files)

    print(f"[INFO] Found {len(file_list)} files.")
    return sorted(file_list)


# 1) 원하는 데이터 타입 설정
data_type = 'normal_add'  # 또는 'anomal_add'

# 2) 파일 리스트 불러오기
file_list = load_add_files(data_type)

    # 그래프 1: x = position, y = gyro
def plot_individual_graphs(df, base_name):
    plt.figure(figsize=(10, 6))  # 그래프 크기 설정
    plt.plot(df['position'], df['gyro'], label='Gyro', color='b')
    plt.xlabel('Position')
    plt.ylabel('Gyro')
    plt.title(f'{base_name} - Gyro vs Position')
    plt.legend()
    plt.grid(True)
    plt.ylim(0, 3)  # y축 범위 설정
    plt.close()
    
    # 그래프 2: x = position, y = pitch
    plt.figure(figsize=(10, 6))  # 그래프 크기 설정
    plt.plot(df['position'], df['cumulative_pitch'], label='pitch', color='g')
    plt.xlabel('Position')
    plt.ylabel('pitch')
    plt.title(f'{base_name} - Pitch vs Position')
    plt.legend()
    plt.grid(True)
    plt.ylim(-0.5, 0.5)  # y축 범위 설정
    plt.close()

    # 그래프 3: x = position, y = roll
    plt.figure(figsize=(10, 6))  # 그래프 크기 설정
    plt.plot(df['position'], df['cumulative_roll'], label='roll', color='g')
    plt.xlabel('Position')
    plt.ylabel('roll')
    plt.title(f'{base_name} - roll vs Position')
    plt.legend()
    plt.grid(True)
    plt.ylim(-0.5, 0.5)  # y축 범위 설정
    plt.close()

    # 그래프 4: x = position, y = tilt
    plt.figure(figsize=(10, 6))  # 그래프 크기 설정
    plt.plot(df['position'], df['tilt'], label='tilt', color='g')
    plt.xlabel('Position')
    plt.ylabel('tilt')
    plt.title(f'{base_name} - tilt vs Position')
    plt.legend()
    plt.grid(True)
    plt.ylim(0, 0.5)  # y축 범위 설정
    plt.close()





### 한번에 비교 ###
### 그래프 1: x = position, y = gyro

plt.figure(figsize=(10, 6))
combined_df = pd.DataFrame()

for file_path in file_list:
    df = pd.read_csv(file_path)
    if 'gyro' in df.columns:
        combined_df = pd.concat([combined_df, df[['position', 'gyro']]], ignore_index=True)


# 개별 파일 시각화
for file_path in file_list:
    df = pd.read_csv(file_path)
    base_name = os.path.basename(file_path).split('.')[0]
    if 'gyro' in df.columns:
        plt.plot(df['position'], df['gyro'], alpha=0.35, label=f'{base_name} - Gyro')


# 평균선 계산 (0.1이 쪼개는 단위, 더 작은 수치 대입하여 더 정교한 값 얻을 수 있음)

combined_df['position_bin'] = (combined_df['position'] / 0.1).round() * 0.1

gyro_summary = combined_df.groupby('position_bin')['gyro'].mean().reset_index()
plt.plot(gyro_summary['position_bin'], gyro_summary['gyro'], color='red', linewidth=1.5, label='Mean Gyro')

# 고점 계산
gyro_max = combined_df.groupby('position_bin')['gyro'].max().reset_index()
plt.plot(gyro_max['position_bin'], gyro_max['gyro'], color='green', linewidth=1, label='Max Gyro')

# 상한선만 계산
def calc_iqr_upper_bound(group):
    q1 = group.quantile(0.25)
    q3 = group.quantile(0.75)
    iqr = q3 - q1
    upper = q3 + 1.5 * iqr
    return pd.Series({'upper': upper})

iqr_upper = combined_df.groupby('position_bin')['gyro'].apply(calc_iqr_upper_bound).unstack().reset_index()
###IQR 방식은 데이터가 한쪽으로 너무 커지면 불리함

# 상한선 시각화
plt.plot(iqr_upper['position_bin'], iqr_upper['upper'], color='orange', linestyle='--', linewidth=1, label='IQR Upper Bound')

# 시각화
plt.xlabel('Position')
plt.ylabel('Gyro')
plt.title('Gyro vs Position with Mean, Max and IQR Bounds')
plt.legend()
plt.grid(True)
plt.ylim(0, 2.5)
plt.show()




### 그래프 2: x = position, y = cumulative_pitch
plt.figure(figsize=(10, 6))

for file_path in file_list:
    df = pd.read_csv(file_path)
    base_name = os.path.basename(file_path).split('.')[0]
    if 'cumulative_pitch' in df.columns:
        plt.plot(df['position'], df['cumulative_pitch'], alpha=0.35, label=f'{base_name} - cumulative_pitch')

for file_path in file_list:
    df = pd.read_csv(file_path)
    if 'cumulative_pitch' in df.columns:
        combined_df = pd.concat([combined_df, df[['position', 'cumulative_pitch']]], ignore_index=True)

combined_df['position_bin'] = (combined_df['position'] / 0.1).round() * 0.1
pitch_summary = combined_df.groupby('position_bin')['cumulative_pitch'].mean().reset_index()

plt.plot(pitch_summary['position_bin'], pitch_summary['cumulative_pitch'], color='red', linewidth=1, label='Mean Pitch')

# 고점 계산
pitch_max = combined_df.groupby('position_bin')['cumulative_pitch'].max().reset_index()
plt.plot(pitch_max['position_bin'], pitch_max['cumulative_pitch'], color='green', linewidth=0.7, label='Max Pitch')

# 저점 계산
pitch_min = combined_df.groupby('position_bin')['cumulative_pitch'].min().reset_index()
plt.plot(pitch_min['position_bin'], pitch_min['cumulative_pitch'], color='green', linewidth=0.7, label='Min Pitch')

# 고점-저점 음영처리
plt.fill_between(pitch_max['position_bin'], pitch_max['cumulative_pitch'], pitch_min['cumulative_pitch'], color='green', alpha=0.1, label='Max-Min Range')


plt.xlabel('Position')
plt.ylabel('cumulative_pitch')
plt.title('Pitch vs Position with Mean Line')
plt.legend()
plt.grid(True)
plt.ylim(-0.3, 0.3)
plt.show()



### 그래프 3: x = position, y = cumulative_roll
plt.figure(figsize=(10, 6))

for file_path in file_list:
    df = pd.read_csv(file_path)
    base_name = os.path.basename(file_path).split('.')[0]
    if 'cumulative_roll' in df.columns:
        plt.plot(df['position'], df['cumulative_roll'], alpha=0.35, label=f'{base_name} - cumulative_roll')

for file_path in file_list:
    df = pd.read_csv(file_path)
    if 'cumulative_roll' in df.columns:
        combined_df = pd.concat([combined_df, df[['position', 'cumulative_roll']]], ignore_index=True)

combined_df['position_bin'] = (combined_df['position'] / 0.1).round() * 0.1
roll_summary = combined_df.groupby('position_bin')['cumulative_roll'].mean().reset_index()

plt.plot(roll_summary['position_bin'], roll_summary['cumulative_roll'], color='green', linewidth=1, label='Mean Roll')

plt.xlabel('Position')
plt.ylabel('cumulative_roll')
plt.title('Roll vs Position with Mean Line')
plt.legend()
plt.grid(True)
plt.ylim(-0.3, 0.3)
plt.show()



### 그래프 4: x = position, y = tilt
plt.figure(figsize=(10, 6))

for file_path in file_list:
    df = pd.read_csv(file_path)
    if 'tilt' in df.columns:
        combined_df = pd.concat([combined_df, df[['position', 'tilt']]], ignore_index=True)

combined_df['position_bin'] = (combined_df['position'] / 0.1).round() * 0.1
tilt_summary = combined_df.groupby('position_bin')['tilt'].mean().reset_index()

plt.plot(tilt_summary['position_bin'], tilt_summary['tilt'], color='red', linewidth=1, label='Mean Tilt')

# 고점 계산
tilt_max = combined_df.groupby('position_bin')['tilt'].max().reset_index()
plt.plot(tilt_max['position_bin'], tilt_max['tilt'], color='green', linewidth=0.7, label='Max Tilt')

for file_path in file_list:
    df = pd.read_csv(file_path)
    base_name = os.path.basename(file_path).split('.')[0]
    if 'tilt' in df.columns:
        plt.plot(df['position'], df['tilt'], alpha=0.35, label=f'{base_name} - tilt')

plt.xlabel('Position')
plt.ylabel('Tilt')
plt.title('Tilt vs Position with Mean Line')
plt.legend()
plt.grid(True)
plt.ylim(0, 0.3)
plt.show()


# pitch와 tilt 평균을 한 그래프에 시각화
plt.figure(figsize=(10, 6))

# pitch 평균선 시각화 (이미 계산된 pitch_summary 사용)
plt.plot(pitch_summary['position_bin'], pitch_summary['cumulative_pitch'], label='Mean Pitch', color='green', linewidth=0.7)

# pitch 고점선 시각화 (이미 계산된 pitch_max 사용)
plt.plot(pitch_max['position_bin'], pitch_max['cumulative_pitch'], label='Max Pitch', color='green', linestyle='--', linewidth=0.7)

# pitch 저점선 시각화 (이미 계산된 pitch_min 사용)
plt.plot(pitch_min['position_bin'], pitch_min['cumulative_pitch'], label='Min Pitch', color='green', linestyle='--', linewidth=0.7)

# pitch 고점과 저점 사이 음영 처리
plt.fill_between(pitch_max['position_bin'], pitch_max['cumulative_pitch'], pitch_min['cumulative_pitch'], color='green', alpha=0.1)

# tilt 평균선 시각화 (이미 계산된 tilt_summary 사용)
plt.plot(tilt_summary['position_bin'], tilt_summary['tilt'], label='Mean Tilt', color='red', linewidth=0.7)

# 그래프 꾸미기
plt.xlabel('Position')
plt.ylabel('Cumulative Value')
plt.title('Comparison of Mean Pitch and Mean Tilt vs Position')
plt.legend()
plt.grid(True)
plt.ylim(-0.3, 0.3)
plt.show()