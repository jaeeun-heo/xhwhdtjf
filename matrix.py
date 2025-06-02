import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

# 1. 정상 데이터 통계 요약 파일들 불러오기 (position_bin_gyro는 5단위임)
summary_files = sorted(glob.glob('data/normal/summary/summary_gyro_set[0-5].csv'))
summary_df_list = [pd.read_csv(f) for f in summary_files]
summary_df = pd.concat(summary_df_list, ignore_index=True)

# 2. 이상 탐지용 함수 정의
def detect_anomaly(file_path, summary_df, bin_size=0.3, upper_bin_size=30):
    df = pd.read_csv(file_path)
    
    # 0.3 단위 position_bin_0.1 생성
    df['position_bin_0.3'] = (df['position'] / bin_size).apply(np.floor) * bin_size
    
    # 5 단위 상한선 기준 position_bin_5 생성 (summary_df 기준)
    df['position_bin_30'] = (df['position'] / upper_bin_size).apply(np.floor) * upper_bin_size

    # summary_df와 병합 (position_bin_5 기준)
    merged = pd.merge(df, summary_df, left_on='position_bin_30', right_on='position_bin_gyro', how='inner')

    # 이상치 여부 (gyro > 상한선)
    merged['is_anomaly'] = merged['gyro'] > merged['upper_bound_gyro']

    # 0.3 단위 구간별 이상치 개수, 총 개수
    anomaly_count = merged.groupby('position_bin_0.3')['is_anomaly'].sum()
    total_count = merged.groupby('position_bin_0.3')['is_anomaly'].count()
    
    anomaly_ratio = anomaly_count / total_count

    # 이상 비율 70% 이상인 구간만 추출
    anomaly_bins = anomaly_ratio[anomaly_ratio >= 0.7]

    # 이상 구간 1개 이상이면 이상 감지 True
    detected = len(anomaly_bins) > 0

    return detected, len(anomaly_bins)


# 3. 정상 데이터 검증
normal_val_dir = 'data/normal/set6'
normal_val_files = sorted(glob.glob(os.path.join(normal_val_dir, 'normal_*.csv')))

normal_results = []
for f in normal_val_files:
    detected, anomaly_bin_count = detect_anomaly(f, summary_df)
    normal_results.append({'filename': os.path.basename(f), 'detected': detected, 'anomaly_bins': anomaly_bin_count})

# 4. 이상 데이터 검증
abnormal_val_dir = 'data/anomal/set13'
abnormal_val_files = sorted(glob.glob(os.path.join(abnormal_val_dir, 'anomal_*.csv')))

abnormal_results = []
for f in abnormal_val_files:
    detected, anomaly_bin_count = detect_anomaly(f, summary_df)
    abnormal_results.append({'filename': os.path.basename(f), 'detected': detected, 'anomaly_bins': anomaly_bin_count})

# 5. 평가
y_true = [0]*len(normal_results) + [1]*len(abnormal_results)
y_pred = [r['detected'] for r in normal_results] + [r['detected'] for r in abnormal_results]

cm = confusion_matrix(y_true, y_pred)
print("=== Confusion Matrix ===")
print(cm)
print("\n=== Classification Report ===")
print(classification_report(y_true, y_pred, zero_division=0))

# 6. 결과 출력
print("\n== 정상 데이터 ==")
for r in normal_results:
    print(f"{r['filename']}: 이상 구간 수 = {r['anomaly_bins']}, 이상 감지 = {r['detected']}")

print("\n== 이상 데이터 ==")
for r in abnormal_results:
    print(f"{r['filename']}: 이상 구간 수 = {r['anomaly_bins']}, 이상 감지 = {r['detected']}")


print("정상 데이터 파일 수:", len(normal_val_files))
print("이상 데이터 파일 수:", len(abnormal_val_files))






# === 경로 설정 ===
base_dir = 'data'
normal_summary_dir = os.path.join(base_dir, 'normal', 'summary')
anomal_summary_dir = os.path.join(base_dir, 'anomal', 'summary')

# === 정상 summary 전체 로드 및 평균화 및 std 계산 ===
normal_dfs = []
for i in range(6):  # set0 ~ set6
    file_path = os.path.join(normal_summary_dir, f'summary_pitch_tilt_set{i}.csv')
    df = pd.read_csv(file_path)
    normal_dfs.append(df)

normal_all = pd.concat(normal_dfs)
normal_stats = normal_all.groupby('position_bin_pitch_tilt')[['mean_pitch', 'mean_tilt']].agg(['mean', 'std']).reset_index()
normal_stats.columns = ['position', 'normal_mean_pitch', 'normal_std_pitch', 'normal_mean_tilt', 'normal_std_tilt']

# === 이상 summary 로드 및 비교 ===
for i in [6]:  # set10 ~ set13
    file_path = os.path.join(normal_summary_dir, f'summary_pitch_tilt_set{i}.csv')
    anomal_df = pd.read_csv(file_path)
    anomal_df = anomal_df.rename(columns={'position_bin_pitch_tilt': 'position'})

    # 위치 기준으로 병합
    merged = pd.merge(anomal_df, normal_stats, on='position', how='inner')

    # 차이 계산
    merged['pitch_diff'] = merged['mean_pitch'] - merged['normal_mean_pitch']
    merged['tilt_diff'] = merged['mean_tilt'] - merged['normal_mean_tilt']

    # === 그래프 그리기 ===
    plt.figure(figsize=(12, 5))

    # 1. Pitch Difference + 정상 평균선 + ±3시그마 음영
    plt.subplot(1, 2, 1)
    plt.plot(merged['position'], merged['pitch_diff'], label=f'set{i} pitch diff', color='blue')
    plt.plot(merged['position'], merged['normal_mean_pitch'], label='Normal Mean Pitch', color='crimson')
    plt.axhline(0, color='gray', linestyle='--', linewidth=1)

    upper_pitch = merged['normal_mean_pitch'] + 3 * merged['normal_std_pitch']
    lower_pitch = merged['normal_mean_pitch'] - 3 * merged['normal_std_pitch']
    plt.fill_between(merged['position'], lower_pitch, upper_pitch, color='crimson', alpha=0.15, label='Normal Pitch ±3σ Range')

    plt.title(f'Set{i} - Cumulative Pitch Difference (Anomal - Normal Avg)')
    plt.xlabel('Position')
    plt.ylabel('Pitch Difference')
    plt.ylim(-0.02, 0.04)
    plt.legend()
    plt.grid(True)

    # 2. Tilt 비교 + 정상 평균선 + ±3시그마 음영
    plt.subplot(1, 2, 2)
    plt.plot(merged['position'], merged['mean_tilt'], label=f'set{i} (Anomal)', color='orange')
    plt.plot(merged['position'], merged['normal_mean_tilt'], label='Normal Mean Tilt', color='green')

    upper_tilt = merged['normal_mean_tilt'] + 3 * merged['normal_std_tilt']
    lower_tilt = merged['normal_mean_tilt'] - 3 * merged['normal_std_tilt']
    plt.fill_between(merged['position'], lower_tilt, upper_tilt, color='green', alpha=0.2, label='Normal Tilt ±3σ Range')

    plt.title(f'Set{i} - Tilt Comparison with ±3σ Range')
    plt.xlabel('Position')
    plt.ylabel('Tilt')
    plt.ylim(-0.01, 0.05)
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()