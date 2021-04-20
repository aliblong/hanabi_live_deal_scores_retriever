__version__ = '0.1.0'

import argparse
import json
import logging
import os
# logger = logging.getLogger(__name__)

import dotenv

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
        "--date",
        "-d",
        required=True,
        help="Date in ISO format, e.g. '2020-06-01'",
    )
    parser.add_argument(
        "--num_players",
        "-p",
        type=int,
        required=True,
        help="Number of players, e.g. 2",
    )
    parser.add_argument(
        "--num_seeds",
        "-s",
        type=int,
        required=True,
        help="Number of seeds in the competition, e.g. 4",
    )
    parser.add_argument(
        "--variant_id",
        "-v",
        type=int,
        required=True,
        help="ID of the variant, according to hanabi.live, e.g. 106, for Pink(6 suits)",
    )
    parser.add_argument(
        "--output_json_file_path",
        "-j",
    )
    return parser.parse_args()


SEED_PREFIX = "hc-"


def main():
    dotenv.load_dotenv()
    args = parse_args()
    logging.basicConfig(level=args.verbosity)
    bot = Bot(os.getenv("hanabi_live_username"), os.getenv("hanabi_live_password"))
    seed_results = []
    # Seed names are 1-indexed
    for seed_idx in range(1, args.num_seeds + 1):
        base_seed_name = f"{SEED_PREFIX}{args.date}-{seed_idx}"
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
    with open(args.output_json_file_path, 'w') as json_file:
        json_file.write(json.dumps(output))
