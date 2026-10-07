"""Replay learning and reinforcement learning for the IAmAVirus Fog of War bot.

The package is organised as a pipeline (see README.md in this directory):

    api_client -> ingest -> histories -> dataset -> pretrain -> export
                                            \\-> env/rollouts -> train_ppo

Rules come from the C++ engine through `rules`, so there is one implementation
of movement, observation and termination, the one checked against referee.py.
"""
