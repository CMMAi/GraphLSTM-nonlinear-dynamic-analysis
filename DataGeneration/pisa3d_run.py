import os
import shutil
import subprocess
import sys
import threading
import time

import pisa3d_finished_check
import generate_random_structure
import generate_structural_graph
import make_file


thread_quota    = 7
working_dir     = "D:\\Nonlinear_Dynamic_Analysis_WorldGM_USASection_BSE-1\\"
pisa            = "E:\\TimeHistoryAnalysis\\Data\\PISA3D_Batch_500nodes.exe"
structure_num   = 1000
start_index     = 1


# ground_motion_type: {ChiChi, World}
ground_motion_type = 'World_processed'

# ground_motion_level: {BSE-1, BSE-2, mixed}
ground_motion_level = 'BSE-1'

# section_country: {USA, Taiwan}
section_country = 'USA'

# maximum_duration: {70sec, 100sec}
maximum_duration = 70

# prioritized: {None, thick, thin}
prioritized = None



def check_path(path):
    print("Start checking path......")
    if os.path.exists(path):
        print('This dir is already exist.')
    else:
        os.mkdir(path)
        
 
def run_single_analysis(semaphore, case_dir, ipt):
    semaphore.acquire()
    os.system("@ECHO OFF")
    os.system(pisa + " " + ipt)

    delete_useless_files_in_dir(case_dir)

    try:    # In case it occur errors
        if("modal" in ipt):
            make_file.clean_Eigen(case_dir)
        elif("structure" in ipt):
            make_file.clean_ElemRecord(case_dir)
            make_file.clean_NodeAccRecord(case_dir)
            make_file.clean_NodeVelRecord(case_dir)
            make_file.clean_NodeDisRecord(case_dir)
    except:
        print("There are no such response files yet!!!")

    semaphore.release()


def make_sure_clean_again(case_dir):
    print(f"Checking again case {case_dir}......")
    if "STRUCTURE.VISA3D" in os.listdir(case_dir):
        print(f"Fuond uncleaned folder, now clean again folder {case_dir}......")
        delete_useless_files_in_dir(case_dir)
        make_file.clean_ElemRecord(case_dir)
        make_file.clean_NodeAccRecord(case_dir)
        make_file.clean_NodeVelRecord(case_dir)
        make_file.clean_NodeDisRecord(case_dir)




def run_pisa_all(analysis="structure"):
    print("Start running pisa analysis......")
    len_argv = len(sys.argv)
    semaphore = threading.Semaphore(thread_quota)
    case_counter_unfinished = 1
    
    while (case_counter_unfinished != 0):
        print('\n'*2)
        case_counter_unfinished = 0
        case_list = os.listdir(working_dir)
        case_list.sort()
        target_case_list = []
        t_pool           = []
        for case in case_list:
            case_dir = working_dir + case + "\\"
            if analysis == "modal":
                state = pisa3d_finished_check.check_finish_eigen(case_dir)
            elif analysis == "structure":
                state = pisa3d_finished_check.check_finish(case_dir)
            else:
                raise Exception("Please either use modal analysis or dynamic analysis!")
            
            if state != "finished":
                case_counter_unfinished = case_counter_unfinished + 1
                target_case_list.append(case)
        if (case_counter_unfinished != 0):
            for case in target_case_list:
                case_dir = working_dir + case + "\\"
                ipt      = case_dir + analysis
                t_pool.append(threading.Thread(target=run_single_analysis, args=(semaphore, case_dir, ipt, )))
            for t in t_pool:
                t.start()
            for t in t_pool:
                t.join()

    for case in os.listdir(working_dir):
        case_dir = working_dir + case + "\\"
        make_sure_clean_again(case_dir)





keeped_extensions = ['ipt', 'Eigen', 'Modal', 'ElemRecord', 'NodeDisRecord', 'NodeAccRecord', 'NodeVelRecord', 'pt', 'txt']
def delete_useless_files_in_dir(case_dir):
    print("Start deleting useless files......")
    for analysis_file in os.listdir(case_dir):
        file_name = os.path.join(case_dir, analysis_file)
        extension = analysis_file.split('.')[1]
        if extension not in keeped_extensions:
            os.remove(file_name)




if __name__ == '__main__':

    # 1. Check if the path exists, if not, create folder
    check_path(working_dir)

    # 2-1. Generate modal analysis and structure input file
    # 2-2. Run modal analysis
    # 2-3. Set alpha, beta to structure.ipt
    # generate_random_structure.generate_random_structure(target_dir=working_dir, structure_num=structure_num, start_index=start_index,
    #                                                     ground_motion_type=ground_motion_type, ground_motion_level=ground_motion_level, 
    #                                                     maximum_duration=maximum_duration, section_country=section_country,
    #                                                     prioritized=prioritized)
    # run_pisa_all(analysis="modal")
    # make_file.set_Rayleigh_coeff(target_dir=working_dir, structure_num=structure_num, start_index=start_index,
    #                              ground_motion_type=ground_motion_type)


    # 3. After setting rayleigh, run dynamic analysis
    # run_pisa_all(analysis="structure")

    # 4. Generate graph
    generate_structural_graph.generate_graph_NodeAsNode(working_dir, start_index=start_index, section_country=section_country)
    
    

    
    