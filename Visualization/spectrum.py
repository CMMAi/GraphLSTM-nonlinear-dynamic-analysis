import os
import numpy as np
import matplotlib.pyplot as plt
import eqsig.single
from pathlib import Path


# 1. Calculate design spectrum  (大安區，台北三區)
S_DS = 0.6
T0 = 1.05
print(f"T0 = {T0:.5f}")

periods = np.linspace(0.01, 5, 50)
design_spectrum_BSE1 = np.zeros(50)
design_spectrum_BSE2 = np.zeros(50)
for i, t in enumerate(periods):
    if t < 0.2*T0:
        design_spectrum_BSE1[i] = S_DS * (0.4 + 3 * t / T0)
    elif t >= 0.2*T0 and t <= T0:
        design_spectrum_BSE1[i] = S_DS
    elif t > T0:
        design_spectrum_BSE1[i] = S_DS * T0 / t
    else:
        design_spectrum_BSE1[i] = None

design_spectrum_BSE2 = design_spectrum_BSE1 * (4/3)


plt.rcParams['font.size'] = '16'
plt.figure(figsize=(8, 6))
plt.plot(periods, design_spectrum_BSE1, color="red", linewidth=2, label="BSE-1 (10%/50y)")
plt.plot(periods, design_spectrum_BSE2, color="blue", linewidth=2, label="BSE-2 (2%/50y)")
plt.grid()
plt.legend()
plt.xlabel("T (sec)")
plt.ylabel("Sa (g)")
plt.savefig(r"E:\TimeHistoryAnalysis\Time-History-Analysis\Visualization\spectrum\BSE-1_BSE-2.png")







