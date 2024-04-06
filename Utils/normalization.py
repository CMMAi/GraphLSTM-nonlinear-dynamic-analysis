import torch
from torch_geometric.loader import DataLoader
from copy import deepcopy
import random


def get_norm_dict(dataset, norm_dict):
    loader = DataLoader(dataset, batch_size=len(dataset))
    graph = next(iter(loader))
    ground_motion_1, ground_motion_2, x, y, edge_attr = graph.ground_motion_1, graph.ground_motion_2, graph.x, graph.y, graph.edge_attr        

    # ground motion
    min_ground_motion = 0
    max_ground_motion_1 = torch.max(torch.abs(ground_motion_1)).item()
    max_ground_motion_2 = torch.max(torch.abs(ground_motion_2)).item()
    max_ground_motion = max(max_ground_motion_1, max_ground_motion_2)
    norm_dict['ground_motion'] = [min_ground_motion, max_ground_motion]

    # x
    min_grid_num = 0
    max_grid_num = torch.max(torch.abs(x[:, :3])).item()
    norm_dict['grid_num'] = [min_grid_num, max_grid_num]
    
    min_coord = 0
    max_coord = torch.max(torch.abs(x[:, 3:6])).item()
    norm_dict['coord'] = [min_coord, max_coord]

    min_period = 0
    max_period = torch.max(torch.abs(x[:, 11:14])).item()
    norm_dict['period'] = [min_period, max_period]

    min_modal_shape = 0
    max_modal_shape = torch.max(torch.abs(x[:, 14:23])).item()
    norm_dict['modal_shape'] = [min_modal_shape, max_modal_shape]


    min_length = 0
    max_length = torch.max(torch.abs(x[:, list(range(23, 35, 2))])).item()
    norm_dict['elem_length'] = [min_length, max_length]


    # y
    min_acc = 0
    max_acc = torch.max(torch.abs(y[:, :, 0:2])).item()
    norm_dict['acc'] = [min_acc, max_acc]

    min_vel = 0
    max_vel = torch.max(torch.abs(y[:, :, 2:4])).item()
    norm_dict['vel'] = [min_vel, max_vel]

    min_disp = 0
    max_disp = torch.max(torch.abs(y[:, :, 4:6])).item()
    norm_dict['disp'] = [min_disp, max_disp]
    
    # Here normalize response momentZ with each section's My_z (yielding moment)
    min_moment = 0
    max_moment = torch.max(torch.max(torch.abs(y[:, :, 6:12])), torch.max(torch.abs(x[:, list(range(24, 35, 2))]))).item()
    norm_dict['moment'] = [min_moment, max_moment]

    min_shear = 0
    max_shear = torch.max(torch.abs(y[:, :, 12:18])).item()
    norm_dict['shear'] = [min_shear, max_shear]
    
    return norm_dict



def normalize(original_graph, norm_dict):
    graph = deepcopy(original_graph)
    graph.ground_motion_1 = (graph.ground_motion_1 - norm_dict['ground_motion'][0]) / (norm_dict['ground_motion'][1] - norm_dict['ground_motion'][0])
    graph.ground_motion_2 = (graph.ground_motion_2 - norm_dict['ground_motion'][0]) / (norm_dict['ground_motion'][1] - norm_dict['ground_motion'][0])

    graph.x[:, :3] = (graph.x[:, :3] - norm_dict['grid_num'][0]) / (norm_dict['grid_num'][1] - norm_dict['grid_num'][0])
    graph.x[:, 3:6] = (graph.x[:, 3:6] - norm_dict['coord'][0]) / (norm_dict['coord'][1] - norm_dict['coord'][0])
    graph.x[:, 11:14] = (graph.x[:, 11:14] - norm_dict['period'][0]) / (norm_dict['period'][1] - norm_dict['period'][0])
    graph.x[:, 14:23] = (graph.x[:, 14:23] - norm_dict['modal_shape'][0]) / (norm_dict['modal_shape'][1] - norm_dict['modal_shape'][0])
   
    graph.x[:, list(range(23, 35, 2))] = (graph.x[:, list(range(23, 35, 2))] - norm_dict['elem_length'][0]) / (norm_dict['elem_length'][1] - norm_dict['elem_length'][0])
    graph.x[:, list(range(24, 35, 2))] = (graph.x[:, list(range(24, 35, 2))] - norm_dict['moment'][0]) / (norm_dict['moment'][1] - norm_dict['moment'][0])

    graph.y[:, :, 0:2] = (graph.y[:, :, 0:2] - norm_dict['acc'][0]) / (norm_dict['acc'][1] - norm_dict['acc'][0])
    graph.y[:, :, 2:4] = (graph.y[:, :, 2:4] - norm_dict['vel'][0]) / (norm_dict['vel'][1] - norm_dict['vel'][0])
    graph.y[:, :, 4:6] = (graph.y[:, :, 4:6] - norm_dict['disp'][0]) / (norm_dict['disp'][1] - norm_dict['disp'][0])
    graph.y[:, :, 6:12] = (graph.y[:, :, 6:12] - norm_dict['moment'][0]) / (norm_dict['moment'][1] - norm_dict['moment'][0])
    graph.y[:, :, 12:18] = (graph.y[:, :, 12:18] - norm_dict['shear'][0]) / (norm_dict['shear'][1] - norm_dict['shear'][0])

    graph.edge_attr[:, 0] = (graph.edge_attr[:, 0] - norm_dict['elem_length'][0]) / (norm_dict['elem_length'][1] - norm_dict['elem_length'][0])
    graph.edge_attr[:, 3] = (graph.edge_attr[:, 3] - norm_dict['moment'][0]) / (norm_dict['moment'][1] - norm_dict['moment'][0])

    gm_X_direction = graph.gm_X_name.split('_')[-1].replace('.txt', '')
    if gm_X_direction == 'FN':
        gm_Z_direction = 'FP'
    elif gm_X_direction == 'FP':
        gm_Z_direction = 'FN'
    else:
        raise ValueError("wrong ground motion direction")
    graph.gm_Z_name = graph.gm_X_name.replace(gm_X_direction, gm_Z_direction)

    graph.x = graph.x[:, 0:35]
    graph.ground_motions = torch.cat([graph.ground_motion_1, graph.ground_motion_2], dim=1)
    graph.ground_motions = graph.ground_motions.unsqueeze(0)
    timesteps = graph.ground_motions.shape[1]
    graph.y = graph.y[:, :timesteps, :]
    assert graph.x.shape[1] == 35
    assert graph.y.shape[2] == 18

    return graph



def structureSampling(normed_graph, norm_dict, random_sample):
    graph = deepcopy(normed_graph)

    # if random sample
    if random_sample:
        node_num = graph.x.shape[0]
        sampled_rate = 0.1
        sampled_num = int(node_num * sampled_rate)
        indexes = list(range(node_num))
        random.shuffle(indexes)
        sampled_indexes = indexes[:sampled_num]
        sampled_indexes.sort()
        graph.sampled_index = tuple(sampled_indexes)
        return graph

    # if not random sample
    # Sampled the node on the zigzag path in each story.  
    x_grid_num, y_grid_num, z_grid_num = graph.grid_num.numpy().astype(int)
    x_grid_num, z_grid_num = x_grid_num - 1, z_grid_num - 1
    sampled_xz_coord = []
    if_x_more = True if x_grid_num >= z_grid_num else False
    x = 0
    z = 0
    increase = False
    while((x <= x_grid_num) if if_x_more else (z <= z_grid_num)):
        sampled_xz_coord.append([x, z])

        # Check if need to change direction of zigzag.
        if (if_x_more and (z == 0 or z == z_grid_num)) or (not if_x_more and (x == 0 or x == x_grid_num)):
            increase = not increase

        # Update the zigzag pointer
        if increase:
            x += 1
            z += 1
        else:
            if if_x_more:
                x += 1
                z -= 1
            else:
                x -= 1
                z += 1

    sampled_node_index = []
    topology = denormalize_x(graph.x[:, :6], norm_dict)
    for index in range(graph.x.shape[0]):
        # Check if node's x, z grid coord is in the zigzag path.
        x_grid, y_grid, z_grid = topology[index, 3:6].cpu().numpy()
        if  [x_grid, z_grid] in sampled_xz_coord:
            sampled_node_index.append(index)

    # Reduce the number of sampled node for more data number.
    sampled_node_index = [index for i, index in enumerate(sampled_node_index) if i%2==0]

    # Now we don't sample the node here. We first save the info about which node shoud be sampled later.
    # sampled_index = torch.zeros(graph.x.shape[0])
    # for index in sampled_node_index:
    #     sampled_index[index] = 1
    # graph.sampled_index = sampled_index

    graph.sampled_index = tuple(sampled_node_index)

    return graph




# Normalize the whole dataset.
def normalize_dataset(dataset, random_sample=False):
    norm_dict = dict()
    norm_dict = get_norm_dict(dataset, norm_dict)
    normed_dataset = []

    for graph in dataset:
        graph_norm = normalize(graph, norm_dict)
        graph_norm = structureSampling(graph_norm, norm_dict, random_sample)
        normed_dataset.append(graph_norm)

    return normed_dataset, norm_dict




# def normalize_with_normDict(norm_dict, dataset, reduce_sample=True, threshold=0.9):
#     for key in norm_dict.keys():
#         max_value = norm_dict[key]
#         norm_dict[key] = [0, max_value]

#     new_dataset = []
#     sampled_dataset = []

#     for graph_original in dataset:
#         graph_norm = normalize(graph_original, norm_dict)
#         new_dataset.append(graph_norm)
#         graph_sample, _ = structureSampling(graph_norm, norm_dict, reduce_sample)
#         sampled_dataset.append(graph_sample)

#     return new_dataset, sampled_dataset, norm_dict




# normalize
def normalize_coord(coord, norm_dict):
    norm_coord = (coord - norm_dict['coord'][0]) / (norm_dict['coord'][1] - norm_dict['coord'][0])
    return norm_coord




# denormalize
def denormalize(norm_graph, norm_dict):
    graph = deepcopy(norm_graph)

    graph[:, :3] = graph[:, :3] * (norm_dict['grid_num'][1] - norm_dict['grid_num'][0]) + norm_dict['grid_num'][0]
    graph[:, 3:6] = graph[:, 3:6] * (norm_dict['coord'][1] - norm_dict['coord'][0]) + norm_dict['coord'][0]
    graph[:, 11:14] = graph[:, 11:14] * (norm_dict['period'][1] - norm_dict['period'][0]) + norm_dict['period'][0]
    graph[:, 14:23] = graph[:, 14:23] * (norm_dict['modal_shape'][1] - norm_dict['modal_shape'][0]) + norm_dict['modal_shape'][0]
    graph[:, list(range(23, 35, 2))] = graph[:, list(range(23, 35, 2))] * (norm_dict['elem_length'][1] - norm_dict['elem_length'][0]) + norm_dict['elem_length'][0]
    graph[:, list(range(24, 35, 2))] = graph[:, list(range(24, 35, 2))] * (norm_dict['moment'][1] - norm_dict['moment'][0]) + norm_dict['moment'][0]

    return graph
  


def denormalize_ground_motion(norm_gm, norm_dict):
    gm = deepcopy(norm_gm)
    gm = gm * (norm_dict['ground_motion'][1] - norm_dict['ground_motion'][0]) + norm_dict['ground_motion'][0]    
    return gm

def denormalize_grid_num(norm_x, norm_dict):
    x = deepcopy(norm_x)
    x = x * (norm_dict['grid_num'][1] - norm_dict['grid_num'][0]) + norm_dict['grid_num'][0]
    return x

def denormalize_x(norm_x, norm_dict):
    x = deepcopy(norm_x)
    x[:, :3] = x[:, :3] * (norm_dict['grid_num'][1] - norm_dict['grid_num'][0]) + norm_dict['grid_num'][0]
    x[:, 3:6] = x[:, 3:6] * (norm_dict['coord'][1] - norm_dict['coord'][0]) + norm_dict['coord'][0]
    return x


def denormalize_acc(norm_acc, norm_dict):
    acc = deepcopy(norm_acc)
    acc = acc * (norm_dict['acc'][1] - norm_dict['acc'][0]) + norm_dict['acc'][0]
    return acc

def denormalize_vel(norm_vel, norm_dict):
    vel = deepcopy(norm_vel)
    vel = vel * (norm_dict['vel'][1] - norm_dict['vel'][0]) + norm_dict['vel'][0]
    return vel

def denormalize_disp(norm_disp, norm_dict):
    disp = deepcopy(norm_disp)
    disp = disp * (norm_dict['disp'][1] - norm_dict['disp'][0]) + norm_dict['disp'][0]
    return disp

def denormalize_moment(norm_moment, norm_dict):
    moment = deepcopy(norm_moment)
    moment = moment * (norm_dict['moment'][1] - norm_dict['moment'][0]) + norm_dict['moment'][0]
    return moment

def denormalize_shear(norm_shear, norm_dict):
    shear = deepcopy(norm_shear)
    shear = shear * (norm_dict['shear'][1] - norm_dict['shear'][0]) + norm_dict['shear'][0]
    return shear




