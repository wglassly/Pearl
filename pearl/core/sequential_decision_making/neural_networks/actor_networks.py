"""
This module defines several types of actor neural networks.

Constants:
    ActorNetworkType: a type (and therefore a callable) getting state_dim, hidden_dims, output_dim and producing a neural network with
    able to produce an action probability given a state.
"""


from typing import Callable, List

import torch

import torch.nn as nn
import torch.nn.functional as F
from pearl.core.common.neural_networks.auto_device_nn_module import AutoDeviceNNModule


class VanillaActorNetwork(AutoDeviceNNModule):
    def __init__(self, input_dim, hidden_dims, output_dim):
        super(VanillaActorNetwork, self).__init__()

        self.fc1 = nn.Linear(input_dim, hidden_dims[0])
        hiddens = []
        for i in range(len(hidden_dims) - 1):
            hiddens.append(nn.Linear(hidden_dims[i], hidden_dims[i + 1]))
            hiddens.append(nn.ReLU())
        self.hiddens = nn.Sequential(*hiddens)
        self.fc2 = nn.Linear(hidden_dims[-1], output_dim)

    def forward(self, x):
        value = F.relu(self.fc1(x))
        value = self.hiddens(value)
        return F.softmax(self.fc2(value), dim=1)


class VanillaContinuousActorNetwork(VanillaActorNetwork):
    """
    This is vanilla version of deterministic actor network
    Given input state, output an action vector
    Args
        output_dim: action dimension
    """

    def __init__(self, input_dim, hidden_dims, output_dim):
        super(VanillaContinuousActorNetwork, self).__init__(
            input_dim, hidden_dims, output_dim
        )

    def forward(self, x):
        value = F.relu(self.fc1(x))
        value = self.hiddens(value)
        return torch.tanh(self.fc2(value))


ActorNetworkType = Callable[[int, int, List[int], int], nn.Module]
