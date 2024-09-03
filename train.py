import torch
from torch.utils.data import random_split
from torch_geometric.loader import DataLoader
import torch.optim as optim
import numpy as np
import time
import random
from datetime import datetime
import os
import gc
import json
import logging
from tqdm import tqdm
from argparse import ArgumentParser, Namespace
from pathlib import Path
from copy import deepcopy
from typing import List
import sys
sys.path.append("../")


from Models.LSTM import *
from Models.losses import *
from Utils import plot
from Utils import visualize
from Utils import accuracy
from Utils import dataset
from Utils import normalization
from Utils import utils




def parse_args() -> Namespace:
    parser = ArgumentParser()

    # comment
    parser.add_argument("--comment", type=str, default='AbsAcc, MoreYFeatures(My, Sz), with neglect_beam_My_Sz')

    # checkpoint
    parser.add_argument("--ckpt_dir", type=Path, default="../Results/")

    # dataset
    parser.add_argument("--dataset_name", type=str, default='Nonlinear_Dynamic_Analysis_World_Full_BSE-2')
    parser.add_argument("--other_datasets", type=list, default=[])
    parser.add_argument("--whatAsNode", type=str, default='NodeAsNode')
    parser.add_argument("--data_num", type=int, default=2000)
    parser.add_argument("--random_sample", type=bool, default=True)
    parser.add_argument("--timesteps", type=int, default=1400)
    parser.add_argument("--train_split_ratio", type=list, default=[0.7, 0.2, 0.1])

    # model
    parser.add_argument("--pretrain_path", type=Path, default=None)
    parser.add_argument("--model", type=str, default='GraphLSTM')
    parser.add_argument("--gnn_num_layers", type=int, default=1)
    parser.add_argument("--head_num", type=int, default=4)
    parser.add_argument("--gnn_hidden_dim", type=int, default=64)
    parser.add_argument("--latent_dim", type=int, default=128)
    parser.add_argument("--graph_lstm_hidden_dim", type=int, default=128)
    parser.add_argument("--graph_lstm_num_layers", type=int, default=1)
    parser.add_argument("--node_lstm_hidden_dim", type=int, default=256)
    parser.add_argument("--node_lstm_num_layers", type=int, default=2)

    # training
    parser.add_argument("--loss_function", type=str, default='MSE')
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--sch_factor", type=float, default=0.5)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--target", type=str, default='acc_vel_disp_My_Mz_Sy_Sz')
    parser.add_argument("--epoch_num", type=int, default=300)
    parser.add_argument("--batch_size", type=int, default=12)
    parser.add_argument("--random_seed", type=int, default=731, help="fixed random seed")
    parser.add_argument("--neglect_beam_My_Sz", action="store_true", default=True, help="neglect beams' My, Sz in the loss, accuracy calculation")

    # others
    parser.add_argument("--yield_factor", type=float, default=0.90)
    parser.add_argument("--plot_num", type=int, default=5)
    parser.add_argument("--training_time", type=float, default=0)

    args = parser.parse_args()
    return args



def get_loggings(ckpt_dir):
	logger = logging.getLogger(name='GraphLSTM')
	logger.setLevel(level=logging.INFO)
	# set formatter
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	# console handler
	stream_handler = logging.StreamHandler()
	stream_handler.setFormatter(formatter)
	logger.addHandler(stream_handler)
	# file handler
	file_handler = logging.FileHandler(os.path.join(ckpt_dir, "record.log"))
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)
	return logger


def set_random_seed(SEED: int):
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed(SEED)
    torch.backends.cudnn.deterministic = True



def main(args):
    # args, logger setting
    date_str = datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
    args.ckpt_dir = args.ckpt_dir / args.dataset_name / date_str
    args.ckpt_dir.mkdir(parents=True, exist_ok=True)
    logger = get_loggings(args.ckpt_dir)
    logger.info(f"ckpt_dir: {args.ckpt_dir}")
    logger.info(args)

    model_dir =  args.ckpt_dir / "Models"
    model_dir.mkdir(parents=True, exist_ok=True)

    # set random seed
    set_random_seed(args.random_seed)

    # device
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    GPU_name = torch.cuda.get_device_name()
    logger.info(f"My GPU is {GPU_name}\n")

    # dataset
    dset = dataset.GroundMotionDataset(folder=args.dataset_name,
                                       graph_type=args.whatAsNode,
                                       data_num=args.data_num,
                                       timesteps=args.timesteps,
                                       other_folders=args.other_datasets)
    logger.info(f"Num of structure graph: {len(dset)}")
    logger.info(f"structure_1 graph data: {dset[0]}\n")

    # normalization
    dataset_norm, norm_dict = normalization.normalize_dataset(dset, random_sample=args.random_sample)
    logger.info(f"Normlization structure_1 graph: {dataset_norm[0]}")
    logger.info(f"Normalized feastures: \n{norm_dict}\n")

    # remove the memory usage of original dataset
    del dset
    gc.collect()
    logger.info("Remove the memory usage of original dataset!\n")

    # spilt into train_dataset, valid dataset and test dataset
    data_num = len(dataset_norm)
    train_ratio, valid_ratio, test_ratio = args.train_split_ratio
    train_num, valid_num = int(data_num*train_ratio), int(data_num*valid_ratio)
    test_num = data_num - train_num - valid_num
    train_index, valid_index, test_index = random_split(list(range(data_num)), [train_num, valid_num, test_num])
    train_dataset = [dataset_norm[i] for i in list(train_index)]
    valid_dataset = [dataset_norm[i] for i in list(valid_index)]
    test_dataset = [dataset_norm[i] for i in list(test_index)]
    logger.info(f"train data: {len(train_dataset)}")
    logger.info(f"valid data: {len(valid_dataset)}")
    logger.info(f"test data: {len(test_dataset)}\n")

    # dataloader
    batch_size = args.batch_size
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    valid_loader = DataLoader(valid_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    miniBatch = next(iter(train_loader))
    logger.info(f"Batch size = {batch_size}")
    logger.info(f"One mini DataBatch for training:\n{miniBatch}")
    logger.info(f"graph sampled_index: {miniBatch.sampled_index}")
    logger.info(f"graph ptr: {miniBatch.ptr}")

    # start index, end index, inedx of target feature dict
    y_start, y_finish, target_dict = utils.get_target_index(args.target, args.neglect_beam_My_Sz)
    logger.info(f"Get predict target's index: start at {y_start}, end at {y_finish}")
    logger.info(f"Target index dictionary: {target_dict}\n")

    # num of features of data.x
    node_dim = dataset_norm[0].x.shape[1]
    edge_dim = dataset_norm[0].edge_attr.shape[1]
    ground_motion_dim = dataset_norm[0].ground_motions.shape[-1]
    output_dim = y_finish - y_start

    # save trainig arguments, norm_dict
    args_temp = deepcopy(args)
    args_temp.ckpt_dir = str(args_temp.ckpt_dir)
    with open(args.ckpt_dir / 'training_args.json', 'w') as f:
        json.dump(vars(args_temp), f)

    norm_dict_save = {}
    for key in norm_dict.keys():
        norm_dict_save[key] = norm_dict[key]

    with open(args.ckpt_dir / 'norm_dict.json', 'w') as f:
        json.dump(norm_dict_save, f)
        
    # save all dataset data path
    data_paths = {}
    data_paths['train'] = [graph.path for graph in train_dataset]
    data_paths['valid'] = [graph.path for graph in valid_dataset]
    data_paths['test'] = [graph.path for graph in test_dataset]
    with open(args.ckpt_dir / 'data_paths.json', 'w') as f:
        json.dump(data_paths, f)

    # construct model
    model_constructor_args = {
        'node_dim': node_dim, 'edge_dim': edge_dim, 'gnn_num_layers': args.gnn_num_layers, 'gnn_hidden_dim': args.gnn_hidden_dim,
        'head_num': args.head_num, 'latent_dim': args.latent_dim, 'graph_lstm_hidden_dim': args.graph_lstm_hidden_dim,
        'graph_lstm_num_layers': args.graph_lstm_num_layers,'node_lstm_hidden_dim': args.node_lstm_hidden_dim, 
        'node_lstm_num_layers': args.node_lstm_num_layers, 'ground_motion_dim': ground_motion_dim,
        'output_dim': output_dim, 'device': device}
    model = globals()[args.model](**model_constructor_args).to(device)
    logger.info(model)

    if args.pretrain != None:
        pretrain_path = Path("../Results/") / args.pretrain_path
        model.load_state_dict(torch.load(pretrain_path))
        logger.info(f"Loaded pretrain model: {pretrain_path}")

    # loss function
    criterion = globals()[args.loss_function]()

    # optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', factor=args.sch_factor, patience=args.patience, min_lr=1e-4)

    # accuracy metrics
    plasticHingeClassifier = accuracy.PlasticHingeClassifier(yield_factor=args.yield_factor)
    plasticHingeClassifier_1F = accuracy.PlasticHingeClassifier(yield_factor=args.yield_factor, specific_location=True, norm_dict=norm_dict)
    target_R2_record = utils.get_target_accuracy(args, target_dict)
    target_peak_record = utils.get_target_accuracy(args, target_dict)

    # acc, loss record
    epochs = args.epoch_num
    R2_acc_record = np.zeros((3, args.epoch_num))
    peak_acc_record = np.zeros((3, args.epoch_num))
    loss_record = np.zeros((3, args.epoch_num))
    best_loss = np.inf
    ps_record_Mz = np.zeros((3, args.epoch_num, 4))   # [3 for train/valid/test, epoch_num, 4 for TP/FP/FN/TN]
    ps_record_Mz_1F = np.zeros((3, args.epoch_num, 4))   # [3 for train/valid/test, epoch_num, 4 for TP/FP/FN/TN]

    # train
    start_time = time.time()
    for epoch in range(epochs):
        model.train()
        R2_acc_train = 0
        peak_acc_train = 0
        loss_train, elem_train = 0, 0
        for batch in tqdm(train_loader):
            batch = batch.to(device)
            output, keeped_indexes = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch, batch.ptr, batch.sampled_index, batch.ground_motions)
            x, y = batch.x[keeped_indexes], batch.y[keeped_indexes]

            mask = torch.ones(y.shape, dtype=bool)
            if args.neglect_beam_My_Sz:
                mask[:, :, (6,7,10,11)] = False    # neglect beam's MomentY
                mask[:, :, (24,25,28,29)] = False  # neglect beam's ShearZ
            mask_y = y[mask].reshape(y.shape[0], y.shape[1], -1)
            mask_output = output[mask].reshape(output.shape[0], output.shape[1], -1)

            # calculate loss
            loss = criterion(mask_output, mask_y)

            # calculate gradient and back propagation
            optimizer.zero_grad()  # clean the gradient
            loss.backward()
            optimizer.step()

            # calculate accuracy
            plasticHingeClassifier(x, output, y)
            plasticHingeClassifier_1F(x, output, y)
            R2_acc = accuracy.R2_score(mask_output, mask_y)
            peak_acc = accuracy.peak_R2_score(mask_output, mask_y)
            target_R2_record = utils.accumulate_target_accuracy(y_start, target_R2_record, target_dict, epoch, accuracy.R2_score, output, y, t_v=0)
            target_peak_record = utils.accumulate_target_accuracy(y_start, target_peak_record, target_dict, epoch, accuracy.peak_R2_score, output, y, t_v=0)
            loss_train += loss.item()
            R2_acc_train += R2_acc
            peak_acc_train += peak_acc
            elem_train += 1

        # record accuracy and loss for each epoch
        R2_acc_record[0][epoch] = R2_acc_train / elem_train  
        peak_acc_record[0][epoch] = peak_acc_train / elem_train  
        loss_record[0][epoch] = loss_train / elem_train
        target_R2_record = utils.average_target_accuracy(target_R2_record, epoch, elem_train, t_v=0)
        target_peak_record = utils.average_target_accuracy(target_peak_record, epoch, elem_train, t_v=0)
        train_ps_result_Mz, ps_record_Mz = plasticHingeClassifier.get_accuracy_and_reset(ps_record_Mz, epoch, t_v=0)
        train_ps_result_Mz_1F, ps_record_Mz_1F = plasticHingeClassifier_1F.get_accuracy_and_reset(ps_record_Mz_1F, epoch, t_v=0)


        # Get validation loss
        model.eval()
        with torch.no_grad():
            for t_v, loader in zip([1, 2], [valid_loader, test_loader]):
                R2_acc_valid = 0
                peak_acc_valid = 0
                loss_valid, elem_valid = 0, 0
                for batch in loader:
                    batch = batch.to(device)
                    output, keeped_indexes = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch, batch.ptr, batch.sampled_index, batch.ground_motions)
                    x, y = batch.x[keeped_indexes], batch.y[keeped_indexes]
                    
                    mask = torch.ones(y.shape, dtype=bool)
                    if args.neglect_beam_My_Sz:
                        mask[:, :, (6,7,10,11)] = False    # neglect beam's MomentY
                        mask[:, :, (24,25,28,29)] = False  # neglect beam's ShearZ
                    mask_y = y[mask].reshape(y.shape[0], y.shape[1], -1)
                    mask_output = output[mask].reshape(output.shape[0], output.shape[1], -1)

                    # calculate loss
                    loss = criterion(mask_output, mask_y)
                    
                    # calculate accuracy
                    plasticHingeClassifier(x, output, y)
                    plasticHingeClassifier_1F(x, output, y)
                    R2_acc = accuracy.R2_score(mask_output, mask_y)
                    peak_acc = accuracy.peak_R2_score(mask_output, mask_y)
                    target_R2_record = utils.accumulate_target_accuracy(y_start, target_R2_record, target_dict, epoch, accuracy.R2_score, output, y, t_v=t_v)
                    target_peak_record = utils.accumulate_target_accuracy(y_start, target_peak_record, target_dict, epoch, accuracy.peak_R2_score, output, y, t_v=t_v)
                    loss_valid += loss.item()
                    R2_acc_valid += R2_acc
                    peak_acc_valid += peak_acc
                    elem_valid += 1

                # record accuracy and loss for each epoch
                R2_acc_record[t_v][epoch] = R2_acc_valid / elem_valid
                peak_acc_record[t_v][epoch] = peak_acc_valid / elem_valid
                loss_record[t_v][epoch] = loss_valid / elem_valid
                target_R2_record = utils.average_target_accuracy(target_R2_record, epoch, elem_valid, t_v=t_v)
                target_peak_record = utils.average_target_accuracy(target_peak_record, epoch, elem_valid, t_v=t_v)
                
                if (t_v == 1):
                    valid_ps_result_Mz, ps_record_Mz = plasticHingeClassifier.get_accuracy_and_reset(ps_record_Mz, epoch, t_v=t_v)
                    valid_ps_result_Mz_1F, ps_record_Mz_1F = plasticHingeClassifier_1F.get_accuracy_and_reset(ps_record_Mz_1F, epoch, t_v=t_v)
                elif (t_v == 2):
                    test_ps_result_Mz, ps_record_Mz = plasticHingeClassifier.get_accuracy_and_reset(ps_record_Mz, epoch, t_v=t_v)
                    test_ps_result_Mz_1F, ps_record_Mz_1F = plasticHingeClassifier_1F.get_accuracy_and_reset(ps_record_Mz_1F, epoch, t_v=t_v)

        # learning rate scheduler 
        scheduler.step(loss_record[1][epoch])

        # record trining process to log file
        text = f'Epo: {epoch:03d}, T_Acc: {R2_acc_record[0][epoch]:.4f}, V_Acc: {R2_acc_record[1][epoch]:.4f}, t_Acc: {R2_acc_record[2][epoch]:.4f}, '
        text += f'T_Peak_Acc: {peak_acc_record[0][epoch]:.4f}, V_Peak_Acc: {peak_acc_record[1][epoch]:.4f}, t_Peak_Acc: {peak_acc_record[2][epoch]:.4f}, '
        text += f'T_Loss: {loss_record[0][epoch]:.6f}, V_Loss: {loss_record[1][epoch]:.6f}, t_Loss: {loss_record[2][epoch]:.6f}, '    
        text += f'T_hinge_node_Mz: {train_ps_result_Mz}, V_hinge_node_Mz: {valid_ps_result_Mz}, t_hinge_node_Mz: {test_ps_result_Mz},  '
        text += f'T_hinge_node_Mz_1F: {train_ps_result_Mz_1F}, V_hinge_node_Mz_1F: {valid_ps_result_Mz_1F}, t_hinge_node_Mz_1F: {test_ps_result_Mz_1F}'

        logger.critical(text)

        if (epoch + 1) % 50 == 0:
            torch.save(model.state_dict(), model_dir / f'model_Epoch{epoch+1}.pt')
        
        # Save model if train_loss is better
        if loss_record[1][epoch] < best_loss:
            best_loss = loss_record[1][epoch]
            torch.save(model.state_dict(), model_dir / 'model_Best.pt')
            text = f'Trained model saved, valid loss: {best_loss:.6f}'
            logger.critical(text)

    # record
    finish_time = time.time()
    args.training_time = (finish_time - start_time)/60
    logger.info("")
    logger.info(f"Time spent: {(finish_time - start_time)/60:.2f} min")
    logger.info("Finish time: " + datetime.now().strftime('%b %d, %H:%M:%S'))

    # save record
    record_dir = args.ckpt_dir / "Records"
    record_dir.mkdir(parents=True, exist_ok=True)
    with open(record_dir / "overall_acc_record.txt", 'w') as f: json.dump(R2_acc_record.tolist(), f)
    with open(record_dir / "peak_acc_record.txt", 'w') as f: json.dump(peak_acc_record.tolist(), f)
    with open(record_dir / "loss_record.txt", 'w') as f: json.dump(loss_record.tolist(), f)

    target_R2_record_new = {}
    for target, R2_racord in target_R2_record.items():
        target_R2_record_new[target] = R2_racord.tolist()
    with open(record_dir / "target_overall_acc_record.txt", 'w') as f: json.dump(target_R2_record_new, f)

    target_peak_record_new = {}
    for target, peak_racord in target_peak_record.items():
        target_peak_record_new[target] = peak_racord.tolist()
    with open(record_dir / "target_peak_acc_record.txt", 'w') as f: json.dump(target_peak_record_new, f)

    with open(record_dir / "ps_record_Mz.txt", 'w') as f: json.dump(ps_record_Mz.tolist(), f)
    with open(record_dir / "ps_record_Mz_1F.txt", 'w') as f: json.dump(ps_record_Mz_1F.tolist(), f)


    # plot figures
    plot.plot_learningCurve(R2_acc_record, args.ckpt_dir, title=', '.join([args.model, date_str]))
    plot.plot_lossCurve(loss_record, args.ckpt_dir, title=', '.join([args.model, args.loss_function, date_str]))
    
    plot.plot_target_accuracy(target_R2_record, args.epoch_num, args.neglect_beam_My_Sz, args.ckpt_dir, evaluation="Overall_R2_Score")
    plot.plot_target_accuracy(target_peak_record, args.epoch_num, args.neglect_beam_My_Sz, args.ckpt_dir, evaluation="Peak_R2_Score")
    
    plot.plot_plastic_hinge_accuracy(ps_record_Mz, args.ckpt_dir)
    plot.plot_plastic_hinge_accuracy(ps_record_Mz_1F, args.ckpt_dir, specific_location=True)
    
    # reload the best model
    model = globals()[args.model](**model_constructor_args).to(device)
    model.load_state_dict(torch.load(args.ckpt_dir / 'model_Best.pt'))

    worst_case_index, best_case_index = plot.plot_test_accuracy_distribution(test_dataset, model, args.neglect_beam_My_Sz, args.ckpt_dir)
    logger.info(f"worst case index: {worst_case_index}, best case index: {best_case_index}")
    for case_name, case_index in zip(["Worst", "Best"], [worst_case_index, best_case_index]):
        logger.info(f"visualizing {case_name}")
        visualize.visualize_ground_motion(args.ckpt_dir, test_dataset, case_name, norm_dict, index=case_index)
        for response in ["Acceleration_X", "Acceleration_Z", 
                         "Velocity_X", "Velocity_Z", 
                         "Displacement_X", "Displacement_Z", 
                         "Moment_Y_Column", "Moment_Y_Xbeam", "Moment_Y_Zbeam",
                         "Moment_Z_Column", "Moment_Z_Xbeam", "Moment_Z_Zbeam", 
                         "Shear_Y_Column", "Shear_Y_Xbeam", "Shear_Y_Zbeam", 
                         "Shear_Z_Column", "Shear_Z_Xbeam", "Shear_Z_Zbeam"]:
            visualize.visualize_response(model, args.ckpt_dir, test_dataset, case_name, norm_dict, accuracy.R2_score, response=response, index=case_index)

    # visualize graph embedding
    visualize.visualize_graph_embedding(model, args.ckpt_dir, train_dataset, "train", norm_dict, args.batch_size)
    visualize.visualize_graph_embedding(model, args.ckpt_dir, valid_dataset, "valid", norm_dict, args.batch_size)
    visualize.visualize_graph_embedding(model, args.ckpt_dir, test_dataset, "test", norm_dict, args.batch_size)

    # visualize response
    for structure_index in range(args.plot_num):
        print(f"\n Plotting structure {structure_index}:")

        visualize.visualize_ground_motion(args.ckpt_dir, train_dataset, "train", norm_dict, index=structure_index)
        visualize.visualize_ground_motion(args.ckpt_dir, valid_dataset, "valid", norm_dict, index=structure_index)
        visualize.visualize_ground_motion(args.ckpt_dir, test_dataset, "test", norm_dict, index=structure_index)

        for response in ["Acceleration_X", "Velocity_X", "Displacement_X", 
                         "Moment_Z_Column", "Moment_Z_Xbeam", "Moment_Z_Zbeam", 
                         "Shear_Y_Column", "Shear_Y_Xbeam", "Shear_Y_Zbeam"]:
            visualize.visualize_response(model, args.ckpt_dir, train_dataset, "train", norm_dict, accuracy.R2_score, response=response, index=structure_index)
            visualize.visualize_response(model, args.ckpt_dir, valid_dataset, "valid", norm_dict, accuracy.R2_score, response=response, index=structure_index)
            visualize.visualize_response(model, args.ckpt_dir, test_dataset, "test", norm_dict, accuracy.R2_score, response=response, index=structure_index)
        
        # attention weight
        visualize.visualize_graph_attention(model, args.ckpt_dir, train_dataset, "train", norm_dict, args.head_num, index=structure_index)
        visualize.visualize_graph_attention(model, args.ckpt_dir, valid_dataset, "valid", norm_dict, args.head_num, index=structure_index)
        visualize.visualize_graph_attention(model, args.ckpt_dir, test_dataset, "test", norm_dict, args.head_num, index=structure_index)
        
        # plastic hinge
        # visualize.visualize_plasticHinge(model, args.ckpt_dir, train_dataset, "train", norm_dict, plasticHingeClassifier, index=structure_index)
        # visualize.visualize_plasticHinge(model, args.ckpt_dir, valid_dataset, "valid", norm_dict, plasticHingeClassifier, index=structure_index)
        # visualize.visualize_plasticHinge(model, args.ckpt_dir, test_dataset, "test", norm_dict, plasticHingeClassifier, index=structure_index)




if __name__ == "__main__":
	args = parse_args()
	main(args)