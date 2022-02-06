import sys
import time

import numpy as np
import requests
import json
from typing import List
from functools import lru_cache
from dataclasses import dataclass
import random
import threading
import os
from flufl.lock import Lock

def index_to_titan_name(titan_index):
  return TITAN_ID_TO_NAME[TITAN_IDS[titan_index]]

def index_to_tile(tile_index):
  return tile_index+1

# 22
TITAN_IDS = [0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 21, 23, 24, 26, 30, 31, 32, 33, 34, 35, 37, 38]
TITAN_ID_TO_NAME = {
  0: "Haldor",
  4: "Martello",
  5: "Pako",
  6: "Brown Beard",
  7: "Akiro",
  8: "Eldin",
  9: "Rozan",
  10: "Demetra",
  11: "Layla",
  12: "Masilda",
  13: "Eira",
  16: "Velena",
  17: "Colt",
  18: "Hanako",
  19: "Tonrok",
  21: "Sha'kiva",
  #22: "Ornata",
  23: "Safiri",
  24: "Saito",
  26: "Freya",
  30: "Gilgamesh",
  31: "Vasilios",
  32: "Soha",
  33: "Marie",
  34: "Khasmas",
  35: "Silvus",
  37: "Samson",
  38: "Elai",
}
_timeouts = 0
_wins = 0
_losses = 0
_started = 0
_finished = 0
_port = None
NUM_TITANS = len(TITAN_IDS)
NUM_TILES = 25
MAX_TITANS = 5
PLACEMENT_TEMPLATE = """[{"placement_id":1231,"pos_1":%s,"char_1":{"char_id":6000,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":1,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_2":%s,"char_2":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_3":%s,"char_3":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_4":%s,"char_4":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_5":%s,"char_5":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false}},{"placement_id":1233,"pos_1":%s,"char_1":{"char_id":6015,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_2":%s,"char_2":{"char_id":6010,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":2,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_3":%s,"char_3":{"char_id":6009,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":1,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_4":%s,"char_4":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_5":%s,"char_5":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false}}]"""

@dataclass
class TitanInfo:
  index: int
  tile_index: int = -1
  prestige: int = 0
  def __str__(self):
    return f"{index_to_titan_name(self.index)}({TITAN_IDS[self.index]})\t{index_to_tile(self.tile_index)}"

def _get_port():
  return "1233"
  global _port
  if _port:
    return _port

  filename = "./ports.txt"
  lock = Lock(filename+"lock")
  with lock:
    with open(filename, "r") as f:
      lines = f.readlines()
    _port = lines[0].strip("\n")
    with open(filename, "w") as f:
      for line in lines[1:]:
        f.write(line)

  return _port

def create_placement_str(titan_indexes, tile_indexes):
    formatData = []

    for player in range(2):
      for titan_index, tile_index in zip(titan_indexes[player], tile_indexes[player]):
        # tile, char id, level, prestige
        formatData.extend([tile_index+1, TITAN_IDS[titan_index], 240, -1])
      # pad to 5
      for _ in range(MAX_TITANS-len(titan_indexes[player])):
        formatData.extend([0, -1, 0, -1])
    return PLACEMENT_TEMPLATE % tuple(formatData)

def check_server_win_tournament(titans):
  titan_indexes = [[],[]]
  tile_indexes = [[],[]]
  for p in range(2):
    for t in sorted(titans[p].titans.values(), key=lambda cur_t: cur_t.index):
      if t.tile_index == -1:
        continue
      titan_indexes[p].append(t.index)
      tile_indexes[p].append(t.tile_index)
  print(titan_indexes)
  print(tile_indexes)
  return check_server_win(titan_indexes, tile_indexes)

def check_server_win(titan_indexes, tile_indexes):
  global _wins
  global _losses
  global _started
  global _finished
  if _started == 0:
    print(f"{os.getpid()} starting\n\n")
  _started += 1
  #print(f"{os.getpid()}: {_started}")
  is_win = check_server_win_cached(create_placement_str(titan_indexes, tile_indexes))
  _finished += 1
  if is_win:
    _wins += 1
  else:
    _losses += 1
  print(f"\n\nWins: {_wins} Losses: {_losses}\n\n")
  return is_win

def check_server_win_cached(placementJsonStr):
  global _timeouts
  global _started
  global _port
  while True:
    try:
      #{int((random.random()*1000))}
      time.sleep(random.random()/100)
      response = requests.get(f"http://127.0.0.1:{_get_port()}/simulate/1337/", data=placementJsonStr, timeout=15)
      if response.status_code == 200:
        break
      else:
        print(f"response code {response.status_code}")
    except KeyboardInterrupt:
      print("exiting")
      sys.exit()
    except BaseException as err:
      print(f"Unexpected {err}, {type(err)}, id {os.getpid()} num {_started}")# {placementJsonStr}")
      _timeouts += 1
  assert response.status_code == 200
  return response.content == b"True"
