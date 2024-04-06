import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from PIL import Image
from DataGeneration.sections_tw import *



def _visualize_one_timestep_disp(geo_graph, disp_x_gt, disp_z_gt, disp_x_pred, disp_z_pred, t, save_path):

    scale_factor = 5.0

    # set ground node displacement as 0
    node_per_story = geo_graph["node_per_story"]
    disp_x_pred[:node_per_story] = 0
    disp_z_pred[:node_per_story] = 0

    # nodes
    x_coord = list(geo_graph["geo_x"][:, 0])
    y_coord = list(geo_graph["geo_x"][:, 1])
    z_coord = list(geo_graph["geo_x"][:, 2])
    x_max = max(x_coord)
    y_max = max(y_coord)
    z_max = max(z_coord)


    # plot 3d
    fig = plt.figure(figsize=(20, 15), facecolor="w")
    gs = fig.add_gridspec(17, 8)

    # first plot ground truth
    ax = fig.add_subplot(gs[1:13, 0:4], projection="3d", facecolor="w")
    ax.set_axis_off()

    # nodes
    x_coord_gt = [x + disp * scale_factor for x, disp in zip(x_coord, disp_x_gt)]
    y_coord_gt = y_coord
    z_coord_gt = [z + disp * scale_factor for z, disp in zip(z_coord, disp_z_gt)]
    ax.scatter(x_coord_gt, z_coord_gt, y_coord_gt, color="black", s=200, alpha=0.75, edgecolors="black")
    ax.set_box_aspect((np.ptp(x_coord_gt), np.ptp(z_coord_gt), np.ptp(y_coord_gt)))

    # edges
    for i, (node_i, node_j) in enumerate(geo_graph["geo_edge"]):
        xx = [x_coord_gt[node_i], x_coord_gt[node_j]]
        yy = [y_coord_gt[node_i], y_coord_gt[node_j]]
        zz = [z_coord_gt[node_i], z_coord_gt[node_j]]
        section_name = geo_graph["section_names"][i]
        if section_name in beam_section_dict:
            color = beam_section_dict[section_name]["color"]
        else:
            color = column_section_dict[section_name]["color"]
        color = (color[0]/255, color[1]/255, color[2]/255)
        ax.plot(xx, zz, yy, c=(color), linewidth=6)
    
    ax.set_xlim([-0.05 * x_max, 1.05 * x_max])
    ax.set_ylim([-0.05 * z_max, 1.05 * z_max])
    ax.set_zlim([0, 1.05 * y_max])
    ax.set_title(f"Ground Truth", fontsize=30)



    # then plot prediction
    ax = fig.add_subplot(gs[1:13, 4:8], projection="3d", facecolor="w")
    ax.set_axis_off()

    # nodes
    x_coord_pred = [x + disp * scale_factor for x, disp in zip(x_coord, disp_x_pred)]
    y_coord_pred = y_coord
    z_coord_pred = [z + disp * scale_factor for z, disp in zip(z_coord, disp_z_pred)]
    ax.scatter(x_coord_pred, z_coord_pred, y_coord_pred, color="black", s=200, alpha=0.75, edgecolors="black")
    ax.set_box_aspect((np.ptp(x_coord_pred), np.ptp(z_coord_pred), np.ptp(y_coord_pred)))

    # edges
    for i, (node_i, node_j) in enumerate(geo_graph["geo_edge"]):
        xx = [x_coord_pred[node_i], x_coord_pred[node_j]]
        yy = [y_coord_pred[node_i], y_coord_pred[node_j]]
        zz = [z_coord_pred[node_i], z_coord_pred[node_j]]
        section_name = geo_graph["section_names"][i]
        if section_name in beam_section_dict:
            color = beam_section_dict[section_name]["color"]
        else:
            color = column_section_dict[section_name]["color"]
        color = (color[0]/255, color[1]/255, color[2]/255)
        ax.plot(xx, zz, yy, c=(color), linewidth=6)

    ax.set_xlim([-0.05 * x_max, 1.05 * x_max])
    ax.set_ylim([-0.05 * z_max, 1.05 * z_max])
    ax.set_zlim([0, 1.05 * y_max])
    ax.set_title(f"AI Prediction", fontsize=30)


    # lastly, the ground motion
    timesteps = geo_graph["gm1"].shape[0]
    times = np.arange(timesteps) / 20
    ax = fig.add_subplot(gs[12:14, 1:7])
    ax.plot(times, geo_graph['gm1'][:, 0], color='k')
    ax.axvline(t/20, color='r', linewidth=3)
    ax.set_title("Earthquakes (X, Y)", fontsize=26)
    ax.grid()
    ax.set_xticklabels([])
    ax.set_ylabel("X (g)", fontsize=21, rotation=0)
    ax.tick_params(axis='y', labelsize=16)

    ax = fig.add_subplot(gs[14:16, 1:7])
    ax.plot(times, geo_graph['gm2'][:, 0], color='k')
    ax.axvline(t/20, color='r', linewidth=3)
    ax.grid()
    ax.set_xlabel("Time (sec)", fontsize=22)
    ax.set_ylabel("Y (g)", fontsize=21, rotation=0)
    ax.tick_params(axis='x', labelsize=16)
    ax.tick_params(axis='y', labelsize=16)


    fig.tight_layout()
    plt.suptitle(f"scale factor: {scale_factor}\nTime = {t/20:6.2f} (s)", fontsize=30)
    plt.savefig(save_path)
    plt.close()


def _disp_frames_to_video(save_dir, frame_paths, steps=1):
    frames = [Image.open(name) for name in frame_paths]
    last_frame = frames[-1]
    frames += [last_frame] * 100
    gm_frequency = 20 / steps   # 20 per seond
    frame_duration_ms = int(1000 / gm_frequency)    # 50 for default
    frame_one = frames[0]
    frame_one.save(save_dir / "displacement_animation.gif", format="GIF", append_images=frames, save_all=True, duration=frame_duration_ms, loop=0)


def make_displacement_animation(graph, geo_graph, response, save_dir):

    save_disp_dir = save_dir / "displacement"
    save_disp_dir.mkdir(parents=True, exist_ok=True)

    # first get the disp of ground truth and prediction
    disp_x_gt = graph.y[:, :, 4].numpy()
    disp_z_gt = graph.y[:, :, 5].numpy()
    disp_x_pred = response[:, :, 4]
    disp_z_pred = response[:, :, 5]

    timesteps = response.shape[1]
    saved_frame_paths = []
    steps = 5
    
    for t in tqdm(range(0, timesteps, steps)):
        disp_t_path = save_disp_dir / f"disp_{t}.png"
        saved_frame_paths.append(disp_t_path)
        _visualize_one_timestep_disp(geo_graph, 
                                     disp_x_gt[:, t], disp_z_gt[:, t], 
                                     disp_x_pred[:, t], disp_z_pred[:, t],
                                     t, disp_t_path)

    _disp_frames_to_video(save_dir, saved_frame_paths, steps)



