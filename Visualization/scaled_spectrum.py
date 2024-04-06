import numpy as np
import matplotlib.pyplot as plt
import os
import eqsig.single
from tqdm import tqdm



# root_1 = "E:/TimeHistoryAnalysis/Data/GroundMotions_ChiChi_processed_BSE-1"
# root_2 = "E:/TimeHistoryAnalysis/Data/GroundMotions_ChiChi_processed_BSE-2"
root_1 = "E:/TimeHistoryAnalysis/Data/GroundMotions_World_processed_BSE-1"
root_2 = "E:/TimeHistoryAnalysis/Data/GroundMotions_World_processed_BSE-2"
name = "World_Taipei3"



# 1. Calculate design spectrum  (大安區，台北三區)
S_DS = 0.6
T0 = 1.05
print(f"T0 = {T0:.5f}")

periods = np.linspace(0.01, 10, 100)
design_spectrum_BSE1 = np.zeros(100)
design_spectrum_BSE2 = np.zeros(100)
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




# 2. Find mean of the spectrums
sum_spectrum_1 = np.zeros(100)
sum_spectrum_2 = np.zeros(100)
dt = 0.005  # time step of acceleration time series
periods = np.linspace(0.01, 10, 100)  # compute the response for 100 periods between T=0.2s and 5.0s

# 2.1 Plot each ground motion's spectrun (X--> Period(s), Y--> Sa (G))
# 2.2 Plot in logscale (X--> Period(s), Y--> Sa (G))
plt.rcParams['font.size'] = '14'
fig, axs = plt.subplots(1, 1, figsize=(8, 6))
ground_motion_count_1 = len(os.listdir(root_1))
ground_motion_count_2 = len(os.listdir(root_2))

for i, gm_folder in enumerate(tqdm(os.listdir(root_1))):
    gm_name = gm_folder
    gm_FN_path = os.path.join(root_1, gm_folder, gm_name + "_FN.txt")
    gm_FP_path = os.path.join(root_1, gm_folder, gm_name + "_FP.txt")
    print(i, gm_FN_path, gm_FP_path)
    file_FN = np.loadtxt(gm_FN_path)
    file_FP = np.loadtxt(gm_FP_path)
    gm_FN = file_FN[:, 1] / 1000 / 9.8
    gm_FP = file_FP[:, 1] / 1000 / 9.8
    record_FN = eqsig.AccSignal(gm_FN, dt)
    record_FP = eqsig.AccSignal(gm_FP, dt)
    record_FN.generate_response_spectrum(response_times=periods)
    record_FP.generate_response_spectrum(response_times=periods)
    times = record_FN.response_times

    # find the bigger ground motion among FN and FP
    if np.max(record_FN.s_a) > np.max(record_FP.s_a):
        record = record_FN
    else:
        record = record_FP

    # 2.1
    axs.plot(times, record.s_a, color="silver", linewidth=1)

    sum_spectrum_1 += record.s_a



for i, gm_folder in enumerate(tqdm(os.listdir(root_2))):
    gm_name = gm_folder
    gm_FN_path = os.path.join(root_2, gm_folder, gm_name + "_FN.txt")
    gm_FP_path = os.path.join(root_2, gm_folder, gm_name + "_FP.txt")
    print(i, gm_FN_path, gm_FP_path)
    file_FN = np.loadtxt(gm_FN_path)
    file_FP = np.loadtxt(gm_FP_path)
    gm_FN = file_FN[:, 1] / 1000 / 9.8
    gm_FP = file_FP[:, 1] / 1000 / 9.8
    record_FN = eqsig.AccSignal(gm_FN, dt)
    record_FP = eqsig.AccSignal(gm_FP, dt)
    record_FN.generate_response_spectrum(response_times=periods)
    record_FP.generate_response_spectrum(response_times=periods)
    times = record_FN.response_times

    # find the bigger ground motion among FN and FP
    if np.max(record_FN.s_a) > np.max(record_FP.s_a):
        record = record_FN
    else:
        record = record_FP

    # 2.1
    axs.plot(times, record.s_a, color="silver", linewidth=1)

    sum_spectrum_2 += record.s_a




# Plot the mean spectrum & Design Spectrum
mean_spectrum_1 = sum_spectrum_1 / ground_motion_count_1
mean_spectrum_2 = sum_spectrum_2 / ground_motion_count_2
axs.plot(times, design_spectrum_BSE1, color="black", linewidth=2, label="DBE (10%/50y)")
axs.plot(times, design_spectrum_BSE2, color="blue", linewidth=2, label="MCE (2%/50y)")
axs.plot(times, mean_spectrum_1, color="red", linewidth=2, label="Mean Scaled DBE")
axs.plot(times, mean_spectrum_2, color="orange", linewidth=2, label="Mean Scaled MCE")
axs.set_xlim([-0.1, 3])
axs.axvline(0.3, color='r', linewidth=1, linestyle="dashed")
axs.axvline(1.3, color='r', linewidth=1, linestyle="dashed")




plt.legend()
plt.xlabel("T (sec)")
plt.ylabel("Sa (g)")
plt.xlim([-0.1, 2.0])
# plt.title(f"{name} Response Spectrum -- BSE-1 vs. BSE-2")


plt.savefig(r"E:\TimeHistoryAnalysis\Time-History-Analysis\Visualization\scaled_spectrum\new2_scaled_BSE-1_BSE-2.png")
# plt.show()





