import torch
import torch.nn as nn
import torch_geometric as tg
from torch_geometric.nn import global_mean_pool
from .layers import *


class GraphLatentEncoder(nn.Module):
    def __init__(
        self, node_dim, edge_dim, gnn_num_layers, head_num, gnn_hidden_dim, latent_dim
    ):
        super(GraphLatentEncoder, self).__init__()
        self.gnn_num_layers = gnn_num_layers
        self.conv_layers = nn.ModuleList()
        for i in range(gnn_num_layers):
            in_dim = node_dim if i == 0 else gnn_hidden_dim
            out_dim = latent_dim if i == (gnn_num_layers - 1) else gnn_hidden_dim
            self.conv_layers.append(
                tg.nn.GATv2Conv(
                    in_dim, out_dim, heads=head_num, concat=False, edge_dim=edge_dim
                )
            )

    def forward(self, x, edge_index, edge_attr, batch):
        for i in range(self.gnn_num_layers):
            if i == 0:
                x, (return_edge_index, attention_weights) = self.conv_layers[i](
                    x, edge_index, edge_attr, return_attention_weights=True
                )
            else:
                x = self.conv_layers[i](x, edge_index, edge_attr)
        latent = global_mean_pool(x, batch)
        return latent, return_edge_index, attention_weights


class GraphTimeSeriesEncoder(nn.Module):
    def __init__(
        self,
        latent_dim,
        graph_lstm_hidden_dim,
        graph_lstm_num_layers,
        ground_motion_dim,
    ):
        super(GraphTimeSeriesEncoder, self).__init__()

        input_dim = latent_dim + ground_motion_dim
        self.lstm = nn.LSTM(
            input_dim, graph_lstm_hidden_dim, graph_lstm_num_layers, batch_first=True
        )

    def forward(self, latent, ground_motions):
        # latent: [batch_size, latent_dim]
        # ground_motions: [batch_size, timesteps(2000), ground_motion_dim(20)]
        # first expand latent to [batch_size, timesteps(2000), latent_dim],
        # then concat latent with ground_motions [batch_size, timesteps(2000), latent_dim + gm_per_timestep]

        timesteps = ground_motions.shape[1]
        latent = latent.unsqueeze(1).expand(-1, timesteps, -1)
        graph_ground_motion_input = torch.cat([latent, ground_motions], dim=2)
        graph_time_series_behavior, (_, _) = self.lstm(graph_ground_motion_input)
        return graph_time_series_behavior


class NodeTimeSeriesDecoder(nn.Module):
    def __init__(
        self,
        node_dim,
        graph_lstm_hidden_dim,
        ground_motion_dim,
        node_lstm_hidden_dim,
        node_lstm_num_layers,
        output_dim,
        device,
    ):
        super(NodeTimeSeriesDecoder, self).__init__()

        self.node_dim = node_dim
        self.graph_lstm_hidden_dim = graph_lstm_hidden_dim
        self.ground_motion_dim = ground_motion_dim
        self.num_layers = node_lstm_num_layers
        self.output_dim = output_dim
        self.device = device

        self.input_dim = node_dim + graph_lstm_hidden_dim + ground_motion_dim
        self.node_encoder = MLP(
            self.input_dim, [], node_lstm_hidden_dim, act=True, dropout=False
        )
        self.lstmCellList = nn.ModuleList()
        for _ in range(node_lstm_num_layers):
            self.lstmCellList.append(
                nn.LSTMCell(node_lstm_hidden_dim, node_lstm_hidden_dim)
            )
        self.response_decoder = MLP(
            node_lstm_hidden_dim * 2, [64], output_dim, act=True, dropout=False
        )

    def create_ground_motion_graph(self, gms, node, ptr, latent):
        # gms: [batch_size, ground_motion_dim]
        # latent: [batch_size, graph_lstm_hidden_dim]
        bs = len(ptr) - 1
        x = torch.zeros(node.shape[0], self.input_dim).to(self.device)
        x[:, 0 : self.node_dim] = node
        for b in range(bs):
            x[
                ptr[b] : ptr[b + 1],
                self.node_dim : self.node_dim + self.graph_lstm_hidden_dim,
            ] = latent[b]
            x[ptr[b] : ptr[b + 1], -self.ground_motion_dim :] = gms[b]
        x = self.node_encoder(x)
        return x

    def next_cell_input(self, H, gms, ptr):
        # gms: [batch_size, ground_motion_dim]
        H_gm = H.clone()
        bs = len(ptr) - 1
        for b in range(bs):
            H_gm[ptr[b] : ptr[b + 1], -self.ground_motion_dim :] = gms[b]
        return H_gm

    def create_response(self, H, C):
        state = torch.cat([H, C], dim=1)
        node_out = self.response_decoder(state)
        return node_out

    def forward_one_timestep(self, gms, node, ptr, latent, H_list, C_list):
        x = self.create_ground_motion_graph(gms, node, ptr, latent)

        for i in range(self.num_layers):
            H_list[i] = x if H_list[i] is None else H_list[i]
            C_list[i] = x if C_list[i] is None else C_list[i]

        for i in range(self.num_layers):
            if i == 0:
                H_list[i], C_list[i] = self.lstmCellList[i](x, (H_list[i], C_list[i]))
            else:
                H_list[i], C_list[i] = self.lstmCellList[i](
                    self.next_cell_input(H_list[i - 1], gms, ptr),
                    (H_list[i], C_list[i]),
                )

        y = self.create_response(H_list[-1], C_list[-1])
        return H_list, C_list, y

    def forward(self, node, ptr, graph_time_series_behavior, ground_motions):
        # preparation
        timesteps = graph_time_series_behavior.shape[1]
        output = torch.zeros((node.shape[0], timesteps, self.output_dim)).to(
            self.device
        )
        H_list = [None for _ in range(self.num_layers)]
        C_list = [None for _ in range(self.num_layers)]

        # loop for each time step (make ground_motions: [timesteps(2000), batch_size, gm_per_timestep])
        for i, (gms, latent) in enumerate(
            zip(
                ground_motions.permute(1, 0, 2),
                graph_time_series_behavior.permute(1, 0, 2),
            )
        ):
            H_list, C_list, out = self.forward_one_timestep(
                gms, node, ptr, latent, H_list, C_list
            )
            output[:, i, :] = out
        return output


class GraphLSTM(nn.Module):
    def __init__(
        self,
        node_dim,
        edge_dim,
        gnn_num_layers,
        head_num,
        gnn_hidden_dim,
        latent_dim,
        graph_lstm_hidden_dim,
        graph_lstm_num_layers,
        node_lstm_hidden_dim,
        node_lstm_num_layers,
        ground_motion_dim,
        output_dim,
        device,
    ):
        super(GraphLSTM, self).__init__()

        self.device = device

        self.graphLatentEncoder = GraphLatentEncoder(
            node_dim, edge_dim, gnn_num_layers, head_num, gnn_hidden_dim, latent_dim
        )
        self.graphTimeSeriesEncoder = GraphTimeSeriesEncoder(
            latent_dim, graph_lstm_hidden_dim, graph_lstm_num_layers, ground_motion_dim
        )
        self.nodeTimeSeriesDecoder = NodeTimeSeriesDecoder(
            node_dim,
            graph_lstm_hidden_dim,
            ground_motion_dim,
            node_lstm_hidden_dim,
            node_lstm_num_layers,
            output_dim,
            device,
        )

    def sample_node(self, x, ptr, sampled_indexes, sample_node):
        # if don't samplem, return original x and sampled_indexes=all index
        if not sample_node:
            keeped_indexes = [i for i in range(x.shape[0])]
            return x, keeped_indexes, ptr

        # sampled_indexes = [sampled_index for i in batch_size]
        bs = len(ptr) - 1
        keeped_indexes = []
        new_ptr = [0]
        for b in range(bs):
            sampled_index = sampled_indexes[b]
            keeped_indexes += [(ptr[b] + index).item() for index in sampled_index]
            new_ptr.append(new_ptr[-1] + len(sampled_index))
        x = x[keeped_indexes]
        return x, keeped_indexes, new_ptr

    def forward(
        self,
        x,
        edge_index,
        edge_attr,
        batch,
        ptr,
        sampled_indexes,
        ground_motions,
        sample_node=True,
    ):
        # graph latent
        latent, _, _ = self.graphLatentEncoder(x, edge_index, edge_attr, batch)

        # graph level time series behavior
        graph_time_series_behavior = self.graphTimeSeriesEncoder(latent, ground_motions)

        # sample node
        x, keeped_indexes, ptr = self.sample_node(x, ptr, sampled_indexes, sample_node)

        # node level time series prediction
        output = self.nodeTimeSeriesDecoder(
            x, ptr, graph_time_series_behavior, ground_motions
        )

        return output, keeped_indexes
