import os
from dotenv import load_dotenv
from src.bot import violet

load_dotenv()

if __name__ == "__main__":
    bot = violet()
    bot.run(os.getenv("TOKEN"))