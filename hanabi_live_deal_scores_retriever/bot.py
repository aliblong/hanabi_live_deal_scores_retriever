import logging
import json
from time import sleep

import requests
import websocket

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class Bot:
    def __init__(self, username, password):
        """TODO: Docstring for __init__.

        :function: TODO
        :returns: TODO

        """
        login_url = "https://hanabi.live/login"
        session = requests.Session()
        session.post(login_url, data={
            "username": username,
            "password": password,
            "version": "bot",
        })
        cookies = session.cookies.get_dict()
        self._conn = websocket.create_connection(
            'wss://hanabi.live/ws',
            header={"Cookie": f"hanabi.sid={cookies['hanabi.sid']}"},
        )

    GLOBAL_RATE_LIMIT_N_MESSAGES = 100
    GLOBAL_RATE_LIMIT_TIMEOUT_SECONDS = 2.0
    global_rate_limit_counter = 0

    def _send_msg(self, msg_type, msg_payload):
        self.global_rate_limit_counter += 1
        # fudge factor to ensure compliance
        if self.global_rate_limit_counter > self.GLOBAL_RATE_LIMIT_N_MESSAGES * 0.9:
            self.global_rate_limit_counter = 0
            sleep(self.GLOBAL_RATE_LIMIT_TIMEOUT_SECONDS * 1.1)
        self._conn.send(f"{msg_type} {json.dumps(msg_payload)}")

    def _recv_msg(self, msg_type):
        while True:
            msg = self._conn.recv()
            logger.debug(msg)
            if msg[:len(msg_type)] == msg_type:
                return json.loads(msg[len(msg_type) + 1:])

    def get_deal_scores(self, seed):
        logger.debug("Getting scores for deals like game %s", seed)
        self._send_msg("historyGetSeed", {"seed": seed})
        games = self._recv_msg("gameHistoryOtherScores")
        retval = {}

        for game in games['games']:
            # server doesn't allow commas in names
            players = game["playerNames"]
            game_id = game["id"]
            retval[game_id] = {}
            retval[game_id]["players"] = players
            self._send_msg("replayCreate", {
                "gameID": game_id,
                "source": "id",
                "visibility": "solo",
            })
            table = self._recv_msg("tableStart")
            self._send_msg("getGameInfo2", {"tableID": table["tableID"]})
            game_events = self._recv_msg("gameActionList")["list"]
            for event in reversed(game_events):
                event_type = event["type"]
                if event_type == "turn":
                    retval[game_id]["turn"] = event["num"]
                elif event_type == "status":
                    retval[game_id]["score"] = event["score"]
                    break
            self._send_msg("tableUnattend", {"tableID": table["tableID"]})
        return retval
# game_actions = json.loads(
#     requests.get(f"https://hanabi.live/export/{game_id}").content.decode("utf-8")
# )
# https://hanabi.live/deals/{seed_name}, select on game options,
# then https://hanabi.live/export/{game_id} will get you game actions, but the
# game state still needs to be reconstructed to determine things like score and turns taken
