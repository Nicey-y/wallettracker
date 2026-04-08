import os
from dotenv import load_dotenv

load_dotenv()  # reads the .env file and loads the variables into the environment

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_IDS = [
    int(os.getenv("GUILD_ID_1")),
    int(os.getenv("GUILD_ID_2")),
    int(os.getenv("GUILD_ID_3")),
]

