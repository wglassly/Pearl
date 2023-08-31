#!/usr/bin/env fbpython
# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.
import unittest

import torch
from pearl.core.common.replay_buffer.transition import TransitionBatch
from pearl.core.contextual_bandits.policy_learners.deep_linear_bandit import (
    DeepLinearBandit,
)
from pearl.core.contextual_bandits.policy_learners.exploration_module.linucb_exploration import (
    LinUCBExploration,
)
from pearl.utils.action_spaces import DiscreteActionSpace


class TestDeepLinearBandits(unittest.TestCase):
    def test_deep_linucb(self) -> None:
        feature_dim = 15  # It is important to keep this different from hidden_dims
        batch_size = feature_dim * 4  # It is important to have enough data for training
        policy_learner = DeepLinearBandit(
            feature_dim=feature_dim,
            hidden_dims=[16, 16],
            learning_rate=0.01,
            exploration_module=LinUCBExploration(alpha=0.1),
        )
        self.assertEqual(feature_dim, policy_learner.feature_dim)
        state = torch.randn(batch_size, 3)
        action = torch.randn(batch_size, feature_dim - 3)
        batch = TransitionBatch(
            state=state,
            action=action,
            # y = sum of state + sum of action
            reward=state.sum(-1) + action.sum(-1),
            weight=torch.ones(batch_size),
        )
        losses = []
        for _ in range(1000):
            losses.append(policy_learner.learn_batch(batch)["mlp_loss"])

        self.assertGreater(1e-2, losses[-1])
        # this is to ensure e2e run to get ucb score works
        policy_learner.get_scores(torch.randn(batch_size, feature_dim))
        scores = policy_learner.get_scores(
            subjective_state=batch.state,
            action_space=DiscreteActionSpace(batch.action.tolist()),
        )
        # shape should be batch_size, action_count
        self.assertEqual(scores.shape, (batch.state.shape[0], batch.action.shape[0]))

        # TEST ACT API
        action_space = DiscreteActionSpace(batch.action.tolist())
        # act on one state
        action = policy_learner.act(
            subjective_state=state[0], action_space=action_space
        )
        self.assertTrue(action in range(batch_size))  # return action index
        # act on a batch of states
        action = policy_learner.act(subjective_state=state, action_space=action_space)
        self.assertEqual(action.shape, batch.reward.shape)