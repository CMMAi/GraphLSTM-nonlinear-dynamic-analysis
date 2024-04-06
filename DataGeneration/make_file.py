import os
from os.path import join


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False



def update_plastic_hinge(element_file_path):
    element_file = open(element_file_path, 'r').readlines()
    update_ps_content = []
    currentElem = ""
    currentElem_iEnd_isPS = False
    currentElem_jEnd_isPS = False
    for line in element_file:
        contents = line.split(',')
        if len(contents) <= 2: continue
        if(contents[0] != currentElem): # Change to next element
            currentElem = contents[0]
            currentElem_iEnd_isPS = False
            currentElem_jEnd_isPS = False
            update_ps_content.append('\n'*2)
            update_ps_content.append(line)
        else:   # Still in the same element, but next timestep.
            if(currentElem_iEnd_isPS):  contents[2] = "1"
            if(currentElem_jEnd_isPS):  contents[3] = "1"
            if(contents[2] == "1"): currentElem_iEnd_isPS = True
            if(contents[3] == "1"): currentElem_jEnd_isPS = True
            update_ps_content.append(','.join(contents))

    with open(element_file_path, 'w') as f:
        for line in update_ps_content:
            f.write(line)
    del update_ps_content



def clean_ElemRecord(folder_path):
    element_file_path = join(folder_path, 'STRUCTURE.ElemRecord')
    element_file = open(element_file_path, 'r').readlines()

    keeped_elemRecord = []
    current_elem = None
    for line in element_file:
        contents = line.strip().split()
        if len(contents) == 0: continue
        
        if contents[0][0] == 'E':
            current_elem = contents[0]
            keeped_elemRecord.append('\n'*2)
        
        elif is_number(contents[0]):
            keeped_elemRecord.append(f"{current_elem},{contents[0]},{contents[1]},{contents[2]},{','.join(contents[9:17])}\n") 
            
            
    # Make a new .ElemRecord file to replace the old one.
    with open(element_file_path, 'w') as f:
        for line in keeped_elemRecord:
            f.write(line)

    update_plastic_hinge(element_file_path)
    del keeped_elemRecord



def clean_NodeDisRecord(folder_path):
    displacement_file_path = join(folder_path, 'STRUCTURE.NodeDisRecord')
    displacement_file = open(displacement_file_path, 'r').readlines()

    keeped_dispRecord = []
    for line in displacement_file:
        contents = line.strip().split()
        if len(contents) == 0: continue
        if contents[0][0] != "N": continue
        keeped_dispRecord.append(f"{contents[0]},{contents[1]},{contents[2]},{contents[4]}\n")
            
    # Make a new .NodeDisRecord file to replace the old one.
    with open(join(folder_path, 'STRUCTURE.NodeDisRecord'), 'w') as f:
        for line in keeped_dispRecord:
            f.write(line)
    del keeped_dispRecord
    
    

def clean_NodeAccRecord(folder_path):
    acc_file_path = join(folder_path, 'STRUCTURE.NodeAccRecord')
    acc_file = open(acc_file_path, 'r').readlines()

    keeped_accRecord = []
    for line in acc_file:
        contents = line.strip().split()
        if len(contents) == 0: continue
        if contents[0][0] != "N": continue
        keeped_accRecord.append(f"{contents[0]},{contents[1]},{contents[2]},{contents[4]}\n")
            
    # Make a new .NodeAccRecord file to replace the old one.
    with open(join(folder_path, 'STRUCTURE.NodeAccRecord'), 'w') as f:
        for line in keeped_accRecord:
            f.write(line)
    del keeped_accRecord


def clean_NodeVelRecord(folder_path):
    vel_file_path = join(folder_path, 'STRUCTURE.NodeVelRecord')
    vel_file = open(vel_file_path, 'r').readlines()

    keeped_velRecord = []
    for line in vel_file:
        contents = line.strip().split()
        if len(contents) == 0: continue
        if contents[0][0] != "N": continue
        keeped_velRecord.append(f"{contents[0]},{contents[1]},{contents[2]},{contents[4]}\n")
            
    # Make a new .NodeVelRecord file to replace the old one.
    with open(join(folder_path, 'STRUCTURE.NodeVelRecord'), 'w') as f:
        for line in keeped_velRecord:
            f.write(line)
    del keeped_velRecord


def clean_Eigen(folder_path):
    eigen_file_path = join(folder_path, 'MODAL.Eigen')
    modal_file_path = join(folder_path, 'MODAL.Modal')
    eigen_file = open(eigen_file_path, 'r').readlines()

    first_mode_period = None
    second_mode_period = None
    third_mode_period = None
    is_alpha_beta = False
    alpha, beta = None, None
    is_mode_1, is_mode_2, is_mode_3 = False, False, False
    with open(modal_file_path, 'w') as modal:
        for line in eigen_file:

            if "Period of Mode 1" in line:
                contents = line.strip().split()
                first_mode_period = float(contents[5])
            elif "Period of Mode 2" in line:
                contents = line.strip().split()
                second_mode_period = float(contents[5])
            elif "Period of Mode 3" in line:
                contents = line.strip().split()
                third_mode_period = float(contents[5])

            elif "Alpha" in line and "Beta" in line:
                is_alpha_beta = True
            elif is_alpha_beta == True:
                contents = line.strip().split()
                alpha = float(contents[0])
                beta = float(contents[1])
                is_alpha_beta = False

            elif "Mode 1, Period =" in line:
                is_mode_1 = True
            elif "-----------" in line and is_mode_1:
                is_mode_1 = False
            elif is_mode_1 == True:
                if "Node" in line or "N" not in line: continue
                contents = line.strip().split()
                modal.write(f"Mode1,{contents[0]},{contents[1]},{contents[3]},{contents[5]}\n")
            
            elif "Mode 2, Period =" in line:
                is_mode_2 = True
            elif "-----------" in line and is_mode_2:
                is_mode_2 = False
            elif is_mode_2 == True:
                if "Node" in line or "N" not in line: continue
                contents = line.strip().split()
                modal.write(f"Mode2,{contents[0]},{contents[1]},{contents[3]},{contents[5]}\n")
            
            elif "Mode 3, Period =" in line:
                is_mode_3 = True
            elif "-----------" in line and is_mode_3:
                is_mode_3 = False
            elif is_mode_3 == True:
                if "Node" in line or "N" not in line: continue
                contents = line.strip().split()
                modal.write(f"Mode3,{contents[0]},{contents[1]},{contents[3]},{contents[5]}\n")
                
            
    # Make a new .Eigen file to replace the old one.
    with open(join(folder_path, 'MODAL.Eigen'), 'w') as f:
        f.write(f"FirstModePeriod,{first_mode_period} \n")
        f.write(f"SecondModePeriod,{second_mode_period} \n")
        f.write(f"ThirdModePeriod,{third_mode_period} \n")
        f.write(f"Alpha,{alpha} \n")
        f.write(f"Beta,{beta} \n")
        


def set_Rayleigh_coeff(target_dir, structure_num, start_index, ground_motion_type):
    for index in range(start_index, start_index+structure_num):
        print(f"Setting {index:04d}/{structure_num:04d} Reyleigh coefficients......")
        folder_name = os.path.join(target_dir, f'structure_{index}_{ground_motion_type}')
        
        eigen_file_name = os.path.join(folder_name, 'MODAL.Eigen')
        structure_file_name = os.path.join(folder_name, 'structure.ipt')
        alpha, beta = None, None

        # get alpha, beta from modal analysis' result
        with open(eigen_file_name, 'r') as eigen:
            for line in eigen.readlines():
                contents = line.strip().split(",")
                if contents[0] == "Alpha":
                    alpha = float(contents[1])
                elif contents[0] == "Beta":
                    beta = float(contents[1])

        # set alpha, beta back into the structure.ipt
        structure_ipt_string = ""
        with open(structure_file_name, 'r') as f:
            structure_ipt_string = f.read()

        structure_ipt_string = structure_ipt_string.replace("alpha", str(alpha))
        structure_ipt_string = structure_ipt_string.replace("beta", str(beta))
        structure_ipt_string = structure_ipt_string.replace("# ", "")
        structure_ipt_string = structure_ipt_string.replace("Analysis  ModeShape", "# Analysis  ModeShape")

        with open(structure_file_name, 'w') as f:
            f.write(structure_ipt_string)

