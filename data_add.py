import pandas as pd
import os
import glob
import matplotlib.pyplot as plt

# === 기본 설정 ===
base_dir = 'data'
data_type = 'normal'
folder = os.path.join(base_dir, data_type)
summary_save_dir = os.path.join(folder, "summary")
os.makedirs(summary_save_dir, exist_ok=True)
set_folders = sorted(glob.glob(os.path.join(folder, 'set*')))

bin_size_gyro = 50
bin_size_pitch_tilt = 1

# === 반복 시작 ===
for set_folder in set_folders:
    set_name = os.path.basename(set_folder)
    csv_files = sorted(glob.glob(os.path.join(set_folder, 'normal_*.csv')))

    combined_df = pd.DataFrame()
    for file_path in csv_files:
        df = pd.read_csv(file_path)
        combined_df = pd.concat([combined_df, df], ignore_index=True)

    if combined_df.empty:
        print(f'Warning: {set_name} has no data. Skipping...')
        continue

    required_cols = ['position', 'gyro', 'cumulative_pitch', 'tilt']
    if not all(col in combined_df.columns for col in required_cols):
        print(f'Warning: {set_name} is missing required columns. Skipping...')
        continue

    # === Binning ===
    combined_df['position_bin_gyro'] = (combined_df['position'] / bin_size_gyro).round() * bin_size_gyro
    combined_df['position_bin_pitch_tilt'] = (combined_df['position'] / bin_size_pitch_tilt).round() * bin_size_pitch_tilt

    # === 요약 통계 계산 ===
    summary_gyro = combined_df.groupby('position_bin_gyro').agg(
        mean_gyro=('gyro', 'mean'),
        q1_gyro=('gyro', lambda x: x.quantile(0.25)),
        q3_gyro=('gyro', lambda x: x.quantile(0.75))
    ).reset_index()
    summary_gyro['iqr_gyro'] = summary_gyro['q3_gyro'] - summary_gyro['q1_gyro']
    summary_gyro['upper_bound_gyro'] = summary_gyro['q3_gyro'] + 2.5 * summary_gyro['iqr_gyro']
    summary_gyro = summary_gyro.drop(columns=['q1_gyro', 'q3_gyro', 'iqr_gyro'])

    summary_pitch_tilt = combined_df.groupby('position_bin_pitch_tilt').agg(
        mean_pitch=('cumulative_pitch', 'mean'),
        mean_tilt=('tilt', 'mean')
    ).reset_index()

    # === 1. Gyro Plot ===    
    for file_path in csv_files:
        df = pd.read_csv(file_path)
        plt.plot(df['position'], df['gyro'], linewidth=0.5, alpha=0.8)

    plt.plot(summary_gyro['position_bin_gyro'], summary_gyro['mean_gyro'], color='red', linewidth=1, label='Mean Gyro')
    plt.plot(summary_gyro['position_bin_gyro'], summary_gyro['upper_bound_gyro'], color='orange', linestyle='--', linewidth=1, label='IQR Upper Bound')

    plt.title(f'{set_name} - Position vs. Gyro')
    plt.xlabel('Position')
    plt.ylabel('Gyro')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.ylim(0, 1.0)
    plt.close()

    # === 2. Cumulative Pitch Plot ===
    plt. figure(figsize=(12,10))
    
    plt.subplot(2, 1, 1)
    for file_path in csv_files:
        df = pd.read_csv(file_path)
        plt.plot(df['position'], df['cumulative_pitch'], linewidth=0.5, alpha=0.5)

    plt.plot(summary_pitch_tilt['position_bin_pitch_tilt'], summary_pitch_tilt['mean_pitch'], color='red', linewidth=1, label='Mean Cumulative Pitch')

    plt.title(f'{set_name} - Position vs. Cumulative Pitch')
    plt.xlabel('Position')
    plt.ylabel('Cumulative Pitch')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.ylim(-0.1, 0.1)

    # === 3. Tilt Plot ===
    plt.subplot(2, 1, 2)
    for file_path in csv_files:
        df = pd.read_csv(file_path)
        plt.plot(df['position'], df['tilt'], linewidth=0.5, alpha=0.5)

    plt.plot(summary_pitch_tilt['position_bin_pitch_tilt'], summary_pitch_tilt['mean_tilt'], color='red', linewidth=1, label='Mean Tilt')

    plt.title(f'{set_name} - Position vs. Tilt')
    plt.xlabel('Position')
    plt.ylabel('Tilt')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.ylim(0, 0.1)
    
    plt.tight_layout()
    plt.show()

    # === 파일 저장 ===
    summary_gyro.to_csv(os.path.join(summary_save_dir, f"summary_gyro_{set_name}.csv"), index=False)
    summary_pitch_tilt.to_csv(os.path.join(summary_save_dir, f"summary_pitch_tilt_{set_name}.csv"), index=False)

    print(f"[INFO] 저장 완료: summary_gyro_{set_name}.csv, summary_pitch_tilt_{set_name}.csv")
