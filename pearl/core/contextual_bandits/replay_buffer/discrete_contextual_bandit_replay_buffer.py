import random
from collections import deque

import torch

from pearl.api.action import Action
from pearl.api.action_space import ActionSpace
from pearl.api.state import SubjectiveState

from pearl.core.common.replay_buffer.tensor_based_replay_buffer import (
    TensorBasedReplayBuffer,
)
from pearl.core.common.replay_buffer.transition import Transition, TransitionBatch


class DiscreteContextualBanditReplayBuffer(TensorBasedReplayBuffer):
    """
    DiscreteContextualBanditReplayBuffer has the following key differences from other replay buffers
    - No next action or next state related
    - action is action idx instead of action value
    - done is not needed, as for contextual bandit, it is always True
    """

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.memory = deque([], maxlen=capacity)

    def push(
        self,
        state: SubjectiveState,
        action: Action,
        reward: float,
        next_state: SubjectiveState,
        curr_available_actions: ActionSpace,
        next_available_actions: ActionSpace,
        action_space: ActionSpace,
        done: bool,
    ) -> None:
        # signature of push is the same as others, in order to match codes in PearlAgent
        # TODO add curr_available_actions and curr_available_actions_mask if needed in the future
        self.memory.append(
            Transition(
                state=TensorBasedReplayBuffer._process_single_state(state),
                action=action,
                reward=TensorBasedReplayBuffer._process_single_reward(reward),
            )
        )

    def sample(self, batch_size: int) -> TransitionBatch:
        samples = random.sample(self.memory, batch_size)
        return TransitionBatch(
            state=torch.cat([x.state for x in samples]),
            action=torch.stack([x.action for x in samples]),
            reward=torch.cat([x.reward for x in samples]),
        )

    def __len__(self) -> int:
        return len(self.memory)