import torch
from torch_geometric.data import Data
# from torch.utils.tensorboard import SummaryWriter
from .normalization import *
import numpy as np
import sys
sys.path.append("../")
from Models.losses import *


def get_target_index(target):
    target_dict = {}
    y_start, y_finish = -1, -1
    if('acc' in target):
        y_start = 0 
        y_finish = 2
        target_dict['acc'] = [0, 2]
    if('vel' in target):
        y_finish = 4
        target_dict['vel'] = [2, 4]
    if('disp' in target):
        y_finish = 6
        target_dict['disp'] = [4, 6]
    if('Mz' in target):
        y_finish = 12
        target_dict['Mz'] = [6, 12]
    if('Sy' in target):
        y_finish = 18
        target_dict['Sy'] = [12, 18]
    
    return y_start, y_finish, target_dict     


# prepare a dictionary to record target accuracy
def get_target_accuracy(args, target_dict):
    target_accuracy_record = dict()
    for target in target_dict.keys():
        target_accuracy_record[target] = np.zeros((3, args.epoch_num))
    return target_accuracy_record



def accumulate_target_accuracy(y_start, target_accuracy_record, target_dict, epoch, accuracy, pred, y, t_v=0):
    for target in target_dict.keys():
        i, j = target_dict[target][0] - y_start, target_dict[target][1] - y_start
        acc = accuracy(pred[:, :, i:j], y[:, :, i:j])
        target_accuracy_record[target][t_v][epoch] += acc
    return target_accuracy_record


def average_target_accuracy(target_accuracy_record, epoch, elem_num, t_v=0):
    for target in target_accuracy_record.keys():
        target_accuracy_record[target][t_v][epoch] /= elem_num
    return target_accuracy_record



# return loss function object list and a empty array to record those loss
def get_metrics(args):
    metrics = []
    metrics_record = np.zeros((3, 3, args.epoch_num))
    for metric in ["MAE", "MSE", "RMSE", "MAPE"]:
        if metric == args.loss_function:
            continue
        metrics.append(globals()[metric](**{'accuracy_threshold': args.accuracy_threshold}))
    return metrics, metrics_record


def write_tensorboard(writer, args, accuracy_record, loss_record, target_accuracy_record, metrics, metrics_record):
    # accuracy curve
    for i in range(accuracy_record.shape[1]):
        writer.add_scalars("Accuracy/Learning Curve", {'train':accuracy_record[0][i], 'valid':accuracy_record[1][i]}, i)

    # loss curve
    for i in range(loss_record.shape[1]):
        writer.add_scalars(f"Accuracy/Loss Curve ({args['loss_function']})", {'train':loss_record[0][i], 'valid':loss_record[1][i]}, i)

    # target accuracy record
    for target in target_accuracy_record.keys():
        for i in range(args["epoch_num"]):
            writer.add_scalars(f"Target_Accuracy/{target}", {'train':target_accuracy_record[target][0][i], 'valid':target_accuracy_record[target][1][i]}, i)

    # metrics
    for m, metric in enumerate(metrics):
        for i in range(metrics_record.shape[2]):
            writer.add_scalars(f"Metric/{metric.name}", {'train':metrics_record[m][0][i], 'valid':metrics_record[m][1][i]}, i)

    return writer




