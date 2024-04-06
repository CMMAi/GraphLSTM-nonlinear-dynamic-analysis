import os
import numpy as np
import matplotlib.pyplot as plt
import eqsig.single
from pathlib import Path



gm_folder = Path("E:/TimeHistoryAnalysis/Data/GroundMotions_ChiChi")
save_folder = Path(r"E:\TimeHistoryAnalysis\Time-History-Analysis\Visualization\ground_motions")


dt = 0.005
periods = np.linspace(0.01, 10, 100)


for i, gm_file in enumerate(os.listdir(gm_folder)[:10]):
    gm_path = gm_folder / gm_file
    print("ploting:", gm_path)

    # find the scale factor
    file = np.loadtxt(gm_path)
    gm = file[:, 1] / 1000 / 9.8    # Here divide by 1000 and 9.8 is to plot the curve in terms of g
    # record_FN = eqsig.AccSignal(gm, dt)
    # record_FN.generate_response_spectrum(response_times=periods)

    save_path = save_folder / f"{gm_file}.png"
    plt.figure(figsize=(12, 4))
    plt.plot(gm, color="black", linewidth=2)
    plt.savefig(save_path)




