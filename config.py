import os
from dotenv import load_dotenv

load_dotenv()  # reads the .env file and loads the variables into the environment

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))  # discord.py needs this as an integer