import torch
from torch_geometric.data import Data
import os
from os.path import join
from multiprocessing import Pool
import time
from structure import *
import sections_tw, sections_usa



def generate(args):
    target_dir, structure_dir, structure_index, section_country = args
    print(f"Generating {target_dir}/{structure_index:04d} strucutre graph")
    
    # set section type
    if section_country == "USA":
        beam_sections = sections_usa.beam_sections
        column_sections = sections_usa.column_sections
        beam_section_dict = sections_usa.beam_section_dict
        column_section_dict = sections_usa.column_section_dict
    elif section_country == "Taiwan":
        beam_sections = sections_tw.beam_sections
        column_sections = sections_tw.column_sections
        beam_section_dict = sections_tw.beam_section_dict
        column_section_dict = sections_tw.column_section_dict
    else:
        raise ValueError("wrong sections country!")

    # path of structure_xxx folder
    folder_name = join(target_dir, structure_dir)


    force_file_path = join(folder_name, 'STRUCTURE.ElemRecord')
    if os.path.exists(force_file_path) == False or os.path.exists(join(folder_name, "STRUCTURE.VISA3D")):    
        return
    force_file = open(force_file_path, 'r').readlines()

    # If .ElemRecord is empty, then skip.
    elem_file_stat = os.stat(force_file_path)
    elem_file_size = elem_file_stat.st_size / 1024 / 1024
    if elem_file_size < 10:
        print(f"Structure index: {structure_index} has no elem_file, skip it.")
        return


    input_file_path = join(folder_name, 'structure.ipt')
    input_file = open(input_file_path, 'r').readlines()

    eigen_file_path = join(folder_name, 'MODAL.Eigen')
    eigen_file = open(eigen_file_path, 'r').readlines()

    modal_file_path = join(folder_name, 'MODAL.Modal')
    modal_file = open(modal_file_path, 'r').readlines()

    acc_file_path = join(folder_name, 'STRUCTURE.NodeAccRecord')
    acc_file = open(acc_file_path, 'r').readlines()

    vel_file_path = join(folder_name, 'STRUCTURE.NodeVelRecord')
    vel_file = open(vel_file_path, 'r').readlines()

    displacement_file_path = join(folder_name, 'STRUCTURE.NodeDisRecord')
    displacement_file = open(displacement_file_path, 'r').readlines()
    

    # get node and member information
    node_dict = {}
    node_count = 0
    node_grid_dict = {}
    node_coord_dict = {}
    node_dof_dict = {}
    node_mass_dict = {}      
    member_node_dict = {}    
    member_section_dict = {}  
    member_length_dict = {}
    beta_x_dict = {}
    beta_z_dict = {}
    edge_i, edge_j = [], []
    edge_attr = []  
    x_grid_index, y_grid_index, z_grid_index = [], [], []


    for line in input_file:
        contents = line.split()
        if len(contents) == 0: continue
        
        if contents[0] == 'GUI_GRID':
            if contents[1] == 'XDIR':
                x_grid_index = [int(num) for num in contents[2:]]
            elif contents[1] == 'YDIR':
                y_grid_index = [int(num) for num in contents[2:]]
            elif contents[1] == 'ZDIR':
                z_grid_index = [int(num) for num in contents[2:]]
                
        
        if contents[0] == 'Node' and contents[1][0] != 'M':
            node_name = contents[1]
            node_dict[node_name] = node_count
            node_coord_dict[node_name] = [float(contents[2])/1000, float(contents[3])/1000, float(contents[4])/1000]
            node_grid_dict[node_name] = [x_grid_index.index(int(contents[2])), y_grid_index.index(int(contents[3])), z_grid_index.index(int(contents[4]))]
            node_count += 1


        elif contents[0] == 'DOF' and contents[1][0] != 'M':
            dof = [int(contents[2]), int(contents[3]), int(contents[4]), int(contents[5]), int(contents[6]), int(contents[7])]
            if dof == [-1, -1, -1, -1, -1, -1]:   
                node_dof_dict[contents[1]] = 1
                
                
        elif contents[0] == '#NodeMass':
            mass, Rx, Ry, Rz = float(contents[3]), float(contents[6]), float(contents[7]), float(contents[8])
            node_mass_dict[contents[2]] = [mass, Rx, Ry, Rz]


        elif contents[0] == '#StrongColumnWeakBeamRatio':
            node_name = contents[1]
            beta_x_dict[node_name] = float(contents[2])
            beta_z_dict[node_name] = float(contents[3])
            
            
        elif contents[0] == 'Element':
            node1, node2 = node_dict[contents[3]], node_dict[contents[4]]
            edge_i.append(node1)
            edge_j.append(node2)
            edge_i.append(node2)
            edge_j.append(node1)

            member_name = contents[2]
            section_name = contents[5]
            member_node_dict[member_name] = [contents[3], contents[4]]
            member_section_dict[member_name] = section_name

            # BeamColumn length
            x1, y1, z1 = node_coord_dict[contents[3]]
            x2, y2, z2 = node_coord_dict[contents[4]]
            member_length = abs(x1-x2) + abs(y1-y2) + abs(z1-z2)
            member_length_dict[member_name] = member_length

            # add edge_attr: [member_length, is_beam, is_column, My]
            # USA beam: W21x93, USA column: 16x16x0.875
            # Taiwan beam: 400x200x9x16, Taiwan column: 400x400x20
            member_edge_attr = [member_length]
            if section_name.count('x') == 1 or section_name.count('x') == 3:  # is beam
                member_edge_attr.append(1)
                member_edge_attr.append(0)
                member_edge_attr.append(beam_section_dict[section_name]['My_z(kN-mm)'])
            elif section_name.count('x') == 2: # is column:
                member_edge_attr.append(0)
                member_edge_attr.append(1)
                member_edge_attr.append(column_section_dict[section_name]['My_z(kN-mm)'])
            else:
                raise ValueError(f"No member category: {section_name}")

            edge_attr.append(member_edge_attr)
            edge_attr.append(member_edge_attr)

    edge_index = torch.tensor([edge_i, edge_j], dtype=torch.long)
    edge_attr = torch.tensor(edge_attr, dtype=torch.float)
    


    # Get ground_motion name
    gm_X_name = None
    gm_Z_name = None
    for line in input_file:
        contents = line.split()
        if(len(contents) > 1 and contents[1] == "GroundAccel"):
            if gm_X_name is None:
                gm_X_name = contents[3]
            else:
                gm_Z_name = contents[3]
            break


    # get if_bottom, if_top, if_side
    if_bottom_dict = {}
    if_top_dict = {}
    if_side_dict = {}
    for node_name in node_grid_dict.keys():
        x_grid, y_grid, z_grid = node_grid_dict[node_name]
        if y_grid == 0:
            if_bottom_dict[node_name] = 1
        else:
            if_bottom_dict[node_name] = 0
        
        if y_grid == len(y_grid_index) - 1:
            if_top_dict[node_name] = 1
        else:
            if_top_dict[node_name] = 0
        
        if x_grid == 0 or x_grid == len(x_grid_index) - 1 or z_grid == 0 or z_grid == len(z_grid_index) - 1:
            if_side_dict[node_name] = 1
        else:
            if_side_dict[node_name] = 0


    # Prepare output file for data.x, data.y
    # 1st mode shape
    first_mode_shape_dict = {}
    second_mode_shape_dict = {}
    third_mode_shape_dict = {}
    for line in modal_file:
        contents = line.split(",")
        if contents[1][0] == "N":
            if contents[0] == "Mode1":
                first_mode_shape_dict[contents[1]] = [float(contents[2]), float(contents[3]), float(contents[4])]
            elif contents[0] == "Mode2":
                second_mode_shape_dict[contents[1]] = [float(contents[2]), float(contents[3]), float(contents[4])]
            elif contents[0] == "Mode3":
                third_mode_shape_dict[contents[1]] = [float(contents[2]), float(contents[3]), float(contents[4])]


    # Natural Period
    first_mode_period = None
    second_mode_period = None
    third_mode_period = None
    for line in eigen_file:
        contents = line.split(",")
        if contents[0] == "FirstModePeriod":
            first_mode_period = float(contents[1])
        elif contents[0] == "SecondModePeriod":
            second_mode_period = float(contents[1])
        elif contents[0] == "ThirdModePeriod":
            third_mode_period = float(contents[1])


    # Acceleration
    node_acc_dict = {}
    for line in acc_file:
        contents = line.split(",")
        if len(contents) == 0: continue
        if contents[0] in node_dict.keys():
            node = contents[0]
            if node in node_acc_dict.keys():
                tensor = torch.zeros((1, 2))
                tensor[0][0] = float(contents[2])
                tensor[0][1] = float(contents[3])
                node_acc_dict[node] = torch.cat([node_acc_dict[node], tensor], dim=0)
            else:
                node_acc_dict[node] = torch.zeros((1, 2))
                node_acc_dict[node][0][0] = float(contents[2])
                node_acc_dict[node][0][1] = float(contents[3])
            
    # Velocity
    node_vel_dict = {}
    for line in vel_file:
        contents = line.split(",")
        if len(contents) == 0: continue
        if contents[0] in node_dict.keys():
            node = contents[0]
            if node in node_vel_dict.keys():
                tensor = torch.zeros((1, 2))
                tensor[0][0] = float(contents[2])
                tensor[0][1] = float(contents[3])
                node_vel_dict[node] = torch.cat([node_vel_dict[node], tensor], dim=0)
            else:
                node_vel_dict[node] = torch.zeros((1, 2))
                node_vel_dict[node][0][0] = float(contents[2])
                node_vel_dict[node][0][1] = float(contents[3])
            
    # Displacement
    node_displacement_dict = {}
    for line in displacement_file:
        contents = line.split(",")
        if len(contents) == 0: continue
        if contents[0] in node_dict.keys():
            node = contents[0]
            if node in node_displacement_dict.keys():
                tensor = torch.zeros((1, 2))
                tensor[0][0] = float(contents[2])
                tensor[0][1] = float(contents[3])
                node_displacement_dict[node] = torch.cat([node_displacement_dict[node], tensor], dim=0)
            else:
                node_displacement_dict[node] = torch.zeros((1, 2))
                node_displacement_dict[node][0][0] = float(contents[2])
                node_displacement_dict[node][0][1] = float(contents[3])
            
    try:
        timestep = node_displacement_dict["N1"].shape[0]
    except:
        print(f"Structure index: {structure_index} has some bug, skip it.")
        return

    
    # Get Force
    # First create Rigid Zones
    RigidZones = {}
    for node_name in node_dict.keys():
        RigidZones[node_name] = RigidZone(node_name=node_name, timestep=timestep)
        
    for line in force_file:
        contents = line.split(",")
        if len(contents) == 0: continue
        if contents[0] in member_node_dict.keys():
            member_name = contents[0]
            time_index = int(float(contents[1])/0.05 - 1 + 0.5)
            node1, node2 = member_node_dict[member_name]
            x1, y1, z1 = node_coord_dict[node1]
            x2, y2, z2 = node_coord_dict[node2]


            # Then calculate the relationship of the 2 nodes.
            if x1 != x2:
                # This is a x-beam
                assert x1 < x2
                
                # node1: x_p --> momentY(i), moementZ(i), shearY(i), shearZ(i), plastic hinge(i)
                # Node1 uses positive x to catch beam_i
                RigidZones[node1].face_dict['x_p']['momentY'][time_index] = float(contents[6])
                RigidZones[node1].face_dict['x_p']['momentZ'][time_index] = float(contents[4])
                RigidZones[node1].face_dict['x_p']['shearY'][time_index] = float(contents[8])
                RigidZones[node1].face_dict['x_p']['shearZ'][time_index] = float(contents[10])
                RigidZones[node1].face_dict['x_p']['length'] = member_length_dict[member_name]
                RigidZones[node1].face_dict['x_p']['Myield'] = beam_section_dict[member_section_dict[member_name]]['My_z(kN-mm)']

                
                # node2: x_n --> momentY(j), moementZ(j), shearY(j), shearZ(j), plastic hinge(j)
                # Node2 uses negative x to catch beam_j
                RigidZones[node2].face_dict['x_n']['momentY'][time_index] = float(contents[7])
                RigidZones[node2].face_dict['x_n']['momentZ'][time_index] = float(contents[5])
                RigidZones[node2].face_dict['x_n']['shearY'][time_index] = float(contents[9])
                RigidZones[node2].face_dict['x_n']['shearZ'][time_index] = float(contents[11])
                RigidZones[node2].face_dict['x_n']['length'] = member_length_dict[member_name]
                RigidZones[node2].face_dict['x_n']['Myield'] = beam_section_dict[member_section_dict[member_name]]['My_z(kN-mm)']
                
                
            elif z1 != z2:
                # This is a z-beam
                assert z1 < z2
                
                # node1: z_p --> momentY(i), moementZ(i), shearY(i), shearZ(i), plastic hinge(i)
                # Node1 uses positive z to catch beam_i
                RigidZones[node1].face_dict['z_p']['momentY'][time_index] = float(contents[6])
                RigidZones[node1].face_dict['z_p']['momentZ'][time_index] = float(contents[4])
                RigidZones[node1].face_dict['z_p']['shearY'][time_index] = float(contents[8])
                RigidZones[node1].face_dict['z_p']['shearZ'][time_index] = float(contents[10])
                RigidZones[node1].face_dict['z_p']['length'] = member_length_dict[member_name]
                RigidZones[node1].face_dict['z_p']['Myield'] = beam_section_dict[member_section_dict[member_name]]['My_z(kN-mm)']

                
                # node2: z_n --> momentY(j), moementZ(j), shearY(j), shearZ(j), plastic hinge(j)
                # Node2 uses negative z to catch beam_j
                RigidZones[node2].face_dict['z_n']['momentY'][time_index] = float(contents[7])
                RigidZones[node2].face_dict['z_n']['momentZ'][time_index] = float(contents[5])
                RigidZones[node2].face_dict['z_n']['shearY'][time_index] = float(contents[9])
                RigidZones[node2].face_dict['z_n']['shearZ'][time_index] = float(contents[11])
                RigidZones[node2].face_dict['z_n']['length'] = member_length_dict[member_name]
                RigidZones[node2].face_dict['z_n']['Myield'] = beam_section_dict[member_section_dict[member_name]]['My_z(kN-mm)']
                
                
            elif y1 != y2:
                # This is a column
                assert y1 < y2
                
                # node1: y_p --> momentY(i), moementZ(i), shearY(i), shearZ(i), plastic hinge(i)
                # Node1 uses positive y to catch column_i
                RigidZones[node1].face_dict['y_p']['momentY'][time_index] = float(contents[6])
                RigidZones[node1].face_dict['y_p']['momentZ'][time_index] = float(contents[4])
                RigidZones[node1].face_dict['y_p']['shearY'][time_index] = float(contents[8])
                RigidZones[node1].face_dict['y_p']['shearZ'][time_index] = float(contents[10])
                RigidZones[node1].face_dict['y_p']['length'] = member_length_dict[member_name]
                RigidZones[node1].face_dict['y_p']['Myield'] = column_section_dict[member_section_dict[member_name]]['My_z(kN-mm)']
                
                # node2: y_n --> momentY(j), moementZ(j), shearY(j), shearZ(j), plastic hinge(j)
                # Node2 uses negative y to catch column_j
                RigidZones[node2].face_dict['y_n']['momentY'][time_index] = float(contents[7])
                RigidZones[node2].face_dict['y_n']['momentZ'][time_index] = float(contents[5])
                RigidZones[node2].face_dict['y_n']['shearY'][time_index] = float(contents[9])
                RigidZones[node2].face_dict['y_n']['shearZ'][time_index] = float(contents[11])
                RigidZones[node2].face_dict['y_n']['length'] = member_length_dict[member_name]
                RigidZones[node2].face_dict['y_n']['Myield'] = column_section_dict[member_section_dict[member_name]]['My_z(kN-mm)']

                
            else:
                raise ValueError("There should be some difference between 2 nodes' coordinate!")
       
    



    grid_num = torch.tensor([len(x_grid_index), len(y_grid_index), len(z_grid_index)])

    # data.x: XYZ grid nums(3), node_grid(3), if_bottom(1), if_top(1), if_side(1), beta(2), period(3), Ux_Uz_Ry(3*3), section_info_per_face(2*6), ground_motion_x(10), ground_motion_z(10)
    # data.y: disp(2), momentZ(6)
    # data.x_y_z_gird: grid_num(3)
    section_info_dim = 2
    x = torch.zeros((node_count, 23 + section_info_dim * 6))  # 35
    y = torch.zeros((node_count, timestep, 18))

    for line in input_file:
        contents = line.split()
        if len(contents) == 0: continue
        
        if contents[0] == 'Node' and contents[1][0] != 'M':
            node_index = node_dict[contents[1]]
            node_name = contents[1]
            
            # structure X, Y, Z grid nums
            x[node_index, 0] = len(x_grid_index)
            x[node_index, 1] = len(y_grid_index)
            x[node_index, 2] = len(z_grid_index)
            
            
            # node coordinates
            x[node_index, 3] = node_grid_dict[contents[1]][0]
            x[node_index, 4] = node_grid_dict[contents[1]][1]
            x[node_index, 5] = node_grid_dict[contents[1]][2]


            # if bottom, if top, if side
            x[node_index, 6] = if_bottom_dict[node_name]
            x[node_index, 7] = if_top_dict[node_name]
            x[node_index, 8] = if_side_dict[node_name]
                
                
            # beta_x, beta_z
            x[node_index, 9] = beta_x_dict[node_name]
            x[node_index, 10] = beta_z_dict[node_name]
            
            
            # natural period
            x[node_index, 11] = first_mode_period
            x[node_index, 12] = second_mode_period
            x[node_index, 13] = third_mode_period


            # 1st mode shape (Ux, Uz, Ry)
            x[node_index, 14] = first_mode_shape_dict[node_name][0]
            x[node_index, 15] = first_mode_shape_dict[node_name][1]
            x[node_index, 16] = first_mode_shape_dict[node_name][2]
            x[node_index, 17] = second_mode_shape_dict[node_name][0]
            x[node_index, 18] = second_mode_shape_dict[node_name][1]
            x[node_index, 19] = second_mode_shape_dict[node_name][2]
            x[node_index, 20] = third_mode_shape_dict[node_name][0]
            x[node_index, 21] = third_mode_shape_dict[node_name][1]
            x[node_index, 22] = third_mode_shape_dict[node_name][2]
            
        
            # Section information
            for i, face in enumerate(['x_n', 'x_p', 'y_n', 'y_p', 'z_n', 'z_p']):
                start_index = 23 + i * section_info_dim
                x[node_index, start_index] = RigidZones[node_name].face_dict[face]['length']
                x[node_index, start_index+1] = RigidZones[node_name].face_dict[face]['Myield']
                


            # y:

            '''
            # disp_x, disp_z
            y[node_index, :, 0:2] = node_displacement_dict[node_name]
            
            # momentZ
            y[node_index, :, 2] = RigidZones[node_name].face_dict['x_n']['momentZ']
            y[node_index, :, 3] = RigidZones[node_name].face_dict['x_p']['momentZ']
            y[node_index, :, 4] = RigidZones[node_name].face_dict['y_n']['momentZ']
            y[node_index, :, 5] = RigidZones[node_name].face_dict['y_p']['momentZ']
            y[node_index, :, 6] = RigidZones[node_name].face_dict['z_n']['momentZ']
            y[node_index, :, 7] = RigidZones[node_name].face_dict['z_p']['momentZ']
            '''


            # Acc, Vel, Disp
            y[node_index, :, 0:2] = node_acc_dict[node_name]
            y[node_index, :, 2:4] = node_vel_dict[node_name]
            y[node_index, :, 4:6] = node_displacement_dict[node_name]

            # Moment Z
            y[node_index, :, 6] = RigidZones[node_name].face_dict['x_n']['momentZ']
            y[node_index, :, 7] = RigidZones[node_name].face_dict['x_p']['momentZ']
            y[node_index, :, 8] = RigidZones[node_name].face_dict['y_n']['momentZ']
            y[node_index, :, 9] = RigidZones[node_name].face_dict['y_p']['momentZ']
            y[node_index, :, 10] = RigidZones[node_name].face_dict['z_n']['momentZ']
            y[node_index, :, 11] = RigidZones[node_name].face_dict['z_p']['momentZ']
            
            # ShearY
            y[node_index, :, 12] = RigidZones[node_name].face_dict['x_n']['shearY']
            y[node_index, :, 13] = RigidZones[node_name].face_dict['x_p']['shearY']
            y[node_index, :, 14] = RigidZones[node_name].face_dict['y_n']['shearY']
            y[node_index, :, 15] = RigidZones[node_name].face_dict['y_p']['shearY']
            y[node_index, :, 16] = RigidZones[node_name].face_dict['z_n']['shearY']
            y[node_index, :, 17] = RigidZones[node_name].face_dict['z_p']['shearY']

            
                
    # print(x)
    # print(y)
    
    # Make above data into a torch_geometric.data.Data object
    data = Data(x=x, y=y, edge_index=edge_index, edge_attr=edge_attr, grid_num=grid_num, path=folder_name, gm_X_name=gm_X_name, gm_Z_name=gm_Z_name)
    # print(gm_name)
    # print(data)
    torch.save(data, join(folder_name, 'structure_graph_NodeAsNode.pt'))





def check_if_pt_file_already_exist(target_dir, structure_dir):
    folder_name = join(target_dir, structure_dir)
    graph_name = "structure_graph_NodeAsNode.pt"
    if graph_name in os.listdir(folder_name):
        print(f"folder {folder_name} already has graph......")
        return True
    return False




final_extension_list = ['ipt', 'pt', 'txt']
def delete_useless_files_after_graph(target_dir):
    for structure_dir in os.listdir(target_dir):
        structure_dir = os.path.join(target_dir, structure_dir)
        print(f"Start deleting {structure_dir} useless files......")
        for analysis_file in os.listdir(structure_dir):
            file_name = os.path.join(structure_dir, analysis_file)
            extension = analysis_file.split('.')[1]
            if extension not in final_extension_list:
                os.remove(file_name)




def generate_graph_NodeAsNode(target_dir, start_index, section_country):
    processes = 6
    print(f"Start generating graph, processes: {processes}......")

    p_pool = []

    for index, structure_dir in enumerate(sorted(os.listdir(target_dir))):
        structure_index = int(structure_dir.split('_')[1])
        if structure_index < start_index:  continue
        if check_if_pt_file_already_exist(target_dir, structure_dir): continue
        args = (target_dir, structure_dir, structure_index, section_country)
        p_pool.append(args)

    with Pool(processes=processes) as p:
        for i in p.imap_unordered(generate, p_pool):
            time.sleep(0.1)

    delete_useless_files_after_graph(target_dir)


    


    

