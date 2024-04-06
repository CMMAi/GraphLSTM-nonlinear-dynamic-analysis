import numpy as np
import matplotlib.pyplot as plt
import os
from os.path import join
from tqdm import tqdm
import eqsig.single


source = "World"
name = "BSE-2"

source_gm_folder = f"E:/TimeHistoryAnalysis/Data/GroundMotions_{source}_processed"
target_gm_folder = f"E:/TimeHistoryAnalysis/Data/GroundMotions_{source}_processed_{name}"


maximum_tolerant_Sa = 1.5 if name == "BSE-1" else 1.5 * (4/3)
maximum_tolerant_scale = 4 if name == "BSE-1" else 4 * (4/3)




# 1. define the time range that the mean Sa will be calculated for scaling
min_t = 0.45
max_t = 1.35
main_start, main_end = None, None    # indexes for t = min_t ~ max_t
main_Sa = None                       # mean for Sa between t = min_t ~ max_t




# 2. Calculate design spectrum  (大安區，台北三區)
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


design_spectrum = design_spectrum_BSE1 if name == "BSE-1" else design_spectrum_BSE2
max_value = np.max(design_spectrum)



for i, t in enumerate(periods):
    if main_start == None and t >= min_t:
        main_start = i
    if main_end == None and t > max_t:
        main_end = i

main_Sa = np.sum(design_spectrum[main_start:main_end])

print(f"Index for t = {min_t}, t = {max_t} is i = {main_start}, i = {main_end}, main_Sa = {main_Sa}")






# 3. Find the scaling factor for all of the gm pairs
dt = 0.005
appeared_gm = []
if os.path.exists(target_gm_folder) == False:
    os.mkdir(target_gm_folder)

for i, gm_file in enumerate(os.listdir(source_gm_folder)):
    # get gm name
    gm_name = gm_file.split("_")[0]
    gm_type = gm_file.split("_")[1].replace("txt", "")
    if gm_name in appeared_gm:
        continue
    gm_FN_name = gm_name + "_FN.txt"
    gm_FP_name = gm_name + "_FP.txt"

    # check both FN, FP gm exist
    source_gm_FN_path = join(source_gm_folder, gm_FN_name)
    source_gm_FP_path = join(source_gm_folder, gm_FP_name)
    if os.path.exists(source_gm_FN_path) == False or os.path.exists(source_gm_FP_path) == False:
        print(f"{source_gm_FN_path} or {source_gm_FP_path} does not exist...")
        continue
    appeared_gm.append(gm_name)

    # find the scale factor
    file_FN = np.loadtxt(source_gm_FN_path)
    file_FP = np.loadtxt(source_gm_FP_path)
    gm_FN = file_FN[:, 1] / 1000 / 9.8    # Here divide by 1000 and 9.8 is to plot the curve in terms of g
    gm_FP = file_FP[:, 1] / 1000 / 9.8    # Here divide by 1000 and 9.8 is to plot the curve in terms of g
    record_FN = eqsig.AccSignal(gm_FN, dt)
    record_FP = eqsig.AccSignal(gm_FP, dt)
    record_FN.generate_response_spectrum(response_times=periods)
    record_FP.generate_response_spectrum(response_times=periods)

    sa_sum_FN = np.sum(record_FN.s_a[main_start:main_end])
    sa_sum_FP = np.sum(record_FP.s_a[main_start:main_end])
    scale_factor_FN = main_Sa / sa_sum_FN
    scale_factor_FP = main_Sa / sa_sum_FP

    # one of the direction attain BSE level is enough
    scale_factor = min(scale_factor_FN, scale_factor_FP)
    sa_FN_max = np.max(record_FN.s_a) * scale_factor
    sa_FP_max = np.max(record_FP.s_a) * scale_factor
    sa_max = max(sa_FN_max, sa_FP_max)
    print(f"{i}, {gm_name}, {scale_factor}")

    # Discard the gms that scale to much or the shape are not fitting the design spectrum.
    if scale_factor > maximum_tolerant_scale or scale_factor < 1/maximum_tolerant_scale:
        print(f"\t\t Scaling factor too big or too small: {scale_factor}")
        continue
    elif sa_max > maximum_tolerant_Sa:
        print(f"\t\t Peak Sa: {sa_max}, bigger than tolerant maximum Sa: {maximum_tolerant_Sa}")
        continue 

    # create a subfolder for the 2 ground motions
    target_gm_path = join(target_gm_folder, gm_name)
    if os.path.exists(target_gm_path) == False:
        os.mkdir(target_gm_path)

    # Rewrite the ground motion file with scale_factor
    target_gm_FN_path = join(target_gm_path, gm_FN_name)
    target_gm_FP_path = join(target_gm_path, gm_FP_name)
    new_content_FN = ""
    new_content_FP = ""

    with open(source_gm_FN_path, "r") as f:
        for i, line in enumerate(f.readlines()):
            contents = line.strip().split()
            new_content_FN += f"{float(contents[0]) :.4f}\t{float(contents[1]) * scale_factor :.3f}\n"
    with open(source_gm_FP_path, "r") as f:
        for i, line in enumerate(f.readlines()):
            contents = line.strip().split()
            new_content_FP += f"{float(contents[0]) :.4f}\t{float(contents[1]) * scale_factor :.3f}\n"

    with open(target_gm_FN_path, "w") as f:
        f.write(new_content_FN)
    with open(target_gm_FP_path, "w") as f:
        f.write(new_content_FP)



