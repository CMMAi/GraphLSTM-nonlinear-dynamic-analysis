import torch
from torch_geometric.loader import DataLoader
from .normalization import *
from .accuracy import *
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
from sklearn.manifold import TSNE


# https://stackoverflow.com/questions/31478077/how-to-make-two-markers-share-the-same-label-in-the-legend-using-matplotlib

class AnyObject(object):
    pass


class data_handler(object):
    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        scale = fontsize / 22






def visualize_response(model, ckpt_dir, dataset, dataset_name, norm_dict, accuracy, response, index):  
    print(f"Visualizing {dataset_name} -- structure_{index} --  {response}......", flush=True)
    # Make directory
    save_dir = ckpt_dir / dataset_name / f"structure_{index}" / response  # /train/structure_0/Acceleration/
    save_dir.mkdir(parents=True, exist_ok=True)
    
    device = "cuda"
    g = dataset[index]
    loader = DataLoader([g], batch_size=1)
    # batch = next(iter(loader))
    batch = g.clone().to(device)
    batch.ptr = torch.tensor([0, batch.x.shape[0]]).to(device)
    batch.sampled_index = [batch.sampled_index]
    batch.batch = torch.zeros(batch.x.shape[0]).to(device).to(torch.int64)
    model.eval()

    with torch.no_grad():
        output, keeped_indexes = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch, batch.ptr, batch.sampled_index, batch.ground_motions, sample_node=False)
        x, y = batch.x[keeped_indexes], batch.y[keeped_indexes]
    

    if response == "Acceleration_X":
        # normalized scale
        pred_norm = output[:, :, 0]
        true_norm = y[:, :, 0]
        # original scale
        pred = denormalize_acc(pred_norm, norm_dict)
        true = denormalize_acc(true_norm, norm_dict)

    elif response == "Velocity_X":
        # normalized scale
        pred_norm = output[:, :, 2]
        true_norm = y[:, :, 2]
        # original scale
        pred = denormalize_vel(pred_norm, norm_dict)
        true = denormalize_vel(true_norm, norm_dict)

    elif response == "Displacement_X":
        # normalized scale
        pred_norm = output[:, :, 4]
        true_norm = y[:, :, 4]
        # original scale
        pred = denormalize_disp(pred_norm, norm_dict)
        true = denormalize_disp(true_norm, norm_dict)

    elif response == "Displacement_Z":
        # normalized scale
        pred_norm = output[:, :, 5]
        true_norm = y[:, :, 5]
        # original scale
        pred = denormalize_disp(pred_norm, norm_dict)
        true = denormalize_disp(true_norm, norm_dict)

    elif response == "Moment_Z_Column":
        # Display momentZ on y_n.
        # normalized scale
        pred_norm = output[:, :, 8]
        true_norm = y[:, :, 8]
        # original scale
        pred = denormalize_moment(pred_norm, norm_dict)
        true = denormalize_moment(true_norm, norm_dict)

    elif response == "Moment_Z_Xbeam":
        # Display momentZ on x_p.
        # normalized scale
        pred_norm = output[:, :, 7]
        true_norm = y[:, :, 7]
        # original scale
        pred = denormalize_moment(pred_norm, norm_dict)
        true = denormalize_moment(true_norm, norm_dict)

    elif response == "Moment_Z_Zbeam":
        # Display momentZ on z_p.
        # normalized scale
        pred_norm = output[:, :, 11]
        true_norm = y[:, :, 11]
        # original scale
        pred = denormalize_moment(pred_norm, norm_dict)
        true = denormalize_moment(true_norm, norm_dict)

    elif response == "Shear_Y_Column":
        # Display shearY on y_n.
        # normalized scale
        pred_norm = output[:, :, 14]
        true_norm = y[:, :, 14]
        # original scale
        pred = denormalize_shear(pred_norm, norm_dict)
        true = denormalize_shear(true_norm, norm_dict)

    elif response == "Shear_Z_Xbeam":
        # Display shearY on x_p.
        # normalized scale
        pred_norm = output[:, :, 13]
        true_norm = y[:, :, 13]
        # original scale
        pred = denormalize_shear(pred_norm, norm_dict)
        true = denormalize_shear(true_norm, norm_dict)

    elif response == "Shear_Z_Zbeam":
        # Display shearY on z_p.
        # normalized scale
        pred_norm = output[:, :, 17]
        true_norm = y[:, :, 17]
        # original scale
        pred = denormalize_shear(pred_norm, norm_dict)
        true = denormalize_shear(true_norm, norm_dict)


    # num of grid(3) + grid index(3)
    original_x = denormalize_x(x[:, :6], norm_dict)
    original_ground_motion_1 = denormalize_ground_motion(batch.ground_motions, norm_dict).cpu().detach().numpy()
    timeline = (np.arange(original_ground_motion_1.shape[1])+1) * 0.05

    # Plot
    x_grid_num, y_grid_num, z_grid_num = original_x[0, 0:3].cpu().numpy().astype(int)  

    # Eeach story print diagonal nodes.
    for story in range(1, y_grid_num):
        # print("\n" * 5)
        # print(f"Now is printing {story}F......")
        save_story_dir = save_dir / f"{story}F"
        save_story_dir.mkdir(parents=True, exist_ok=True)
        for x_z_coord in range(min(x_grid_num, z_grid_num)):
            node_index = None
            grid_coord = np.array([x_z_coord, story, x_z_coord])
            for i in range(original_x.shape[0]):
                # find the node whose grid index = [x_grid, story, z_grid]
                if (original_x[i, 3:6].cpu().numpy() == grid_coord).all():
                    node_index = i
                    break     
            
            # If the node is not found, continue.
            if(node_index is None): continue
            
            pred_story = pred[node_index, :]
            true_story = true[node_index, :]
            story_MSE = normalized_MSE(pred_story, true_story)
            story_acc = accuracy(pred_story, true_story)
            pred_story = pred_story.cpu().detach().numpy()
            true_story = true_story.cpu().detach().numpy()

            plt.figure(figsize=(30, 8))
            # Set general font size
            plt.rcParams['font.size'] = '20'

            plt.plot(timeline, true_story, label="true", color="silver", linewidth=3)
            plt.plot(timeline, pred_story, label="pred", color="black", linewidth=1)

            plt.legend(loc="upper right")
            plt.grid()
            plt.xlabel("Time(sec)", fontsize=18)
            plt.ylabel(f"{response}", fontsize=18)
            plt.title(f"{dataset_name} dataset \n{story}F, N{node_index+1}, {response} \n normMSE = {story_MSE:.4f} \n R2_Score = {story_acc:.3f}", fontsize=14)
            plt.savefig(save_story_dir / f"N{node_index+1}_{response}.png")
            plt.close()
















'''
def visualize_response(model, ckpt_dir, dataset, dataset_name, norm_dict, accuracy, response, index):  
    print(f"Visualizing {dataset_name} -- structure_{index} --  {response}......")
    # Make directory
    save_dir = ckpt_dir / dataset_name / f"structure_{index}" / response  # /train/structure_0/Acceleration/
    save_dir.mkdir(parents=True, exist_ok=True)
    
    device = "cuda"
    g = dataset[index]
    loader = DataLoader([g], batch_size=1)
    # batch = next(iter(loader))
    batch = g.clone().to(device)
    batch.ptr = torch.tensor([0, batch.x.shape[0]]).to(device)
    batch.sampled_index = [batch.sampled_index]
    batch.batch = torch.zeros(batch.x.shape[0]).to(device).to(torch.int64)
    model.eval()

    with torch.no_grad():
        output, keeped_indexes = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch, batch.ptr, batch.sampled_index, batch.ground_motions, sample_node=False)
        x, y = batch.x[keeped_indexes], batch.y[keeped_indexes]
    
    if response == "Displacement_X":
        # normalized scale
        pred_norm = output[:, :, 4]
        true_norm = y[:, :, 4]
        # original scale
        pred = denormalize_disp(pred_norm, norm_dict)
        true = denormalize_disp(true_norm, norm_dict)

    elif response == "Displacement_Z":
        # normalized scale
        pred_norm = output[:, :, 5]
        true_norm = y[:, :, 5]
        # original scale
        pred = denormalize_disp(pred_norm, norm_dict)
        true = denormalize_disp(true_norm, norm_dict)

    elif response == "Moment_Z_Column":
        # Display momentZ on y_n.
        # normalized scale
        pred_norm = output[:, :, 8]
        true_norm = y[:, :, 8]
        My_face_norm = x[:, 20]
        # original scale
        pred = denormalize_moment(pred_norm, norm_dict)
        true = denormalize_moment(true_norm, norm_dict)
        My_face = denormalize_moment(My_face_norm, norm_dict).cpu().numpy()

    elif response == "Moment_Z_Xbeam":
        # Display momentZ on x_p.
        # normalized scale
        pred_norm = output[:, :, 7]
        true_norm = y[:, :, 7]
        My_face_norm = x[:, 18]
        # original scale
        pred = denormalize_moment(pred_norm, norm_dict)
        true = denormalize_moment(true_norm, norm_dict)
        My_face = denormalize_moment(My_face_norm, norm_dict).cpu().numpy()

    elif response == "Moment_Z_Zbeam":
        # Display momentZ on z_p.
        # normalized scale
        pred_norm = output[:, :, 11]
        true_norm = y[:, :, 11]
        My_face_norm = x[:, 26]
        # original scale
        pred = denormalize_moment(pred_norm, norm_dict)
        true = denormalize_moment(true_norm, norm_dict)
        My_face = denormalize_moment(My_face_norm, norm_dict).cpu().numpy()


    # num of grid(3) + grid index(3)
    original_x = denormalize_x(x[:, :6], norm_dict)
    original_ground_motion_1 = denormalize_ground_motion(batch.ground_motions, norm_dict).cpu().detach().numpy()
    timeline = (np.arange(original_ground_motion_1.shape[1])+1) * 0.05

    # Plot
    x_grid_num, y_grid_num, z_grid_num = original_x[0, 0:3].cpu().numpy().astype(int)  

    # Eeach story print diagonal nodes.
    for story in range(1, y_grid_num):
        # print("\n" * 5)
        # print(f"Now is printing {story}F......")
        save_story_dir = save_dir / f"{story}F"
        save_story_dir.mkdir(parents=True, exist_ok=True)
        for x_z_coord in range(min(x_grid_num, z_grid_num)):
            node_index = None
            grid_coord = np.array([x_z_coord, story, x_z_coord])
            for i in range(original_x.shape[0]):
                # find the node whose grid index = [x_grid, story, z_grid]
                if (original_x[i, 3:6].cpu().numpy() == grid_coord).all():
                    node_index = i
                    break     
            
            # If the node is not found, continue.
            if(node_index is None): continue
            
            pred_story = pred[node_index, :]
            true_story = true[node_index, :]
            story_MSE = normalized_MSE(pred_story, true_story)
            story_acc = accuracy(pred_story, true_story)
            pred_story = pred_story.cpu().detach().numpy()
            true_story = true_story.cpu().detach().numpy()

            plt.figure(figsize=(30, 8))
            # Set general font size
            plt.rcParams['font.size'] = '16'

            plt.plot(timeline, true_story, label="true", color="silver", linewidth=3)
            plt.plot(timeline, pred_story, label="pred", color="black", linewidth=1)

            if response in ['Moment_Z_Column', 'Moment_Z_Xbeam', 'Moment_Z_Zbeam']:
                My = np.array([My_face[node_index] for _ in timeline])
                plt.plot(timeline, My, color='red', linewidth=1, linestyle='--', label='My')
                plt.plot(timeline, -My, color='red', linewidth=1, linestyle='--')

            plt.legend(loc="upper right")
            plt.grid()
            plt.xlabel("Time(sec)", fontsize=18)
            plt.ylabel(f"{response}", fontsize=18)
            plt.title(f"{dataset_name} dataset \n{story}F, N{node_index+1}, {response} \n normMSE = {story_MSE:.4f} \n R2_Score = {story_acc:.3f}", fontsize=14)
            plt.savefig(save_story_dir / f"N{node_index+1}_{response}.png")
            plt.close()
'''




def visualize_ground_motion(ckpt_dir, dataset, dataset_name, norm_dict, index):  
    print(f"Visualizing {dataset_name} -- structure_{index} --  Gruond Motion......")
    # Make directory
    save_dir = ckpt_dir / dataset_name / f"structure_{index}"  # /train/structure_0/
    save_dir.mkdir(parents=True, exist_ok=True)

    
    device = "cuda"
    g = dataset[index]
    graph = g.clone().to(device)
    original_ground_motion_1 = denormalize_ground_motion(graph.ground_motions[:, :, 0:10].squeeze(), norm_dict).cpu().detach().numpy()
    original_ground_motion_2 = denormalize_ground_motion(graph.ground_motions[:, :, 10:20].squeeze(), norm_dict).cpu().detach().numpy()
    timeline = (np.arange(original_ground_motion_1.shape[0])+1) * 0.05

    # First ground motion shape
    plt.figure(figsize=(30, 8))
    plt.plot(timeline, original_ground_motion_1[:, 0], color='black', linewidth=1)
    plt.xlabel("Time(sec)")
    plt.ylabel("Acceleration")
    plt.title(graph.gm_X_name)
    plt.grid()
    plt.savefig(save_dir / "ground_motion_X.png")
    plt.close()

    # Second ground motion shape
    plt.figure(figsize=(30, 8))
    plt.plot(timeline, original_ground_motion_2[:, 0], color='black', linewidth=1)
    plt.xlabel("Time(sec)")
    plt.ylabel("Acceleration")
    plt.title(graph.gm_Z_name)
    plt.grid()
    plt.savefig(save_dir / "ground_motion_Z.png")
    plt.close()





def visualize_plasticHinge(model, ckpt_dir, dataset, dataset_name, norm_dict, classifier, index):

    print(f"Visualizing {dataset_name} -- structure_{index} --  plastic hinge......")
    # Make directory
    save_dir = ckpt_dir / dataset_name / f"structure_{index}" / "plastic_hinge"  # /train/structure_0/plastic_hinge/
    save_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda"
    g = dataset[index]
    batch = g.clone().to(device)
    batch.ptr = [0, batch.x.shape[0]]
    batch.batch = torch.zeros(batch.x.shape[0]).to(device).to(torch.int64)
    model.eval()

    with torch.no_grad():
        output, keeped_indexes = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch, batch.ptr, batch.sampled_index, batch.ground_motions, sample_node=False)
        x, y = batch.x[keeped_indexes], batch.y[keeped_indexes]

    # Plot
    original_x = denormalize_x(x[:, :6], norm_dict)
    x_grid_num, y_grid_num, z_grid_num = original_x[0, 0:3].cpu().numpy().astype(int) 
    
    print(batch.path)
    
    for z in range(z_grid_num):
        fig, axs = plt.subplots(1, 2, figsize=(24, 10))
        fig.suptitle(f"Plastic Hinge Visualization --- Z{z} Section", fontsize=19, fontweight='bold')

        for y in range(y_grid_num):
            for x in range(x_grid_num):
                grid_coord = np.array([x, y, z])                
                node_index = 0
                for i in range(batch.x.shape[0]):
                    if (original_x[i, 3:6].cpu().numpy() == grid_coord).all():
                        node_index = i
                        break

                # Plot structure skeleton -- beam (0F no beam)
                if x != x_grid_num - 1 and y != 0:
                    # Get x_p section My
                    My_x_p = batch.x[node_index, classifier.Myield_start_index + 1 * classifier.section_info_dim].cpu().numpy()
                    # print(f"Node num: {node_index+1},", f"{x} {y} {z}, ", graph.x[node_index, classifier.Myield_start_index:classifier.Myield_start_index+6])
                    color = 1 - (My_x_p - 0.3) / 0.7 * 0.8
                    axs[0].plot([x, x+1], [y, y], linewidth=5, color=(color, color, color), marker='o', markerfacecolor='k', markersize=10, zorder=1)
                    axs[1].plot([x, x+1], [y, y], linewidth=5, color=(color, color, color), marker='o', markerfacecolor='k', markersize=10, zorder=1)


        for x in range(x_grid_num):   
            for y in range(y_grid_num):   
                grid_coord = np.array([x, y, z])            
                node_index = 0
                for i in range(batch.x.shape[0]):
                    if (original_x[i, 3:6].cpu().numpy() == grid_coord).all():
                        node_index = i
                        break

                # Plot structure skeleton -- column
                if y != y_grid_num - 1:
                    # Get y_p section My
                    My_y_p = batch.x[node_index, classifier.Myield_start_index + 3 * classifier.section_info_dim].cpu().numpy()
                    color = 1 - (My_y_p - 0.3) / 0.7 * 0.8
                    axs[0].plot([x, x], [y, y+1], linewidth=5, color=(color, color, color), marker='o', markerfacecolor='k', markersize=10, zorder=1)
                    axs[1].plot([x, x], [y, y+1], linewidth=5, color=(color, color, color), marker='o', markerfacecolor='k', markersize=10, zorder=1)
                    
                
                # Plot plastic hinge
                for i, face_index in enumerate(list(range(2, 8))):   # face_index is index for Mz(x_n, x_p, y_n, y_p, z_n, z_p)
                    Myield_face_i = batch.x[node_index, classifier.Myield_start_index + i * classifier.section_info_dim]
                    if Myield_face_i <= 0.1:     # It means this face is not connect to any element.
                        continue
                    pred_node_plastic_hinge = torch.max(output[node_index, :, face_index].abs()) >= classifier.yield_factor * Myield_face_i
                    real_node_plastic_hinge = torch.max(batch.y[node_index, :, face_index].abs()) >= classifier.yield_factor * Myield_face_i

                   
                    if real_node_plastic_hinge:
                        if i == 0:
                            axs[0].add_artist(plt.Circle((x - 0.2, y), 0.05, fill=True, color='red'))
                        elif i == 1:
                            axs[0].add_artist(plt.Circle((x + 0.2, y), 0.05, fill=True, color='red'))
                        elif i == 2:
                            axs[0].add_artist(plt.Circle((x, y - 0.2), 0.05, fill=True, color='red'))
                        elif i == 3:
                            axs[0].add_artist(plt.Circle((x, y + 0.2), 0.05, fill=True, color='red'))

                    if pred_node_plastic_hinge:
                        if i == 0:
                            axs[1].add_artist(plt.Circle((x - 0.2, y), 0.05, fill=True, color='red'))
                        elif i == 1:
                            axs[1].add_artist(plt.Circle((x + 0.2, y), 0.05, fill=True, color='red'))
                        elif i == 2:
                            axs[1].add_artist(plt.Circle((x, y - 0.2), 0.05, fill=True, color='red'))
                        elif i == 3:
                            axs[1].add_artist(plt.Circle((x, y + 0.2), 0.05, fill=True, color='red'))


        axs[0].set_xlabel('x axis (mm)')
        axs[0].set_ylabel('y axis (mm)')
        axs[0].set_xlim((-1, x_grid_num))
        axs[0].set_title("TRUE")

        axs[1].set_xlabel('x axis (mm)')
        axs[1].set_ylabel('y axis (mm)')
        axs[1].set_xlim((-1, x_grid_num))
        axs[1].set_title("PREDICTION")

        plt.savefig(save_dir / f"Z{z}.png")
        plt.close()



def visualize_graph_attention(model, ckpt_dir, dataset, dataset_name, norm_dict, head_num, index):
    print(f"Visualizing {dataset_name} -- structure_{index} --  graph attention weights......")
    # Make directory
    save_dir = ckpt_dir / dataset_name / f"structure_{index}"  # /train/structure_0/attention_head_0.png
    save_dir.mkdir(parents=True, exist_ok=True)
    
    device = "cuda"
    g = dataset[index]
    loader = DataLoader([g], batch_size=1)
    batch = next(iter(loader))
    batch = g.clone().to(device)
    batch.ptr = torch.tensor([0, batch.x.shape[0]]).to(device)
    batch.sampled_index = [batch.sampled_index]
    batch.batch = torch.zeros(batch.x.shape[0]).to(device).to(torch.int64)
    model.eval()

    with torch.no_grad():
        x, return_edge_index, attention_weights = model.graphLatentEncoder(batch.x, batch.edge_index, batch.edge_attr, batch.batch)    
    
    x_denorm = denormalize_x(batch.x[:, :6], norm_dict)
    x_coord = x_denorm[:,3].cpu().numpy()
    y_coord = x_denorm[:,5].cpu().numpy()
    z_coord = x_denorm[:,4].cpu().numpy()

    for head in range(head_num):
        node_color = attention_weights[batch.edge_index.size(-1):, head].cpu().numpy()
        edge_color = attention_weights[:batch.edge_index.size(-1), head].cpu().numpy()
        edge_pos_xyz = np.array([((x_coord[u]/2 + x_coord[v]/2), (y_coord[u]/2 + y_coord[v]/2).item(), (z_coord[u]/2 + z_coord[v]/2).item(), 
            x_coord[v].item(), y_coord[v].item(), z_coord[v].item()) for u, v in batch.edge_index.T])

        fig = plt.figure(figsize=(15, 15), facecolor="w")
        ax = fig.add_subplot(111, projection="3d", facecolor="w")
        ax.set_axis_off()
        # plot nodes
        p = ax.scatter(x_coord, y_coord, z_coord, c = node_color, s = 250, alpha = 0.75, edgecolors='black', cmap='Greys')
        ax.set_box_aspect((np.ptp(x_coord), np.ptp(y_coord), np.ptp(z_coord)))
        # plot edges
        for e, color in zip(edge_pos_xyz, edge_color):
            xx = [e[0], e[3]] 
            yy = [e[1], e[4]]
            zz = [e[2], e[5]]
            ax.plot(xx, yy, zz, c='grey', linewidth=10*color if 10*color >= 0.5 else 0.5)

        cbar = fig.colorbar(p, shrink=0.5, aspect=5, pad = 0)
        cbar.ax.tick_params(labelsize=15)
        cbar.set_label("Attention Weights", size=24,)
        plt.savefig(save_dir / f"attention_head_{head}.png")
        plt.close()




def visualize_graph_embedding(model, ckpt_dir, dataset, dataset_name, norm_dict, batch_size):
    print(f"Visualizing {dataset_name} --  graph embedding tsne......")
    # Make directory
    save_dir = ckpt_dir / dataset_name / "graph_embedding_tsne"  # /train/graph_embedding_tsne/period.png
    save_dir.mkdir(parents=True, exist_ok=True)
    
    device = "cuda"
    loader = DataLoader(dataset, batch_size=batch_size)
    model.eval()
    graph_embedding = torch.tensor([]).to(device)
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            x, _, _ = model.graphLatentEncoder(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
            graph_embedding = torch.cat([graph_embedding, x], dim=0)
    graph_embedding = graph_embedding.cpu().numpy()
    print("graph embedding shape:", graph_embedding.shape)
        
    label1 = np.array([graph.x[0, 0].item() for graph in dataset]) * norm_dict["grid_num"][1] - 1
    label2 = np.array([graph.x[0, 1].item() for graph in dataset]) * norm_dict["grid_num"][1] - 1 
    label3 = np.array([graph.x[0, 2].item() for graph in dataset]) * norm_dict["grid_num"][1] - 1
    label4 = np.array([graph.x[0, 11].item() for graph in dataset]) * norm_dict["period"][1]
    label5 = np.array([graph.x[0, 12].item() for graph in dataset]) * norm_dict["period"][1]
    label6 = np.array([graph.x[0, 13].item() for graph in dataset]) * norm_dict["period"][1]
    label7 = np.array([len(graph.x) for graph in dataset]) 
    
    def plot_TSNE(tsne, label, color, name):
        plt.figure(figsize=(10,10), facecolor="w")
        plt.scatter(tsne[:,0], tsne[:,1], c = label, s = 100, alpha = 0.75, cmap='viridis')
        plt.xticks([])
        plt.yticks([])
        cbar = plt.colorbar()
        cbar.set_label(color, size=15,)
        plt.savefig(save_dir / f"{name}.png")
        plt.close()
        
    tsne = TSNE(n_components=2, init='random', perplexity=40, n_iter=1000).fit_transform(graph_embedding)
    plot_TSNE(tsne, label1, color = "X span number", name="x_span_num")
    plot_TSNE(tsne, label2, color = "Story number", name="story_num")
    plot_TSNE(tsne, label3, color = "Z span number", name="z_span_num")
    plot_TSNE(tsne, label4, color = "1st period", name="1st_period")
    plot_TSNE(tsne, label5, color = "2nd period", name="2nd_period")
    plot_TSNE(tsne, label6, color = "3rd period", name="3rd_period")
    plot_TSNE(tsne, label7, color = "Number of nodes", name="node_num")