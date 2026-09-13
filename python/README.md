# IFC Python bot

This directory contains the Python rewrite scaffold for the IFC league bot.

Quick start:

1. Create a virtualenv and install dependencies

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2. Copy .env.template -> .env and fill DISCORD_TOKEN and other values.

3. Initialize the database (SQLite dev):

# uses SQLAlchemy + aiosqlite; for production set DATABASE_URL to a Postgres URL

4. Run the bot:

python -m ifc_bot.bot

5. Run the API:

uvicorn ifc_bot.api:app --reload --port 8000

Note: This is an initial scaffold with core commands (/createteam, /player, /offer). I will expand features in follow-up commits.
