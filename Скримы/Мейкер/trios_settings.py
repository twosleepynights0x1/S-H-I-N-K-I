import json
from pathlib import Path
import disnake
from disnake.ext import commands

JSON_PATH = Path("data/trios_allow.json")

def load_json():
    if JSON_PATH.exists():
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(data):
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class allowtrios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="maker_allow_reg", description="Разрешить или запретить регистрацию")
    async def maker_allow_reg(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: bool = commands.Param(description="Выберите True (разрешить) или False (запретить)")
    ):

        data = load_json()
        data['allow_registration'] = option
        save_json(data)
        await inter.response.send_message(f"Регистрация {'разрешена' if option else 'запрещена'}.")

def setup(bot):
    bot.add_cog(allowtrios(bot))