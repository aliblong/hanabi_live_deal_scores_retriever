# hanabi.live deal scores retriever

This tool is used to collect scores for competitions on [hanabi.live](https://hanabi.live).
It takes a set of sample game IDs, finds all game IDs and results relevant to our competition scoring (score & turns taken) of equivalent deals (i.e. same card order, variant, and number of players), filters out non-first attempts for every player, and prints the results by team to csv.

## Usage instructions

1. Install poetry: `curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python`.
2. `cp .env_template .env`, then fill out `.env` with the account you want to use.
3. `poetry install`
4. `poetry run main`
