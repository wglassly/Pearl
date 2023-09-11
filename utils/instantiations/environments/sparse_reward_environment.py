"""
This file contains environment to simulate sparse rewards
Also contains history summarization module that needs to be used together
when defining PearlAgent

Set up is following:
2d box environment, where the agent gets initialized in a center of a square arena,
and there is a target - 2d point, randomly generated in the arena.
The agent gets reward 0 only when it gets close enough to the target, otherwise the reward is -1.

There are 2 versions in this file:
- one for discrete action space
- one for contineous action space
"""
import math
import random
from abc import abstractmethod
from collections import namedtuple

import torch

from pearl.api.action import Action
from pearl.api.action_result import ActionResult
from pearl.api.action_space import ActionSpace

from pearl.api.environment import Environment

from pearl.history_summarization_modules.history_summarization_module import (
    HistorySummarizationModule,
    SubjectiveState,
)
from pearl.replay_buffers.replay_buffer import ReplayBuffer
from pearl.replay_buffers.transition import TransitionBatch
from pearl.utils.instantiations.action_spaces.action_spaces import DiscreteActionSpace

SparseRewardEnvironmentObservation = namedtuple(
    "SparseRewardEnvironmentObservation", ["agent_position", "goal"]
)


class SparseRewardEnvironment(Environment):
    def __init__(
        self,
        length: float,
        height: float,
        max_episode_duration: int = 500,
        reward_distance: float = 1,
    ):
        self._length = length
        self._height = height
        self._max_episode_duration = max_episode_duration
        # reset will initialize following
        self._agent_position = None
        self._goal = None
        self._step_count = 0
        self._reward_distance = reward_distance

    @abstractmethod
    def step(self, action: Action) -> ActionResult:
        pass

    def reset(self) -> (SparseRewardEnvironmentObservation, ActionSpace):
        # reset (x, y)
        self._agent_position = (self._length / 2, self._height / 2)
        self._goal = (random.uniform(0, self._length), random.uniform(0, self._height))
        self._step_count = 0
        return (
            SparseRewardEnvironmentObservation(
                agent_position=self._agent_position, goal=self._goal
            ),
            self.action_space,
        )

    def _update_position(self, delta) -> None:
        """
        This API is to update and clip and ensure agent always stay in map
        """
        delta_x, delta_y = delta
        x, y = self._agent_position
        self._agent_position = (
            max(min(x + delta_x, self._length), 0),
            max(min(y + delta_y, self._height), 0),
        )

    def _check_win(self) -> bool:
        """
        Return:
            True if reached goal
            False if not reached goal
        """
        if math.dist(self._agent_position, self._goal) < self._reward_distance:
            return True
        return False


class ContinuousSparseRewardEnvironment(SparseRewardEnvironment):
    """
    Given action vector (x, y)
    agent position is updated accordingly
    """

    def step(self, action: Action) -> ActionResult:
        self._update_position(action)

        has_win = self._check_win()
        self._step_count += 1
        terminated = has_win or self._step_count >= self._max_episode_duration
        return ActionResult(
            observation=SparseRewardEnvironmentObservation(
                agent_position=self._agent_position, goal=self._goal
            ),
            reward=0 if has_win else -1,
            terminated=terminated,
            truncated=False,
            info=None,
        )

    @property
    def action_space(self) -> ActionSpace:
        return None


class DiscreteSparseRewardEnvironment(ContinuousSparseRewardEnvironment):
    """
    Given action count N, action index will be 0,...,N-1
    For action n, position will be changed by:
    x +=  cos(360/N * n) * step_size
    y +=  sin(360/N * n) * step_size
    """

    def __init__(
        self,
        length: float,
        height: float,
        step_size: float = 0.01,
        action_count: int = 4,
        max_episode_duration: int = 500,
        reward_distance: float = None,
    ):
        super(DiscreteSparseRewardEnvironment, self).__init__(
            length,
            height,
            max_episode_duration,
            reward_distance if reward_distance is not None else step_size,
        )
        self._step_size = step_size
        self._action_count = action_count
        self._actions = [
            (
                math.cos(2 * math.pi / self._action_count * i),
                math.sin(2 * math.pi / self._action_count * i),
            )
            * self._step_size
            for i in range(action_count)
        ]

    def step(self, action: Action) -> ActionResult:
        assert action < self._action_count and action >= 0
        return super(DiscreteSparseRewardEnvironment, self).step(self._actions[action])

    @property
    def action_space(self) -> DiscreteActionSpace:
        return DiscreteActionSpace(range(self._action_count))


class SparseRewardEnvSummarizationModule(HistorySummarizationModule):
    """
    A history summarization module that is used for sparse reward game environment
    """

    def __init__(self, **options) -> None:
        pass

    def summarize_history(
        self,
        subjective_state: SubjectiveState,
        observation: SparseRewardEnvironmentObservation,
    ) -> SubjectiveState:
        # for this game, state is a cat between agent position and goal position
        return torch.Tensor(list(observation.agent_position) + list(observation.goal))

    def learn(self, replay_buffer: ReplayBuffer) -> None:
        pass

    def learn_batch(self, batch: TransitionBatch) -> None:
        pass