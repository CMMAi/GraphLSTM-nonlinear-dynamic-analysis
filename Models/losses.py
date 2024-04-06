# Self-defined loss class
# https://spandan-madan.github.io/A-Collection-of-important-tasks-in-pytorch/
import torch
import torch.nn as nn


class MAE(nn.Module):
    def __init__(self):
        super(MAE, self).__init__()
        self.name = "MAE"

    def forward(self, node_out, node_y):
        mae = torch.sum(torch.mean(torch.abs(node_out - node_y), dim=(0, 1)))
        return mae


class MSE(nn.Module):
    def __init__(self):
        super(MSE, self).__init__()
        self.name = "MSE"

    def forward(self, node_out, node_y):
        mse = torch.sum(torch.mean((node_out - node_y) ** 2, dim=(0, 1)))
        return mse


class RMSE(nn.Module):
    def __init__(self):
        super(RMSE, self).__init__()
        self.name = "RMSE"

    def forward(self, node_out, node_y):
        mse = torch.sum(torch.mean((node_out - node_y) ** 2, dim=(0, 1)))
        rmse = torch.sqrt(mse)
        return rmse


class MAPE(nn.Module):
    def __init__(self, accuracy_threshold):
        super(MAPE, self).__init__()
        self.name = "MAPE"
        self.accuracy_threshold = accuracy_threshold

    def forward(self, node_out, node_y):
        condition = torch.abs(node_y) > self.accuracy_threshold
        node_out = node_out[condition]
        node_y = node_y[condition]
        mape = torch.mean(torch.abs((node_out - node_y) / node_y))
        return mape


class PhysicalConstraint_Loss(nn.Module):
    def __init__(self, alpha=1, norm_dict=None):
        super(PhysicalConstraint_Loss, self).__init__()
        self.alpha = alpha
        self.norm_dict = norm_dict
        self.frequency = 20

    def forward(self, node_out, node_y):
        """
        t: true, u: derivate
        1. disp_u  - vel_t --> 0
        2. disp_uu - acc_t --> 0
        3. vel_u   - acc_t --> 0
        """
        # true
        acc_t = node_y[:, :, 0]
        vel_t = node_y[:, :, 1]

        # predict
        vel_p = node_out[:, :, 1]
        disp_p = node_out[:, :, 2]

        # predict -> derivate
        # disp_u = delta_disp / delta_t = delta_disp * frequency
        append = torch.zeros((node_y.shape[0], 1)).to(node_y.device)
        disp_u = (
            torch.diff(disp_p, dim=1, append=append)
            * self.norm_dict["disp"][1]
            / self.norm_dict["vel"][1]
            * self.frequency
        )
        disp_uu = (
            torch.diff(disp_u, dim=1, append=append)
            * self.norm_dict["vel"][1]
            / self.norm_dict["acc"][1]
            * self.frequency
        )
        vel_u = (
            torch.diff(vel_p, dim=1, append=append)
            * self.norm_dict["vel"][1]
            / self.norm_dict["acc"][1]
            * self.frequency
        )

        # physical loss
        disp_u_loss = torch.mean((disp_u - vel_t) ** 2)
        disp_uu_loss = torch.mean((disp_uu - acc_t) ** 2)
        vel_u_loss = torch.mean((vel_u - acc_t) ** 2)
        phy_loss = self.alpha * (disp_u_loss + disp_uu_loss + vel_u_loss)

        return phy_loss
