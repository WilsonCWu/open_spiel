import sys
import numpy as np
import requests
import json

VALID_CHARS = [0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 21, 22, 23, 24, 26, 30, 31, 32, 33, 34, 35, 37, 38]


def check_server_win(self, board):
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
