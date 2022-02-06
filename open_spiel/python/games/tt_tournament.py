# Copyright 2019 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Lint as python3
"""Kuhn Poker implemented in Python.

This is a simple demonstration of implementing a game in Python, featuring
chance and imperfect information.

Python games are significantly slower than C++, but it may still be suitable
for prototyping or for small games.

It is possible to run C++ algorithms on Python implemented games, This is likely
to have good performance if the algorithm simply extracts a game tree and then
works with that. It is likely to be poor if the algorithm relies on processing
and updating states as it goes, e.g. MCTS.
"""

import enum

import numpy as np
from copy import deepcopy
import pyspiel
from open_spiel.python.games.tt_utils import *

_NUM_PLAYERS = 2
# per titan: pick, remove, 25 place. also pass
_NUM_ACTIONS_PER_TITAN = (1 + 1 + NUM_TILES)
_NUM_ACTIONS = NUM_TITANS*_NUM_ACTIONS_PER_TITAN + 1
_MAX_GAME_LENGTH = 30
# TODO: allow removals?
"""
r0: (8 titans) * 2 = 16
r1: (place 2) * 2 = 4
r2: (place 1) * 2 = 2
r3: (place 1) * 2 = 2
r4: (place 1) * 2 = 2
r5: (remove 1 place 1) * 2 = 4
"""
#harcoding special actions
PASS_ACTION = NUM_TITANS*_NUM_ACTIONS_PER_TITAN
_GAME_TYPE = pyspiel.GameType(
    short_name="ttt",
    long_name="Tiny Titans Tournament",
    dynamics=pyspiel.GameType.Dynamics.SEQUENTIAL,
    chance_mode=pyspiel.GameType.ChanceMode.DETERMINISTIC,
    information=pyspiel.GameType.Information.IMPERFECT_INFORMATION,
    utility=pyspiel.GameType.Utility.ZERO_SUM,
    reward_model=pyspiel.GameType.RewardModel.TERMINAL,
    max_num_players=_NUM_PLAYERS,
    min_num_players=_NUM_PLAYERS,
    provides_information_state_string=True,
    provides_information_state_tensor=True,
    provides_observation_string=True,
    provides_observation_tensor=True,
    provides_factored_observation_string=True)
_GAME_INFO = pyspiel.GameInfo(
    num_distinct_actions=_NUM_ACTIONS,
    max_chance_outcomes=0,
    num_players=_NUM_PLAYERS,
    min_utility=-1.03,
    max_utility=1.03,
    utility_sum=0.0,
    max_game_length=_MAX_GAME_LENGTH)


class TTTGame(pyspiel.Game):
  """A Python version of Tiny Titans."""

  def __init__(self, params=None):
    super().__init__(_GAME_TYPE, _GAME_INFO, params or dict())

  def new_initial_state(self):
    """Returns a state corresponding to the start of a game."""
    return TTTState(self)

  def make_py_observer(self, iig_obs_type=None, params=None):
    """Returns an object used for observing game state."""
    return TTTObserver(
        iig_obs_type or pyspiel.IIGObservationType(perfect_recall=False),
        params)

class Titans:
  def __init__(self):
    self.titans = {}

  def __str__(self):
    return "\n".join([str(self.titans[t]) for t in sorted(self.titans.keys())])

  def num_titans(self):
    return len(self.titans)

  def pick_titan(self, titan_index):
    self.titans[titan_index] = TitanInfo(titan_index)

  def place_titan(self, titan_index, tile_index):
    self.titans[titan_index].tile_index = tile_index

  def unplace_titan(self, titan_index):
    self.titans[titan_index].tile_index = -1

  def picked_titans(self):
    return list(t for t in self.titans.keys())

  def unpicked_titans(self):
    picked = self.picked_titans()
    return [t for t in range(NUM_TITANS) if t not in picked]

  def placed_titans(self):
    return [t.index for t in self.titans.values() if t.tile_index != -1]

  def unplaced_titans(self):
    return [t.index for t in self.titans.values() if t.tile_index == -1]

  def used_tiles(self):
    return [t.tile_index for t in self.titans.values()]

  def unused_tiles(self):
    used = self.used_tiles()
    return [t for t in range(NUM_TILES) if t not in used]


class TTTState(pyspiel.State):
  """A python version of the tt state."""

  def __init__(self, game):
    """Constructor; should only be called by Game.new_initial_state."""
    super().__init__(game)
    self.titans_prev = [Titans(), Titans()]
    self.titans = [Titans(), Titans()]
    self.round = 0
    self.score = [0, 0]
    self.actions = []
    self._next_player = 0
    self._game_over = False

  def _cur_max_placed_titans(self):
    if self.round == 0:
      return 0
    return min(self.round+1, MAX_TITANS)
  # OpenSpiel (PySpiel) API functions are below. This is the standard set that
  # should be implemented by every sequential-move game with chance.

  def current_player(self):
    """Returns id of the next player to move, or TERMINAL if game is over."""
    if self._game_over:
      return pyspiel.PlayerId.TERMINAL
    else:
      return self._next_player

  def _legal_actions(self, player):
    # per titan: pick, remove, 25 place
    ret = []
    my_titans = self.titans[player]

    if self.round == 0: # picking phase
      unpicked_titans = my_titans.unpicked_titans()
      for titan_index in unpicked_titans:
        ret.append(titan_index*_NUM_ACTIONS_PER_TITAN)
    elif len(my_titans.placed_titans()) < self._cur_max_placed_titans():
      unplaced_titans = my_titans.unplaced_titans()
      unused_tiles = my_titans.unused_tiles()
      for titan_index in unplaced_titans:
        for tile_index in unused_tiles:
          ret.append(titan_index*_NUM_ACTIONS_PER_TITAN+2+tile_index)
    if self.round == 5: # can remove on 5
      placed_titans = my_titans.placed_titans()
      for titan_index in placed_titans:
        ret.append(titan_index*_NUM_ACTIONS_PER_TITAN+1) # remove
      ret.append(PASS_ACTION) # pass

    return ret


  def chance_outcomes(self):
    """Returns the possible chance outcomes and their probabilities."""
    assert self.is_chance_node()
    assert False, "not implemented"
    return 0


  def _apply_action(self, action):
    """Applies the specified action to the state."""
    if self.is_chance_node():
      assert False, "Not Implemented"
      return
    else:
      self.actions.append(action)
    self.titans_prev = deepcopy(self.titans)
    my_titans = self.titans[self._next_player]
    if action != PASS_ACTION:
      titan_index = action // _NUM_ACTIONS_PER_TITAN
      action_type = action % _NUM_ACTIONS_PER_TITAN
      if action_type == 0: # pick
        assert self.round == 0
        my_titans.pick_titan(titan_index)
      elif action_type == 1:
        my_titans.unplace_titan(titan_index)
      else:
        my_titans.place_titan(titan_index, action_type-2)

    if self.round == 0:
      if my_titans.num_titans() == 8 and self._next_player == 1:
        self.round += 1
      self._next_player = 1-self._next_player
      return

    # not enough placed titans
    if len(my_titans.placed_titans()) < self._cur_max_placed_titans():
      return

    # p1 hasnt gone
    if self._next_player == 0:
      self._next_player = 1
      return

    # both done, play a game
    is_p0_win = check_server_win_tournament(self.titans)
    if is_p0_win:
      self.score[0] += 1
    else:
      self.score[1] += 1

    # if a round ended
    if self.score[0] != 3 and self.score[1] != 3:
      self.round += 1
      self._next_player = 0
      return

    # if is complete
    self._game_over = True

  def _action_to_string(self, player, action):

    if action == PASS_ACTION:
      cmd = "PASS"
    else:
      titan_index = action // _NUM_ACTIONS_PER_TITAN
      action_type = action % _NUM_ACTIONS_PER_TITAN
      if action_type == 0:
        act_str = "PICK"
      elif action_type == 1:
        act_str = "REMOVE"
      else:
        act_str = f"TILE({index_to_tile(action_type-2)})"
      cmd = f"{index_to_titan_name(titan_index)}({TITAN_IDS[titan_index]})-{act_str}"
    return f"[p{player}-{cmd}]"

  def is_terminal(self):
    """Returns True if the game is over."""
    return self._game_over

  def returns(self):
    """Total reward for each player over the course of the game so far."""
    if all([s != 3 for s in self.score]): # only terminal for az
      return [0, 0]

    points_0 = self.score[0]//3 + self.score[0]*0.01
    points_1 = self.score[1]//3 + self.score[1]*0.01
    return [points_0-points_1, points_1-points_0]

  def __str__(self):
    """String for debug purposes. No particular semantics are required."""
    """Observation of `state` from the PoV of `player`, as a string."""
    ret = []
    ret.append(f"Round {self.round}")
    ret.append(f"Score {self.score}")
    ret.append(f"p0 \n{self.titans[0]}")
    ret.append(f"p1 \n{self.titans[1]}")

    return "\n".join(ret)


class TTTObserver:
  """Observer, conforming to the PyObserver interface (see observation.py)."""

  def __init__(self, iig_obs_type, params):
    """Initializes an empty observation tensor."""
    if params:
      raise ValueError(f"Observation parameters not supported; passed {params}")

  def set_from(self, state: TTTState, player):
    """Updates `tensor` and `dict` to reflect `state` from PoV of `player`."""

  def string_from(self, state: TTTState, player):
    """Observation of `state` from the PoV of `player`, as a string."""

# Register the game with the OpenSpiel library

pyspiel.register_game(_GAME_TYPE, TTTGame)
