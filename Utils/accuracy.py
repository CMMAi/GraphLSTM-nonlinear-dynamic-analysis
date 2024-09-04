import torch
import torch.nn as nn
import copy
from Utils import normalization    


def R2_score(node_out, node_y):
    y_bar = torch.sum(torch.mean(node_y))
    SS_tot = torch.sum((node_y - y_bar)**2)
    SS_res = torch.sum((node_y - node_out)**2)
    R2 = 1 - SS_res / SS_tot
    return R2


def peak_R2_score(node_out, node_y):
    out = torch.max(node_out.abs(), dim=1)[0]
    y = torch.max(node_y.abs(), dim=1)[0]
    mask = (y != 0)     # mask for zero-value response
    return R2_score(out[mask], y[mask])



 

def normalized_MSE(node_out, node_y):
    N = torch.numel(node_y)
    max_val = torch.max(torch.abs(node_y))
    node_out, node_y = node_out/max_val, node_y/max_val
    error = (1/N) * torch.sum((node_out - node_y)**2)
    return error



class PlasticHingeClassifier(nn.Module):
    def __init__(self, yield_factor=0.90, specific_location=False, norm_dict=None):
        super(PlasticHingeClassifier, self).__init__()
        self.specific_location = specific_location
        self.norm_dict = norm_dict

        self.section_info_dim = 2
        self.Myield_start_index = 24
        self.Myield_end_index = 24 + (6 - 1) * self.section_info_dim + 1
        self.Myield_yn_index = 28
        self.Myield_yp_index = 30
        self.output_start_index = 12  # (Mz, Sy): 6   --> (My, Mz, Sy, Sz): 12
        self.output_end_index = 18    # (Mz, Sy): 12  --> (My, Mz, Sy, Sz): 18 
        self.output_yn_index = 14     # (Mz, Sy): 8   --> (My, Mz, Sy, Sz): 14
        self.output_yp_index = 15     # (Mz, Sy): 9   --> (My, Mz, Sy, Sz): 15
        self.Hz = 20
        self.yield_factor = yield_factor
        self.section_accuracy_Mz = [0, 0, 0, 0]  # [TP, FP, FN, TN]


    def get_accuracy_and_reset(self, record_Mz, epoch, t_v=0):
        result_Mz = copy.deepcopy(self.section_accuracy_Mz)
        if record_Mz is not None:
            record_Mz[t_v, epoch, 0:4] = result_Mz
        self.section_accuracy_Mz = [0, 0, 0, 0]
        return result_Mz, record_Mz


    def forward(self, x, node_out, node_y):
        if self.specific_location:
            # first find the 1F_bottom and 1F_top mask
            bot_norm_val = normalization.normalize_coord(0, self.norm_dict)
            top_norm_val = normalization.normalize_coord(1, self.norm_dict)
            mask_1F_column_bot = (abs(x[:, 4] - bot_norm_val) < 1e-4)
            mask_1F_column_top = (abs(x[:, 4] - top_norm_val) < 1e-4)
            
            # 1F_column_bottom uses y_p, 1F_column_top uses y_n
            condition_not_zero_bot = (x[mask_1F_column_bot, self.Myield_yp_index] != 0)
            condition_not_zero_top = (x[mask_1F_column_top, self.Myield_yn_index] != 0)
            condition_real_bot = (torch.max(node_y[mask_1F_column_bot, :, self.output_yp_index].abs(), dim=1)[0] >= self.yield_factor * x[mask_1F_column_bot, self.Myield_yp_index])
            condition_real_top = (torch.max(node_y[mask_1F_column_top, :, self.output_yn_index].abs(), dim=1)[0] >= self.yield_factor * x[mask_1F_column_top, self.Myield_yn_index])
            condition_pred_bot = (torch.max(node_out[mask_1F_column_bot, :, self.output_yp_index].abs(), dim=1)[0] >= self.yield_factor * x[mask_1F_column_bot, self.Myield_yp_index])
            condition_pred_top = (torch.max(node_out[mask_1F_column_top, :, self.output_yn_index].abs(), dim=1)[0] >= self.yield_factor * x[mask_1F_column_top, self.Myield_yn_index])

            condition_not_zero = torch.cat([condition_not_zero_bot, condition_not_zero_top], dim=0)
            condition_real = torch.cat([condition_real_bot, condition_real_top], dim=0)
            condition_pred = torch.cat([condition_pred_bot, condition_pred_top], dim=0)

        else:
            # node_out, node_y: [node_num in a mini-batch, output dimension]
            condition_not_zero = (x[:, self.Myield_start_index : self.Myield_end_index : self.section_info_dim] != 0)
            condition_real = (torch.max(node_y[:, :, self.output_start_index : self.output_end_index].abs(), dim=1)[0] >= self.yield_factor * x[:, self.Myield_start_index : self.Myield_end_index : self.section_info_dim])
            condition_pred = (torch.max(node_out[:, :, self.output_start_index : self.output_end_index].abs(), dim=1)[0] >= self.yield_factor * x[:, self.Myield_start_index : self.Myield_end_index : self.section_info_dim])
        
        
        plastic_hinge_real = torch.logical_and(condition_real, condition_not_zero)
        plastic_hinge_pred = torch.logical_and(condition_pred, condition_not_zero)

        # get TP, FP, FN, TN
        TP = torch.sum(torch.logical_and(plastic_hinge_real == True, plastic_hinge_pred == True)).item()
        FP = torch.sum(torch.logical_and(plastic_hinge_real == False, plastic_hinge_pred == True)).item()
        FN = torch.sum(torch.logical_and(plastic_hinge_real == True, plastic_hinge_pred == False)).item()
        TN = torch.sum(torch.logical_and(plastic_hinge_real == False, plastic_hinge_pred == False)).item()
        
        # update accuracy
        self.section_accuracy_Mz[0] += TP
        self.section_accuracy_Mz[1] += FP
        self.section_accuracy_Mz[2] += FN
        self.section_accuracy_Mz[3] += TN













if __name__ == '__main__':
    # print("Hello")
    # graph = torch.load("E:\TimeHistoryAnalysis\Data\\Nonlinear_Dynamic_Analysis_test\structure_3\structure_graph_NodeAsNode.pt")
    # classifier = PlasticHingeClassifier()
    # result = classifier(graph.x, graph.y, graph.y)
    # print(result)

    y = torch.tensor([[4, 6, 9, 6, 2],
                      [3, 7, 12, 4, 1],
                      [7, 20, 6, 3, 1]])
    pred = torch.tensor([[3, 5, 5, 6, 8],
                         [10, 4, 2, 1, 5],
                         [22, 4, 7, 2, 1]])
    #print(peak_rel_acc(pred, y))










