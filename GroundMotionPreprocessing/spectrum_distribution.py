import numpy as np
import matplotlib.pyplot as plt
import os
import eqsig.single




root_1 = "E:/TimeHistoryAnalysis/Data/GroundMotions_ChiChi_processed_BSE-1"
root_2 = "E:/TimeHistoryAnalysis/Data/GroundMotions_ChiChi_processed_BSE-2"
name = "ChiChi_Taipei3"



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
fig, axs = plt.subplots(1, 2, figsize=(20, 8))
ground_motion_count_1 = len(os.listdir(root_1))
ground_motion_count_2 = len(os.listdir(root_2))

for i, gm_folder in enumerate(os.listdir(root_1)):
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
    axs[0].plot(times, record.s_a, color="silver", linewidth=1)

    # 2.2
    freq = (1 / times)[::-1]
    reverse_sa = record.s_a[::-1]
    axs[1].plot(freq, reverse_sa, color="silver", linewidth=1)

    sum_spectrum_1 += record.s_a



for i, gm_folder in enumerate(os.listdir(root_2)):
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
    axs[0].plot(times, record.s_a, color="silver", linewidth=1)

    # 2.2
    freq = (1 / times)[::-1]
    reverse_sa = record.s_a[::-1]
    axs[1].plot(freq, reverse_sa, color="silver", linewidth=1)

    sum_spectrum_2 += record.s_a




# Plot the mean spectrum & Design Spectrum
mean_spectrum_1 = sum_spectrum_1 / ground_motion_count_1
mean_spectrum_2 = sum_spectrum_2 / ground_motion_count_2
axs[0].plot(times, design_spectrum_BSE1, color="black", linewidth=2, label="BSE-1 (10%/50y)")
axs[0].plot(times, design_spectrum_BSE2, color="blue", linewidth=2, label="BSE-2 (2%/50y)")
axs[0].plot(times, mean_spectrum_1, color="red", linewidth=2, label="Mean Scaled BSE-1")
axs[0].plot(times, mean_spectrum_2, color="orange", linewidth=2, label="Mean Scaled BSE-2")
axs[1].plot(freq, design_spectrum_BSE1[::-1], color="black", linewidth=2, label="BSE-1 (10%/50y)")
axs[1].plot(freq, design_spectrum_BSE2[::-1], color="blue", linewidth=2, label="BSE-2 (2%/50y)")
axs[1].plot(freq, mean_spectrum_1[::-1], color="red", linewidth=2, label="Mean Scaled BSE-1")
axs[1].plot(freq, mean_spectrum_2[::-1], color="orange", linewidth=2, label="Mean Scaled BSE-2")



axs[0].legend()
axs[0].set_xlabel("T (sec)")
axs[0].set_ylabel("Sa (G)")
axs[0].set_title(f"{name} Response Spectrum -- BSE-1 vs. BSE-2")

axs[1].legend()
axs[1].set_xlabel("Frequency (Hz)")
axs[1].set_ylabel("Sa (G)")
axs[1].set_xscale("log")
axs[1].set_yscale("log")
axs[1].set_title(f"{name} Response Spectrum (log scale) -- BSE-1 vs. BSE-2")

plt.savefig(f"Spectrums/{name}_BSE1_BSE_2_spectrum.png")
plt.show()





