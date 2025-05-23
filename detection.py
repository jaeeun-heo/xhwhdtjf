import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# 예시 데이터프레임 df 에서 accel_y 기준
data = df['accel_y'].dropna()

# IQR 계산
Q1 = data.quantile(0.25)
Q3 = data.quantile(0.75)
IQR = Q3 - Q1

# 이상치 기준 범위
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# 박스플롯 그리기
plt.figure(figsize=(10, 4))
sns.boxplot(x=data, color='skyblue')

# 이상치 기준선 그리기
plt.axvline(lower_bound, color='red', linestyle='--', label=f'Lower Bound: {lower_bound:.2f}')
plt.axvline(upper_bound, color='green', linestyle='--', label=f'Upper Bound: {upper_bound:.2f}')

plt.title('Boxplot of accel_y with IQR-based Outlier Bounds')
plt.xlabel('accel_y')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
