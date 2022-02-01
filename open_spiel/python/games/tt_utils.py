import sys
import numpy as np
import requests
import json
from functools import lru_cache
import random
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
NUM_TILES = 25
MAX_TITANS = 5
PLACEMENT_TEMPLATE = """[{"placement_id":1231,"pos_1":%s,"char_1":{"char_id":6000,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":1,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_2":%s,"char_2":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_3":%s,"char_3":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_4":%s,"char_4":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_5":%s,"char_5":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false}},{"placement_id":1233,"pos_1":%s,"char_1":{"char_id":6015,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_2":%s,"char_2":{"char_id":6010,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":2,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_3":%s,"char_3":{"char_id":6009,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":1,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_4":%s,"char_4":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false},"pos_5":%s,"char_5":{"char_id":0,"user":0,"char_type":%s,"level":%s,"prestige":%s,"copies":0,"hat":{"item_id":0,"user":0,"item_type":0,"exp":0},"armor":{"item_id":0,"user":0,"item_type":0,"exp":0},"weapon":{"item_id":0,"user":0,"item_type":0,"exp":0},"boots":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_1":{"item_id":0,"user":0,"item_type":0,"exp":0},"trinket_2":{"item_id":0,"user":0,"item_type":0,"exp":0},"is_tourney":false}}]"""
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

def check_server_win(titan_indexes, tile_indexes):
  global _wins
  global _losses
  is_win = check_server_win_cached(create_placement_str(titan_indexes, tile_indexes))
  if is_win:
    _wins += 1
  else:
    _losses += 1
  #print(f"\n\nWins: {_wins} Losses: {_losses}\n\n")
  return is_win

def check_server_win_cached(placementJsonStr):
  global _timeouts
  while True:
    try:
      #{int((random.random()*1000))}
      response = requests.get(f"http://192.168.3.112:8007/simulate/1337/", data=placementJsonStr, timeout=3)
      if response.status_code == 200:
        break
      else:
        print(f"response code {response.status_code}")
    except KeyboardInterrupt:
      print("exiting")
      sys.exit()
    except:
      print(f"timed out {_timeouts}")# {placementJsonStr}")
      _timeouts += 1
  assert response.status_code == 200
  return response.content == b"True"
