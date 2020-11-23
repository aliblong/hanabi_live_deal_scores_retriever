__version__ = '0.1.0'

import argparse
import csv
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
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument(
        "--output_json_file_path",
        "-j",
    )
    output_group.add_argument(
        "--output_csv_file_path",
        "-c",
    )
    return parser.parse_args()


SEED_PREFIX = "hc-"


def main():
    dotenv.load_dotenv()
    args = parse_args()
    logging.basicConfig(level=args.verbosity)
    bot = Bot(os.getenv("hanabi_live_username"), os.getenv("hanabi_live_password"))
    teams_results = {}
    team_captains = {}
    seed_results = []
    base_seed_names = [f"{SEED_PREFIX}{args.date}-{idx + 1}" for idx in range(args.num_seeds)]
    for deal_idx, base_seed_name in enumerate(base_seed_names):
        seed_name = f"p{args.num_players}v{args.variant_id}s{base_seed_name}"
        results = bot.get_deal_scores(seed_name)
        if args.output_csv_file_path:
            # Veto all games where not every player is on their first attempt at the deal
            past_participants = set()
            # Results were previously in order of ascending game ID, i.e. game completion datetime.
            # Then, they were changed to be in order of _de_scending game ID.
            # Let's just try to rely on consistency of server behaviour as little as possible.
            for game_id, properties in sorted(results.items()):
                players = set(properties["players"])
                # if the intersection is an empty set, everyone is on their first attempt
                if not players.intersection(past_participants):
                    players_tuple = tuple(sorted(players))
                    if players_tuple not in teams_results:
                        teams_results[players_tuple] = [(None, None, None, None, None)] * args.num_seeds
                        team_captains[players_tuple] = properties["players"][0]
                    score = properties["score"]
                    turns = properties["turns"]
                    datetime_started = properties["datetime_started"]
                    datetime_ended = properties["datetime_ended"]
                    teams_results[players_tuple][deal_idx] = (
                        game_id, score, turns, datetime_started, datetime_ended)
                past_participants.update(players)
        else:
            seed_results.append({
                "base_seed_name": base_seed_name,
                "games": [
                    dict({"game_id": game_id}, **game_results)
                    for game_id, game_results in results.items()
                ],
            })

    if args.output_csv_file_path:
        with open(args.output_csv_file_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for team, games_results in teams_results.items():
                flattened_games_results = [
                    game_subresult
                    for game_result in games_results
                    for game_subresult in game_result[:3]
                ]
                team_captain = team_captains[team]
                team_with_captain_first = [team_captain] \
                    + [player for player in team if player != team_captain]
                writer.writerow(team_with_captain_first + flattened_games_results)
    else:
        output = {
            "num_players": args.num_players,
            "variant_id": args.variant_id,
            "end_date": args.date,
            "seeds_games": seed_results,
        }
        with open(args.output_json_file_path, 'w') as json_file:
            json_file.write(json.dumps(output))
