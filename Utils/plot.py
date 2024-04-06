import enum
import matplotlib.pyplot as plt
# import seaborn as sns
import numpy as np
import torch
from torch_geometric.loader import DataLoader
import os
from .normalization import *
from .accuracy import *


def print_space():
    return "\n"*3 + "="*100 + "\n"*3
    


def plot_learningCurve(accuracy_record, ckpt_dir, title=None):
    train_acc, valid_acc, test_acc = accuracy_record    
    epochs = list(range(1, len(train_acc)+1))
    plt.figure(figsize=(8, 6))
    plt.rcParams['font.size'] = '14'
    plt.plot(epochs, train_acc, label=f'train: {np.max(train_acc):.4f}')
    plt.plot(epochs, valid_acc, label=f'valid: {np.max(valid_acc):.4f}')
    plt.plot(epochs, test_acc, label=f'test: {np.max(test_acc):.4f}')
    plt.legend()
    plt.grid(alpha=.7)
    plt.xlabel("Epochs")
    plt.ylabel("R2 Score")
    plt.ylim([-0.1, 1.05])
    plt.title(title)
    plt.savefig(ckpt_dir / "learningCurve.png")
    # plt.show()
    plt.close()



def plot_lossCurve(loss_record, ckpt_dir, title=None):
    train_loss, valid_loss, test_loss = loss_record    
    epochs = list(range(1, len(train_loss)+1))
    plt.figure(figsize=(8, 6))
    plt.rcParams['font.size'] = '14'
    plt.plot(epochs, train_loss, label=f'train: {np.min(train_loss):.4f}')
    plt.plot(epochs, valid_loss, label=f'valid: {np.min(valid_loss):.4f}')
    plt.plot(epochs, test_loss, label=f'test: {np.min(test_loss):.4f}')
    plt.legend()
    plt.grid()
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    # plt.ylim([-0.01, 0.1])
    plt.title(title)
    plt.savefig(ckpt_dir / "lossCurve.png")
    # plt.show()
    plt.close()



    

def plot_target_accuracy(target_accuracy_record, epoch_num, ckpt_dir, evaluation):
    epochs = list(range(1, epoch_num+1))

    for i, name in enumerate(['Training', 'Validation', 'Testing']):
        plt.figure(figsize=(8, 6))
        plt.rcParams['font.size'] = '14'
        for target in target_accuracy_record.keys():
            acc = target_accuracy_record[target][i]
            plt.plot(epochs, acc, label=f"{target}: {np.max(acc):.4f}")
        plt.legend()
        plt.grid()
        plt.xlabel("Epochs")
        plt.ylabel(evaluation)
        plt.title(f"{name} {evaluation}")
        plt.savefig(ckpt_dir / f"{name}_Target_{evaluation}.png")
        plt.close()


            

def plot_plastic_hinge_accuracy(record, ckpt_dir, specific_location=False):
    epochs = np.arange(1, record.shape[1]+1)

    for i, t_v in enumerate(['Train', 'Valid', 'Test']):
        node_level_precision = record[i, :, 0] / (record[i, :, 0] + record[i, :, 1] + 1)
        node_level_recall = record[i, :, 0] / (record[i, :, 0] + record[i, :, 2] + 1)  # +1 in case division problem

        plt.rcParams['font.size'] = '14'
        fig, axs = plt.subplots(2, 1, figsize=[16, 12])
        if specific_location:
            suptitle = f"{t_v}_Mz_1F_column:  Precision and Recall Evaluation"
        else:
            suptitle = f"{t_v}_Mz:  Precision and Recall Evaluation"
        fig.suptitle(suptitle, fontsize=19, fontweight='bold')

        axs[0].plot(epochs, node_level_precision)
        axs[0].set_title(f'Section Precision, best acc: {np.max(node_level_precision):.4f}')
        axs[0].grid()

        axs[1].plot(epochs, node_level_recall)
        axs[1].set_title(f'Section Recall, best acc: {np.max(node_level_recall):.4f}')
        axs[1].grid()

        fig.add_subplot(1, 1, 1, frame_on=False)
        # Hiding the axis ticks and tick labels of the bigger plot
        plt.tick_params(labelcolor="none", bottom=False, left=False)

        plt.xlabel("Epochs", fontsize=15, fontweight='bold')
        plt.ylabel("Evaluation", fontsize=15, fontweight='bold')
        if specific_location:
            save_path = ckpt_dir / f"Mz_plastic_hinge_{t_v}_1F_column.png"
        else:
            save_path = ckpt_dir / f"Mz_plastic_hinge_{t_v}.png"
        plt.savefig(save_path)
        plt.close()


@torch.no_grad()
def plot_test_accuracy_distribution(test_dataset, model, ckpt_dir):
    R2_per_structure = []
    device = "cuda"
    model.eval()
    for i in range(len(test_dataset)):
        graph = test_dataset[i].clone().to(device)
        graph.ptr = torch.tensor([0, graph.x.shape[0]]).to(device)
        graph.sampled_index = [graph.sampled_index]
        graph.batch = torch.zeros(graph.x.shape[0]).to(device).to(torch.int64) 

        output, keeped_indexes = model(graph.x, graph.edge_index, graph.edge_attr, graph.batch, graph.ptr, graph.sampled_index, graph.ground_motions, sample_node=False)
        x, y = graph.x[keeped_indexes], graph.y[keeped_indexes]
        R2_acc = R2_score(output, y).cpu().numpy()
        R2_per_structure.append(R2_acc)

    # find the highest and lowest R2 case
    R2_per_structure = np.array(R2_per_structure)
    worst_case_index = np.argmin(R2_per_structure)
    best_case_index = np.argmax(R2_per_structure)

    # plot
    plt.rcParams['font.size'] = '14'
    fig, ax = plt.subplots()
    ax.hist(R2_per_structure, edgecolor="black", facecolor="orange")
    ax.invert_xaxis()
    plt.xlabel("R2 Score")
    plt.ylabel("Structure Number")
    plt.title(f"Max R2: {max(R2_per_structure):.4f}, Min R2: {min(R2_per_structure):.4f}")
    plt.savefig(ckpt_dir / "test_acc_distribution.png")

    return worst_case_index, best_case_index
    



