__version__ = '0.1.0'

import argparse
import csv
import logging
import os
# logger = logging.getLogger(__name__)

import dotenv

from .bot import Bot


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample_game_ids",
        "-g",
        required=True,
        type=int,
        nargs='+',
        help="For each deal, an ID of any game of that deal",
    )
    parser.add_argument(
        "--output_csv_file_path",
        "-o",
        default="hanabi_competition_results.csv",
        required=False,
        help="https://docs.python.org/3.8/library/logging.html#logging-levels",
    )
    parser.add_argument(
        "--verbosity",
        "-v",
        default="WARNING",
        required=False,
        help="https://docs.python.org/3.8/library/logging.html#logging-levels",
    )
    return parser.parse_args()


def main():
    dotenv.load_dotenv()
    args = parse_args()
    logging.basicConfig(level=args.verbosity)
    bot = Bot(os.getenv("hanabi_live_username"), os.getenv("hanabi_live_password"))
    game_results = {}
    team_captains = {}
    for deal_idx, sample_game_id in enumerate(args.sample_game_ids):
        results = bot.get_deal_scores(sample_game_id)
        # Veto all games where not every player is on their first attempt at the deal
        past_participants = set()
        # Results are assumed to be in order of ascending game ID, i.e. game completion datetime.
        for game_id, properties in results.items():
            players = set(properties["players"])
            # if the intersection is an empty set, everyone is on their first attempt
            if not players.intersection(past_participants):
                players_tuple = tuple(sorted(players))
                if players_tuple not in game_results:
                    game_results[players_tuple] = [(None, None, None)] * len(args.sample_game_ids)
                    team_captains[players_tuple] = properties["players"][0]
                score = properties["score"]
                turn = properties["turn"]
                game_results[players_tuple][deal_idx] = (game_id, score, turn)
            past_participants.update(players)

    with open(args.output_csv_file_path, 'w') as csv_file:
        writer = csv.writer(csv_file)
        for team, games_results in game_results.items():
            flattened_games_results = [
                game_subresult
                for game_result in games_results
                for game_subresult in game_result
            ]
            team_captain = team_captains[team]
            team_with_captain_first = [team_captain] \
                + [player for player in team if player != team_captain]
            writer.writerow(team_with_captain_first + flattened_games_results)
