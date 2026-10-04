import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

TOKEN = os.getenv("DISCORD_TOKEN")
# GUILD_IDS = [
#     int(os.getenv("GUILD_ID_1")),
#     int(os.getenv("GUILD_ID_2")),
#     int(os.getenv("GUILD_ID_3")),
# ]
# print(f"Token length: {len(TOKEN)}")
# print(f"Token: {TOKEN}")