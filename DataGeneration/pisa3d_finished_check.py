import os


def check_ipt(case_dir):
    file_list = os.listdir(case_dir)
    for f in file_list:
        if (f.lower()[-4:] == ".ipt"):
            return True
    return False

def check_eigen(case_dir):
    file_list = os.listdir(case_dir)
    for f in file_list:
        if (f.lower()[-6:] == ".eigen"):
            return True
    return False


def check_ElemRecord(case_dir):
    file_list = os.listdir(case_dir)
    for f in file_list:
        if (f.lower()[-11:] == ".elemrecord"):
            return True
    return False


def check_NodeDisRecord(case_dir):
    file_list = os.listdir(case_dir)
    for f in file_list:
        if (f.lower()[-14:] == ".nodedisrecord"):
            return True
    return False



def check_finish(case_dir):
    if (check_ipt(case_dir) and check_ElemRecord(case_dir) and check_NodeDisRecord(case_dir)):
        return "finished"
    else:
        return "failed"
    

def check_finish_eigen(case_dir):
    if (check_ipt(case_dir) and check_eigen(case_dir)):
        return "finished"
    else:
        return "failed"
