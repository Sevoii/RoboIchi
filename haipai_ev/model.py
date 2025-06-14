import torch
from torch import nn


# Embedding layer for each tile
class TileEmbedding(nn.Module):
    def __init__(self, dmodel):
        super().__init__()

        self.embedding = nn.Embedding(37, dmodel)
        self.tedashi_bias = nn.Parameter(torch.randn(1, 1, dmodel))
        self.tsumogiri_bias = nn.Parameter(torch.randn(1, 1, dmodel))
        self.riichi_bias = nn.Parameter(torch.randn(1, 1, dmodel))
        self.called_bias = nn.Parameter(torch.randn(1, 1, dmodel))

    def forward(self, x, tedashi, tsumogiri, riichi, called):
        return (self.embedding(x) +
                tedashi * self.tedashi_bias +
                tsumogiri + self.tsumogiri_bias +
                riichi * self.riichi_bias +
                called + self.called_bias)


# Linear layer for cont points -> points diff should already be normalized
class PointEmbedding(nn.Module):
    def __init__(self, dmodel):
        super().__init__()
        self.dmodel = dmodel

        self.linear = nn.Linear(1, dmodel)

    def forward(self, x):
        return self.linear(x)


# Seat embedding (i.e. for dealer or current player)
class SeatEmbedding(nn.Embedding):
    def __init__(self, dmodel):
        super().__init__(4, dmodel)


# Token that says if riichi or not
class RiichiEmbedding(nn.Embedding):
    def __init__(self, dmodel):
        super().__init__(2, dmodel)


# Generic Integer Embedding layer, goes from 0-9
class IntEmbedding(nn.Embedding):
    def __init__(self, dmodel):
        super().__init__(10, dmodel)


class Brain(nn.Module):
    def __init__(self, dmodel=128):
        super().__init__()
        self.cls_token = nn.Parameter(torch.randn(1, 1, dmodel))

        self.transformer = nn.Transformer(d_model=dmodel, batch_first=True)
        self.decoder = nn.Linear(dmodel, 1)

    def forward(self, x):

        batch_size = x.size(0)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)

        x = self.pos_enc(x)
        x = self.transformer(x)
        cls_output = x[:, 0, :]

        return self.decoder(cls_output)

    def pos_enc(self, x):
        batch_size, seq_len, d_model = x.shape
        positions = torch.arange(0, seq_len, dtype=torch.float).unsqueeze(1)
        dims = torch.arange(0, d_model, dtype=torch.float)
        angle_rates = 1 / torch.pow(10000, (2 * (dims // 2)) / d_model)
        pos_enc = positions * angle_rates
        pos_enc[:, 0::2] = torch.sin(pos_enc[:, 0::2])
        pos_enc[:, 1::2] = torch.cos(pos_enc[:, 1::2])
        return pos_enc.unsqueeze(0).expand(batch_size, -1, -1) + x
