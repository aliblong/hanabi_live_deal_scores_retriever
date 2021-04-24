__version__ = '0.1.0'

import argparse
from collections import deque
import json
import logging
# import os
import subprocess
from time import sleep

import dotenv
import websocket


from .bot import Bot


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbosity",
        default="WARNING",
        required=False,
        help="https://docs.python.org/3.8/library/logging.html#logging-levels",
    )

    parser.add_argument(
        "--env_file",
        default=".env",
        help="https://docs.python.org/3.8/library/logging.html#logging-levels",
    )

    subparsers = parser.add_subparsers(dest='game_type')
    comp_parser = subparsers.add_parser('comp')
    novar_parser = subparsers.add_parser('novar')

    comp_parser.add_argument(
        "--date",
        "-d",
        required=True,
        help="Date in ISO format, e.g. '2020-06-01'",
    )
    comp_parser.add_argument(
        "--num_players",
        "-p",
        type=int,
        required=True,
        help="Number of players, e.g. 2",
    )
    comp_parser.add_argument(
        "--num_seeds",
        "-s",
        type=int,
        required=True,
        help="Number of seeds in the competition, e.g. 4",
    )
    comp_parser.add_argument(
        "--variant_id",
        "-v",
        type=int,
        required=True,
        help="ID of the variant, according to hanabi.live, e.g. 106, for Pink(6 suits)",
    )
    comp_parser.add_argument(
        "--output_json_file_path",
        "-j",
    )

    novar_subparsers = novar_parser.add_subparsers(dest='bot_op_type')
    novar_subparsers.add_parser('batch')
    novar_subparsers.add_parser('stream')

    return parser.parse_args()


SEED_PREFIX = {
    "comp": "hc-",
    "novar": "NoVarathon-",
}


def main():
    args = parse_args()
    secrets = dotenv.dotenv_values(args.env_file)
    logging.basicConfig(level=args.verbosity)

    logger = logging.getLogger(__name__)
    hc_username = secrets.get("hanabi_competitions_username")
    hc_password = secrets.get("hanabi_competitions_password")

    if args.game_type == "comp":
        bot = Bot(secrets.get("hanabi_live_username"), secrets.get("hanabi_live_password"))
        seed_results = []
        # Seed names are 1-indexed
        for seed_idx in range(1, args.num_seeds + 1):
            base_seed_name = f"{SEED_PREFIX['comp']}{args.date}-{seed_idx}"
            seed_name = f"p{args.num_players}v{args.variant_id}s{base_seed_name}"
            results = bot.get_deal_scores(seed_name)

            seed_results.append({
                "base_seed_name": base_seed_name,
                "games": [
                    dict({"game_id": game_id}, **game_results)
                    for game_id, game_results in results.items()
                ],
            })

        output = {
            "num_players": args.num_players,
            "variant_id": args.variant_id,
            "end_date": args.date,
            "seeds_games": seed_results,
        }
        upload_game(hc_username, hc_password, output)

    elif args.bot_op_type == "stream":
        game_queue = deque()
        while True:
            try:
                bot = Bot(secrets.get("hanabi_live_username"), secrets.get("hanabi_live_password"))
                while True:
                    if game_queue:
                        game_id = game_queue[0]
                        result = bot.get_game_result(game_id)
                        upload_game(hc_username, hc_password, result)
                        game_queue.pop_left()
                    else:
                        while True:



            except websocket.WebSocketException:
                logger.error("Websocket connection closed")
                sleep(5)


def upload_game(username, password, json_data):
    subprocess.check_call(
        ' '.join([
            f'curl -u "{username}:{password}"',
            '-H "Content-Type: application/json"',
            'https://hanabi-competitions.com/games',
            f"--data '{json.dumps(json_data)}'",
        ]),
        shell=True,
    )
