import sys
import numpy as np
import requests
import json

TITAN_IDS = [0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 21, 22, 23, 24, 26, 30, 31, 32, 33, 34, 35, 37, 38]
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
  22: "Ornata",
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
NUM_TILES = 25
MAX_TITANS = 5

def check_server_win(self, titan_indexes, tile_indexes):
  print("TODO")
  placementJsonStr = self._createPlacementJsonStr(board)
  while True:
    try:
      response = requests.get("http://192.168.0.24:8007/simulate/1337/", data=placementJsonStr, timeout=10)
      if response.status_code == 200:
        break
      else:
        print(f"response code {response.status_code}")
    except KeyboardInterrupt:
      print("exiting")
      sys.exit()
    except:
      print("timed out")

  assert response.status_code == 200
  return response.content == b"True"
