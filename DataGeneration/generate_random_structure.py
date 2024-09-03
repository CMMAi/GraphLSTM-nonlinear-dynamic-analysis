import numpy as np
import torch
import random
import os
import shutil
import random
from copy import deepcopy
from structure import *
import sections_tw, sections_usa


# A table which correspond face to node feature's yielding moment face index
FACE_HASH_TABLE = {
    'x_n': 23,
    'x_p': 25,
    'y_n': 27,
    'y_p': 29,
    'z_n': 31,
    'z_p': 33,
}




def _strongColumn_weakBeam_criterion(node_need_beta, node_neighbor_Mp_matrix):
        """Check if all beta is greater than 1."""
        Mpc = node_neighbor_Mp_matrix @ torch.tensor([0, 0, 1, 1, 0, 0]).unsqueeze(1).float()        # [n_n, 6]
        Mpb_x = node_neighbor_Mp_matrix @ torch.tensor([1, 1, 0, 0, 0, 0]).unsqueeze(1).float()      # [n_n, 6]
        Mpb_z = node_neighbor_Mp_matrix @ torch.tensor([0, 0, 0, 0, 1, 1]).unsqueeze(1).float()      # [n_n, 6]
        beta_x = (Mpc / Mpb_x).squeeze()    # [n_n]
        beta_z = (Mpc / Mpb_z).squeeze()    # [n_n]
        beta_pass = torch.min(beta_x[node_need_beta == 1]).item() > 1 and torch.min(beta_z[node_need_beta == 1]).item() > 1
        # first make sure beta passes, then transform beta
        beta_x = torch.tanh(1.0 / beta_x)
        beta_z = torch.tanh(1.0 / beta_z)
        return beta_x, beta_z, beta_pass





def _assign_member_sections(thickest_member_section_list,
                            member_category_list,
                            column_index_list,
                            beam_index_list,
                            member_XZ_dict, 
                            member_same_location_dict, 
                            member_to_nodeIndex_dict, 
                            thickest_node_neighbor_Mp_matrix,
                            node_need_beta,
                            member_group_dict,
                            section_country="USA",
                            prioritized=None):
    """Assign random structure with the qualified sections (pass the strong column-weak beam constraint)."""
    
    if section_country == "USA":
        beam_sections = sections_usa.beam_sections
        column_sections = sections_usa.column_sections
    elif section_country == "Taiwan":
        beam_sections = sections_tw.beam_sections
        column_sections = sections_tw.column_sections
    else:
        raise ValueError("wrong sections country!")

    member_number = len(thickest_member_section_list)
    qualified_designs = []

    current_member_sections = deepcopy(thickest_member_section_list)  # it should be qualified (pass the constraint)
    current_node_neighbor_Mp_matrix = deepcopy(thickest_node_neighbor_Mp_matrix)
    qualified_designs.append(current_member_sections)

    # if 10 consecutive designs cannot pass strong column-weak beam constraint, then stop it
    failed_time = 0
    while failed_time <= 10:
        # if current design is too thin (which means it is hard to reduce), then stop
        if sum(current_member_sections) < member_number * 2:
            break

        # use deepcopy to avoid modifiying the original member_section_list and node_neightbor_Mp_matrix
        member_section_list = deepcopy(current_member_sections)
        node_neighbor_Mp_matrix = deepcopy(current_node_neighbor_Mp_matrix)

        # avoid selecting the member that is already with minimium section
        # the selected update member should mostly be beam rather than column, since column have much fewer section categories.
        # let column prob = 0.15, beam prob = 0.85
        if random.random() < 0.4:
            update_member_index = random.choice(column_index_list)
        else:
            update_member_index = random.choice(beam_index_list)

        while member_section_list[update_member_index] == 0:    
            update_member_index = random.randint(0, member_number - 1)

        # get the update information
        update_member_category = member_category_list[update_member_index]
        new_section_index = member_section_list[update_member_index] - 1
        new_section_info = column_sections[new_section_index] if update_member_category == 'y' else beam_sections[new_section_index]
        
        # get the upper members that needed auto correct.
        auto_correct_needed_members = [update_member_index]
        auto_correct_member_category = [update_member_category]
        member_XZ = member_XZ_dict[update_member_index]
        indexes_in_same_location = member_same_location_dict[member_XZ]
        update_member_in_same_locaion_index = indexes_in_same_location.index(update_member_index)
        for upper_member_index in indexes_in_same_location[update_member_in_same_locaion_index+1:]:
            upper_member_section = member_section_list[upper_member_index]
            upper_member_category = member_category_list[upper_member_index]
            if upper_member_section > new_section_index:
                auto_correct_needed_members.append(upper_member_index)
                auto_correct_member_category.append(upper_member_category)

        # also add same group member into auto correct list
        # currently auto_correct_needed_members contains the update_member_index and the upper beam/columns where their group members also need to be corrected
        group_auto_correct_needed_members = []      # create a temp list to avoid changing the looping auto_correct_needed_members list
        group_auto_correct_member_category = []
        for correct_needed_member in auto_correct_needed_members:
            same_group_members = member_group_dict[correct_needed_member]
            for group_member in same_group_members:
                group_auto_correct_needed_members.append(group_member)
                group_auto_correct_member_category.append(member_category_list[group_member])
        auto_correct_needed_members += group_auto_correct_needed_members
        auto_correct_member_category += group_auto_correct_member_category

        # update node_neighbor_Mp_matrix
        new_Mp = new_section_info['Mp_z(kN-mm)']
        for update_index in auto_correct_needed_members:
            node1_index, node2_index, face_number1, face_number2, _, _ = member_to_nodeIndex_dict[update_index]
            node_neighbor_Mp_matrix[node1_index, face_number1] = new_Mp      
            node_neighbor_Mp_matrix[node2_index, face_number2] = new_Mp

        # check if strong column-weak beam constraint pass
        _, _, beta_pass = _strongColumn_weakBeam_criterion(node_need_beta, node_neighbor_Mp_matrix)

        if not beta_pass: 
            failed_time += 1
            continue
        failed_time = 0
        # if pass, then update member_seciton_list, and add it to qualified_designs and update current list
        for update_index in auto_correct_needed_members:
            member_section_list[update_index] = new_section_index

        qualified_designs.append(deepcopy(member_section_list))
        current_member_sections = deepcopy(member_section_list)
        current_node_neighbor_Mp_matrix = deepcopy(node_neighbor_Mp_matrix)

    # now we have all qualified designs, random pick one as the random struture's section
    qualified_number = len(qualified_designs)
    if prioritized == 'thick':
        selected_index = random.randint(0, int(qualified_number / 10) - 1)
    else:
        selected_index = random.randint(0, qualified_number - 1)
    selected_design = qualified_designs[selected_index]
    print(f"\nselected index: {selected_index} / {qualified_number}")

    return selected_design







def _generate_ipt(modal_file_path,
                  ground_motion_file_1,
                  ground_motion_file_2,
                  environment_parameters,
                  node_neighbor_member_dict,
                  member_section_list,
                  member_category_list,
                  member_to_nodeIndex_dict,
                  beta_x,
                  beta_z,
                  maximum_duration,
                  section_country):
    """Generate modal.ipt""" 
    
    if section_country == "USA":
        beam_sections = sections_usa.beam_sections
        column_sections = sections_usa.column_sections
    elif section_country == "Taiwan":
        beam_sections = sections_tw.beam_sections
        column_sections = sections_tw.column_sections
    else:
        raise ValueError("wrong sections country!")

    node_number = beta_x.shape[0]
    member_number = len(member_section_list)
    
    x_grid, y_grid, z_grid, x_grid_space, y_grid_space, z_grid_space = environment_parameters
    x_grid_string = '  ' + '  '.join([str(x) for x in x_grid])
    y_grid_string = '  ' + '  '.join([str(y) for y in y_grid])
    z_grid_string = '  ' + '  '.join([str(z) for z in z_grid])

    # Collect all node objects
    Nodes = {}

    # 2. Nodes & Master Nodes
    node_count = 0
    node_dict = {}
    node_string = ''
    master_nodes = {}
    master_x, master_z = int(x_grid[-1]/2), int(z_grid[-1]/2)

    for story, y in enumerate(y_grid):
        if story > 0:
            master_name = 'M' + str(story) + 'F'
            master_nodes[master_name] = []
            
        for x in x_grid:
            for z in z_grid:
                node_count += 1
                name = 'N' + str(node_count)
                node_dict[','.join([str(x), str(y), str(z)])] = name
                node_string = node_string + 'Node  ' + name + ' ' + ' '.join([str(x), str(y), str(z)]) + '\n'
                node_neighbor_member_list = node_neighbor_member_dict[node_count - 1]  # node_count starts from 1, 2, 3, but node_index starts from 0, 1, 2, ...
                node_object = Node(environment_parameters=environment_parameters,
                                   name=name, coord=[x, y, z],
                                   node_neighbor_member_list=node_neighbor_member_list,
                                   member_category_list=member_category_list,
                                   member_section_list=member_section_list,
                                   beam_sections=beam_sections, column_sections=column_sections)
                Nodes[name] = node_object
                if story > 0:
                    master_nodes[master_name].append(node_object)
    
    node_string += '\n'
    for story, y in enumerate(y_grid):
        if story > 0:
            master_name = 'M' + str(story) + 'F'
            node_string += 'Node  ' + master_name + ' ' + ' '.join([str(master_x), str(y), str(master_z)]) + '\n'

    # 3. DOF
    dof_string = ''
    for position, node_name in node_dict.items():
        y = int(position.split(',')[1])
        if y == 0:
            dof_string += 'DOF  ' + node_name + ' -1 -1 -1 -1 -1 -1' + '\n'
            Nodes[name].dof = 1
    
    # master node DOF
    for master_node in master_nodes.keys():
        dof_string += 'DOF  ' + master_node + ' 0 -1 0 -1 0 -1' + '\n'

    # 4. Nodal Mass, Translational mass (Ux, Uy, Uz, Rx, Ry, Rz)
    mass_string = ''
    for node in Nodes.values():
        name = node.name
        mass = node.translational_mass
        Rx, Ry, Rz = node.Rx, node.Ry, node.Rz
        mass_string += '#NodeMass  Mass  ' + name + ' ' + f"{mass:.7f}" + ' ' + f"{mass:.7f}" + ' ' + f"{mass:.7f}" + ' ' + str(int(Rx)) + ' ' + str(int(Ry)) + ' ' + str(int(Rz)) + '\n'
    
    # For master node's mass:
    for master_name in master_nodes.keys():
        mass, Ry = 0, 0
        for node in master_nodes[master_name]:
            mass += node.translational_mass
            Ry += node.Ry
        mass_string += 'Mass  ' + master_name + ' ' + f"{mass:.7f}" + ' ' + f"{0}" + ' ' + f"{mass:.7f}" + ' ' + str(0) + ' ' + str(int(Ry)) + ' ' + str(0) + '\n'
 
    # 5. Self-weight y load
    # self_weight_string = ''          
    load_string = ''
    for node in Nodes.values():
        name = node.name
        load_string += 'LoadPattern  NodalLoad  DL ' + name + ' ' + f"{0:.2f}" + ' ' + f"{node.load_y:.2f}" + ' ' + f"{0:.2f}" + ' 0 0 0' + '\n'
        load_string += 'GUI_LoadPattern  NodalLoad  DL ' + name + ' ' + f"{0:.2f}" + ' ' + f"{node.load_y:.2f}" + ' ' + f"{0:.2f}" + ' 0 0 0' + '\n'

    # 6. Constraint Diaphragm
    diaphragm_string = ''
    for diaphragm_index, master_name in enumerate(master_nodes.keys()):
        slaves_string = ''
        for node in master_nodes[master_name]:
            slaves_string += node.name + '  '
        diaphragm_string += "Constraint  Diaphragm  " + f"D{diaphragm_index+1}  " + f"{master_name}  " + slaves_string + "\n"

    # 7. BeamColumns
    # X-direction beam        
    beam_column_string = ''
    beam_column_count = 0
    # for beam_column in beam_column_list:
    for member_index in range(member_number):
        section_index = member_section_list[member_index]
        section_category = member_category_list[member_index]
        section_name = column_sections[section_index]['name'] if section_category == 'y' else beam_sections[section_index]['name']
        node1_index, node2_index = member_to_nodeIndex_dict[member_index][:2]
        end1_name, end2_name = 'N'+str(node1_index+1), 'N'+str(node2_index+1)
        beam_column_count += 1
        beam_column_name = 'E' + str(beam_column_count)
        beam_column_string += 'Element  BeamColumn   ' + beam_column_name + ' ' + end1_name + ' ' + end2_name + ' ' + section_name + '  0 1 1 0 0 0 0 0' + '\n'        
    
    # 8. Write beta (strong column - weak beam ratio) with comment
    beta_string = ''
    for node_index in range(node_number):
        node_name = 'N' + str(node_index + 1)
        beta_string += f'#StrongColumnWeakBeamRatio  {node_name}  {beta_x[node_index]:.4f}  {beta_z[node_index]:.4f} \n'


    # start write the file
    f = open(modal_file_path, 'w')

    f.write('PISA3D\n')
    f.write(f'{modal_file_path}\n')
    f.write('kN\n')
    f.write('mm\n')
    f.write('ControlData    GeometricNL  1\n')
    f.write('Analysis  ModeShape  3  1  2  0.02  0.02\n')

    f.write(f'# Analysis  Dynamic  Newmark  XGndMot  1  none  0  ZGndMot  1  0.005  {maximum_duration * 200}  alpha  beta  0\n')
    f.write(f'# LoadPattern  GroundAccel  XGndMot  {ground_motion_file_1}  1  1 \n')
    f.write(f'# LoadPattern  GroundAccel  ZGndMot  {ground_motion_file_2}  1  1 \n')

    f.write('GUI_GRID  XDIR' + x_grid_string + '\n')
    f.write('GUI_GRID  YDIR' + y_grid_string + '\n')
    f.write('GUI_GRID  ZDIR' + z_grid_string + '\n')
    f.write('\n'*2)

    f.write(node_string)
    f.write('\n'*2)

    f.write(dof_string)
    f.write('\n'*2)
    
    f.write(mass_string)
    f.write('\n'*2)

    f.write(load_string)
    f.write('\n'*2)

    f.write(diaphragm_string)
    f.write('\n'*2)

    f.write(beam_column_string)
    f.write('\n'*2)

    f.write(beta_string)
    f.write('\n'*2)

    f.write('% MATERIAL DATA %\n')
    f.write('Material  Bilinear steel 200 0.00 0.35 -0.35 0.3\n')
    f.write('\n'*2)

    f.write('% SECTION DATA %\n')

    for section in beam_sections:
        R, G, B = np.array(section['color'])/255
        f.write(f"GUI_Section I_SHAPE_SECTION {section['name']} steel steel steel steel steel steel steel steel steel 0 {section['H(mm)']} {section['B(mm)']} {section['t_f(mm)']} {section['t_w(mm)']} {section['B(mm)']} {section['t_f(mm)']} \n")
        f.write(f"GUI_SECTION_PROPERTY_FACTOR {section['name']} 1 1 1 1 1 1 1 1 \n")                                           # H                   B                 tf                   tw                   B                    tf
        f.write(f"GUI_SECTION_DISPLAY_COLOR {section['name']} {R}  {G}  {B}  \n")
        f.write(f"Section  BCSection03 {section['name']} steel steel steel steel steel steel steel steel steel 0 {section['A(cm2)']*100} {section['I_z(cm4)']*10000} {section['I_y(cm4)']*10000} {section['J(cm4)']*10000} {section['S_z(cm3)']*1000} {section['S_y(cm3)']*1000} {section['Av_y(cm2)']*100} {section['Av_z(cm2)']*100} \n")
        f.write("\n")                                                                                                  # A(mm2)                 Iz(mm4)                     Iy(mm4)                         J                       Sz                         Sy                        Avy                         Avz                                       
    
    for section in column_sections:
        R, G, B = np.array(section['color'])/255
        f.write(f"GUI_Section BOX_SECTION {section['name']} steel steel steel steel steel steel steel steel steel 0 {section['H(mm)']} {section['B(mm)']} {section['t_f(mm)']} {section['t_w(mm)']} \n")
        f.write(f"GUI_SECTION_PROPERTY_FACTOR {section['name']} 1 1 1 1 1 1 1 1 \n")                                        # H               B                 tf                      tw              
        f.write(f"GUI_SECTION_DISPLAY_COLOR {section['name']} {R}  {G}  {B}  \n")
        f.write(f"Section  BCSection03 {section['name']} steel steel steel steel steel steel steel steel steel 0 {section['A(cm2)']*100} {section['I_z(cm4)']*10000} {section['I_y(cm4)']*10000} {section['J(cm4)']*10000} {section['S_z(cm3)']*1000} {section['S_y(cm3)']*1000} {section['Av_y(cm2)']*100} {section['Av_z(cm2)']*100} \n")
        f.write('\n')                                                                                                    # A(mm2)                   Iz(mm4)                    Iy(mm4)                      J                       Sz                              Sy                   Avy                            Avz    

    f.write('\n'*2)

    f.write('GUI_LoadCase  GUI_AREA_LOAD_DL  DL\n')
    f.write('GUI_AREA_LOAD_ASSIGNED_TYPE  BY_BEAN_SPAN_LOAD\n')
    f.write('GUI_Output  OutFlag  10  10  0  2  2  10  10\n')
    f.write('Output  OutFlag  10  10  0  2  2  10  10\n')
    f.write('% RESPONSE HISTORY %\n')
    f.write('STOP\n')

    f.close() 









def generate_random_structure(target_dir, structure_num, start_index=1, ground_motion_type='World',
                              ground_motion_level='mixed', maximum_duration=100, section_country="USA", prioritized=None):
    print("Start generating structure......")
    
    if section_country == "USA":
        beam_sections = sections_usa.beam_sections
        column_sections = sections_usa.column_sections
    elif section_country == "Taiwan":
        beam_sections = sections_tw.beam_sections
        column_sections = sections_tw.column_sections
    else:
        raise ValueError("wrong sections country!")
    

    for index in range(start_index, start_index+structure_num):
        print(f"Generating {index:04d}/{structure_num:04d} strucutre......")
        folder_name = os.path.join(target_dir, f'structure_{index}_{ground_motion_type}')
        if os.path.exists(folder_name) == False:
            os.mkdir(folder_name)
        
        modal_file_path = os.path.join(folder_name, 'modal.ipt')
        structure_file_path = os.path.join(folder_name, 'structure.ipt')
        
        if ground_motion_level == 'BSE-1':
            ground_motion_root = f"E:/TimeHistoryAnalysis/Data/GroundMotions_{ground_motion_type}_BSE-1"
        elif ground_motion_level == 'BSE-2':
            ground_motion_root = f"E:/TimeHistoryAnalysis/Data/GroundMotions_{ground_motion_type}_BSE-2"
        elif ground_motion_level == 'mixed':
            # Determine the random earthquake
            if random.random() < 0.5:
                ground_motion_root = f"E:/TimeHistoryAnalysis/Data/GroundMotions_{ground_motion_type}_BSE-1"
            else:
                ground_motion_root = f"E:/TimeHistoryAnalysis/Data/GroundMotions_{ground_motion_type}_BSE-2"

        ground_motion_folder = random.choice(os.listdir(ground_motion_root))
        ground_motion_name = ground_motion_folder
        ground_motion_file_1 = os.path.join(ground_motion_root, ground_motion_folder, ground_motion_name + "_FN.txt")
        ground_motion_file_2 = os.path.join(ground_motion_root, ground_motion_folder, ground_motion_name + "_FP.txt")

        shutil.copyfile(ground_motion_file_1, os.path.join(folder_name, "ground_motion_1.txt"))
        shutil.copyfile(ground_motion_file_2, os.path.join(folder_name, "ground_motion_2.txt"))
        print("      ", ground_motion_file_1)
        print("      ", ground_motion_file_2)


        # Grids
        # Floor height = 4~7F
        # Spans = 2~6
        # x, z grid span = 6~8m
        y_grid_num = np.random.randint(4, 8)
        x_grid_num, z_grid_num = np.random.randint(2, 7, size=(2))
        x_grid_space, z_grid_space = np.random.randint(6, 9, size=(2)) * 1000
        # x_grid_num, y_grid_num, z_grid_num = 3, 6, 3
        # x_grid_space, z_grid_space = 7000, 7000
        y_grid_space = 3200        
        
        x_grid = [0 + num * x_grid_space for num in range(x_grid_num+1)]
        y_grid = [0, 4200]
        y_grid += [4200 + num * y_grid_space for num in range(1, y_grid_num)]
        z_grid = [0 + num * z_grid_space for num in range(z_grid_num+1)]
        
        environment_parameters = [x_grid, y_grid, z_grid, x_grid_space, y_grid_space, z_grid_space]
        

        # generate grid coordinate for node and set DOF
        node_number = len(x_grid) * len(y_grid) * len(z_grid)
        node_index = 0
        coord_to_nodeIndex_dict = {}    # key: coord_str(ex: 6000_3200_6000), value: node_index
        node_need_beta = torch.ones(node_number)   # record whether a node need to calculate if beta pass. Upper ends of the top story column and bottem end for first floor column don't need.
        
        for i, y in enumerate(y_grid):
            for j, x in enumerate(x_grid):
                for k, z in enumerate(z_grid):
                    if y == 0:  # if fixed
                        node_need_beta[node_index] = 0
                    if y == y_grid[-1]: # if at top
                        node_need_beta[node_index] = 0
                        
                    coord_to_nodeIndex_dict['_'.join([str(x), str(y), str(z)])] = node_index
                    node_index += 1

                   
                    
        # generate member_feature
        member_number = y_grid_num * (3 * x_grid_num * z_grid_num + 2 * x_grid_num + 2 * z_grid_num + 1)
        member_index = 0
        member_to_nodeIndex_dict = {}   # key: member_index, value: [node1_index, node2_index, face1_number, face2_number, My_face1_index, My_face2_index], whrere face_index is the index in the node feature
        member_section_list = []        # initial: [8, 8, 8, 4, 4, 4, ....], where 8 is the thickest among beam sections and also 4 amoung column sections.
        member_category_list = []       # record whether the member is x_beam, z_beam or y_column
        member_XZ_dict = {}                     # key: member_index, value: xz
        member_same_location_dict = {}     # key: x_z, value: [member_index...]
        node_neighbor_Mp_matrix = torch.zeros(node_number, 6)   # 6 is for xn(0), xp(1), yn(2), yp(3), zn(4), zp(5)
        member_group_category = []      # [1F_outer_column, 1F_inner_column, ...., 5F_inner_beam, 5F_outer_beam...]   
        member_group_dict = {}          # key: member_index, value: [same_group_member_index_1, same_group_member_index_2, ...]   
        
        node_neighbor_member_dict = {}  # key: node_index, value: [member_index1, member_index2, ....]
        for i in range(node_number):
            node_neighbor_member_dict[i] = []
        
        for i, y in enumerate(y_grid):
            # for columns:
            if y != y_grid[-1]:
                y_upper = y_grid[i+1]
                for x in x_grid:
                    for z in z_grid:
                        coord1 = "_".join([str(x), str(y), str(z)])
                        coord2 = "_".join([str(x), str(y_upper), str(z)])
                        node1_index = coord_to_nodeIndex_dict[coord1]
                        node2_index = coord_to_nodeIndex_dict[coord2]
                        member_to_nodeIndex_dict[member_index] = [node1_index, node2_index, 3, 2, FACE_HASH_TABLE['y_p'], FACE_HASH_TABLE['y_n']]
                        
                        # assign member with same location (vertically)
                        column_XZ = "_".join([str(x), str(z)])
                        member_XZ_dict[member_index] = column_XZ
                        if column_XZ not in member_same_location_dict.keys():
                            member_same_location_dict[column_XZ] = []
                        member_same_location_dict[column_XZ].append(member_index)

                        # assign_group_category
                        if x == x_grid[0] or x == x_grid[-1] or z == z_grid[0] or z == z_grid[-1]:
                            member_group_category.append(f"{y+1}F_outer_column")
                        else:
                            member_group_category.append(f"{y+1}F_inner_column")
            
                        init_section = len(column_sections) - 1
                        member_section_list.append(init_section)
                        member_category_list.append('y')
                        member_index += 1
            
            # for x beams and z beams:
            if y != 0:
                for z in z_grid:
                    for x in x_grid[:-1]:
                        x_next = x + x_grid_space
                        coord1 = "_".join([str(x), str(y), str(z)])
                        coord2 = "_".join([str(x_next), str(y), str(z)])
                        node1_index = coord_to_nodeIndex_dict[coord1]
                        node2_index = coord_to_nodeIndex_dict[coord2]
                        member_to_nodeIndex_dict[member_index] = [node1_index, node2_index, 1, 0, FACE_HASH_TABLE['x_p'], FACE_HASH_TABLE['x_n']]
                        
                        # assign member with same location (vertically)
                        beam_XZ = "_".join([str((x + x_next) / 2), str(z)])
                        member_XZ_dict[member_index] = beam_XZ
                        if beam_XZ not in member_same_location_dict.keys():
                            member_same_location_dict[beam_XZ] = []
                        member_same_location_dict[beam_XZ].append(member_index)

                        # assign_group_category
                        if z == z_grid[0] or z == z_grid[-1]:
                            member_group_category.append(f"{y}F_outer_beam")
                        else:
                            member_group_category.append(f"{y}F_inner_beam")
                        
                        init_section = len(beam_sections) - 1
                        member_section_list.append(init_section)
                        member_category_list.append('x')
                        member_index += 1
                
                for x in x_grid:
                    for z in z_grid[:-1]:
                        z_next = z + z_grid_space
                        coord1 = "_".join([str(x), str(y), str(z)])
                        coord2 = "_".join([str(x), str(y), str(z_next)])
                        node1_index = coord_to_nodeIndex_dict[coord1]
                        node2_index = coord_to_nodeIndex_dict[coord2]
                        member_to_nodeIndex_dict[member_index] = [node1_index, node2_index, 5, 4, FACE_HASH_TABLE['z_p'], FACE_HASH_TABLE['z_n']]
                        
                        # assign member with same location (vertically)
                        beam_XZ = "_".join([str(x), str((z + z_next) / 2)])
                        member_XZ_dict[member_index] = beam_XZ
                        if beam_XZ not in member_same_location_dict.keys():
                            member_same_location_dict[beam_XZ] = []
                        member_same_location_dict[beam_XZ].append(member_index)

                        # assign_group_category
                        if x == x_grid[0] or x == x_grid[-1]:
                            member_group_category.append(f"{y}F_outer_beam")
                        else:
                            member_group_category.append(f"{y}F_inner_beam")
                        
                        init_section = len(beam_sections) - 1
                        member_section_list.append(init_section)
                        member_category_list.append('z')
                        member_index += 1

        
        # assign beam and column index
        column_index_list = [index for index in range(member_number) if member_category_list[index] == 'y']
        beam_index_list = [index for index in range(member_number) if member_category_list[index] != 'y']
                        
                        
        # assign same group members
        for member_index in range(member_number):
            member_group_dict[member_index] = []
            group = member_group_category[member_index]
            for another_member_index in range(member_number):
                if member_index != another_member_index and group == member_group_category[another_member_index]:
                    member_group_dict[member_index].append(another_member_index)


        # update member feature into node feature and the node neighbor Mp list, and embedding node
        for member_index in range(member_number):
            section_index = member_section_list[member_index]
            category = member_category_list[member_index]
            if category == 'y':
                member_Mp = column_sections[section_index]['Mp_z(kN-mm)']
            else:
                member_Mp = beam_sections[section_index]['Mp_z(kN-mm)']
            
            node1_index, node2_index, face_number1, face_number2, My_face1_index, My_face2_index = member_to_nodeIndex_dict[member_index]
            node_neighbor_Mp_matrix[node1_index, face_number1] = member_Mp      
            node_neighbor_Mp_matrix[node2_index, face_number2] = member_Mp 
            node_neighbor_member_dict[node1_index].append(member_index)   
            node_neighbor_member_dict[node2_index].append(member_index)  


        # Currently the beam and column sections are initiaized with the thickest sections.
        # Now try to reduce the section size and recrod all the step until the final state that beta < 1.
        # Then randomly select a section state to represent this random structure.
        member_section_list = _assign_member_sections(member_section_list,
                                                      member_category_list,
                                                      column_index_list,
                                                      beam_index_list,
                                                      member_XZ_dict,
                                                      member_same_location_dict,
                                                      member_to_nodeIndex_dict,
                                                      node_neighbor_Mp_matrix,
                                                      node_need_beta,
                                                      member_group_dict,
                                                      section_country=section_country,
                                                      prioritized=prioritized)

        # Now we have the designed member sections.
        # Strat generate the modal.ipt file
        beta_x, beta_z, _ = _strongColumn_weakBeam_criterion(node_need_beta, node_neighbor_Mp_matrix)
        _generate_ipt(modal_file_path,
                      ground_motion_file_1,
                      ground_motion_file_2,
                      environment_parameters,
                      node_neighbor_member_dict,
                      member_section_list,
                      member_category_list,
                      member_to_nodeIndex_dict,
                      beta_x, beta_z, maximum_duration,
                      section_country)

        # generate a copy of modal.ipt to structure.ipt
        shutil.copyfile(modal_file_path, structure_file_path)
        

            
    
    