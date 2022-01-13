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

import pyspiel
from open_spiel.python.games.tt_utils import *

_NUM_PLAYERS = 2
_NUM_ACTIONS = (len(TITAN_IDS) + NUM_TILES)*MAX_TITANS
_GAME_TYPE = pyspiel.GameType(
    short_name="tt",
    long_name="Tiny Titans",
    dynamics=pyspiel.GameType.Dynamics.SEQUENTIAL,
    chance_mode=pyspiel.GameType.ChanceMode.DETERMINISTIC,
    information=pyspiel.GameType.Information.IMPERFECT_INFORMATION,
    utility=pyspiel.GameType.Utility.GENERAL_SUM,
    reward_model=pyspiel.GameType.RewardModel.REWARDS,
    max_num_players=_NUM_PLAYERS,
    min_num_players=_NUM_PLAYERS,
    provides_information_state_string=True,
    provides_information_state_tensor=True,
    provides_observation_string=True,
    provides_observation_tensor=True,
    provides_factored_observation_string=True)
_GAME_INFO = pyspiel.GameInfo(
    num_distinct_actions=_NUM_ACTIONS,
    #max_chance_outcomes=len(_DECK),
    num_players=_NUM_PLAYERS,
    min_utility=-1.03,
    max_utility=1.03,
    utility_sum=0.0,
    max_game_length=54)


class TTGame(pyspiel.Game):
  """A Python version of Tiny Titans."""

  def __init__(self, params=None):
    super().__init__(_GAME_TYPE, _GAME_INFO, params or dict())

  def new_initial_state(self):
    """Returns a state corresponding to the start of a game."""
    return TTState(self)

  def make_py_observer(self, iig_obs_type=None, params=None):
    """Returns an object used for observing game state."""
    return TTObserver(
        iig_obs_type or pyspiel.IIGObservationType(perfect_recall=False),
        params)


class TTState(pyspiel.State):
  """A python version of the tt state."""

  def __init__(self, game):
    """Constructor; should only be called by Game.new_initial_state."""
    super().__init__(game)
    self.score = [0, 0]
    # 0 is titan, 1 is pos
    self.titans = [[], []]
    self.tiles = [[], []]
    self._round = 0 # represents the group of turns that leads into a battle
    self._next_player = 0
    self._game_over = False

  def _cur_max_titans(self):
    return min(self._round+3, MAX_TITANS)
  # OpenSpiel (PySpiel) API functions are below. This is the standard set that
  # should be implemented by every sequential-move game with chance.

  def current_player(self):
    """Returns id of the next player to move, or TERMINAL if game is over."""
    if self._game_over:
      return pyspiel.PlayerId.TERMINAL
    else:
      return self._next_player

  def _legal_actions(self, player):
    """Returns a list of legal actions, sorted in ascending order."""
    assert player >= 0
    ret = []

    my_titans = self.titans[player]
    my_tiles = self.tiles[player]
    used_titans = set(my_titans)
    used_tiles = set(my_tiles)

    if len(my_titans) < self._cur_max_titan_index():
      base_index = len(my_titans)*len(TITAN_IDS)
      for titan_index in range(len(TITAN_IDS)):
        if titan_index not in used_titans:
          ret.append((base_index+titan_index))
      return ret
    else: # tile index
      base_index = MAX_TITANS*len(TITAN_IDS) + len(my_tiles)*NUM_TILES
      for tile_index in range(NUM_TILES):
        if tile_index not in used_tiles:
          ret.append((base_index+tile_index))
      return ret



  def chance_outcomes(self):
    assert False, "not implemented"
    """Returns the possible chance outcomes and their probabilities."""
    assert self.is_chance_node()
    return 0

  def _apply_action(self, action):
    """Applies the specified action to the state."""
    if self.is_chance_node():
      assert False, "Not Implemented"
      return
    my_titans = self.titans[self._next_player]
    my_tiles = self.tiles[self._next_player]
    base_tile_index = MAX_TITANS*len(TITAN_IDS)

    if action < base_tile_index: # create titan
      assert len(my_titans) < self._cur_max_titans()
      titan_slot = action//len(TITAN_IDS)
      assert titan_slot == len(my_titans)
      my_titans.append(action % len(TITAN_IDS))
    else:  # set tile
      assert len(my_tiles) < len(my_titans)
      tile_slot = (action-base_tile_index)//NUM_TILES
      assert tile_slot == len(my_tiles)
      my_tiles.append((action-base_tile_index) % NUM_TILES)

    # self round placement still incomplete
    if len(my_titans) < self._cur_max_titans() or len(my_tiles) < len(my_titans):
      return

    # player 0 done, player 1 turn
    if self._next_player == 0:
      self._next_player = 1
      return

    # both done, play a game
    is_p0_win = check_server_win(self.titans, self.tiles)
    if is_p0_win:
      self.score[0] += 1
    else:
      self.score[1] += 1

    # if a round ended
    if self.score[0] != 3 and self.score[1] != 3:
      self._round += 1
      self._next_player = 0
      self.tiles = [[], []]
      return

    # if is complete
    self._game_over = True


  def _action_to_string(self, player, action):
    """Action -> string."""
    return f"{player}: {action}"

  def is_terminal(self):
    """Returns True if the game is over."""
    return self._game_over

  def returns(self):
    """Total reward for each player over the course of the game so far."""
    return [self.score[0]//3 + self.score[0]*0.01, self.score[1]//3 + self.score[1]*0.01]

  def __str__(self):
    """String for debug purposes. No particular semantics are required."""
    return "TODO debug str"


class TTObserver:
  """Observer, conforming to the PyObserver interface (see observation.py)."""

  def __init__(self, iig_obs_type, params):
    """Initializes an empty observation tensor."""
    if params:
      raise ValueError(f"Observation parameters not supported; passed {params}")

    # Determine which observation pieces we want to include.
    pieces = [("player", 2, (2,))]
    if iig_obs_type.private_info == pyspiel.PrivateInfoType.SINGLE_PLAYER:
      pieces.append(("private_card", 3, (3,)))
    if iig_obs_type.public_info:
      if iig_obs_type.perfect_recall:
        pieces.append(("betting", 6, (3, 2)))
      else:
        pieces.append(("pot_contribution", 2, (2,)))

    # Build the single flat tensor.
    total_size = sum(size for name, size, shape in pieces)
    self.tensor = np.zeros(total_size, np.float32)

    # Build the named & reshaped views of the bits of the flat tensor.
    self.dict = {}
    index = 0
    for name, size, shape in pieces:
      self.dict[name] = self.tensor[index:index + size].reshape(shape)
      index += size

  def set_from(self, state, player):
    """Updates `tensor` and `dict` to reflect `state` from PoV of `player`."""
    self.tensor.fill(0)
    if "player" in self.dict:
      self.dict["player"][player] = 1
    if "private_card" in self.dict and len(state.cards) > player:
      self.dict["private_card"][state.cards[player]] = 1
    if "pot_contribution" in self.dict:
      self.dict["pot_contribution"][:] = state.pot
    if "betting" in self.dict:
      for turn, action in enumerate(state.bets):
        self.dict["betting"][turn, action] = 1

  def string_from(self, state, player):
    """Observation of `state` from the PoV of `player`, as a string."""
    pieces = []
    if "player" in self.dict:
      pieces.append(f"p{player}")
    if "private_card" in self.dict and len(state.cards) > player:
      pieces.append(f"card:{state.cards[player]}")
    if "pot_contribution" in self.dict:
      pieces.append(f"pot[{int(state.pot[0])} {int(state.pot[1])}]")
    if "betting" in self.dict and state.bets:
      pieces.append("".join("pb"[b] for b in state.bets))
    return " ".join(str(p) for p in pieces)


# Register the game with the OpenSpiel library

pyspiel.register_game(_GAME_TYPE, TTGame)
