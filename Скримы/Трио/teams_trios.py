import disnake
from disnake.ext import commands
import json
import os

class ScrimTeams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/trios_reg.json"

    @commands.slash_command(name="teams_trios", description="Показать список зарегистрированных команд")
    async def scrim_teams_trios(self, inter: disnake.ApplicationCommandInteraction):
        if not os.path.exists(self.data_file):
            embed = disnake.Embed(
                title="Ошибка",
                description="Файл с данными о командах не найден!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352422198534602792/standard_13.gif?ex=67ddf4d2&is=67dca352&hm=78cc04b7affe681565f1f7effbdc4a73224df318209d5b578357ecc0f10781de&=&width=1424&height=82")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            embed = disnake.Embed(
                title="Список команд",
                description="Зарегистрированных команд пока нет.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352422198534602792/standard_13.gif?ex=67ddf4d2&is=67dca352&hm=78cc04b7affe681565f1f7effbdc4a73224df318209d5b578357ecc0f10781de&=&width=1424&height=82")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        first_lobby = data[:20]
        second_lobby = data[20:]
        if first_lobby:
            first_lobby_list = "\n".join(
                [f"* **{team['team_name']}** ( {idx + 1} Команда )" for idx, team in enumerate(first_lobby)]
            )
            embed1 = disnake.Embed(
                title="Список зарегистрированных команд",
                description=f"**Первое лобби**\n{first_lobby_list}",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed1.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352422198534602792/standard_13.gif?ex=67ddf4d2&is=67dca352&hm=78cc04b7affe681565f1f7effbdc4a73224df318209d5b578357ecc0f10781de&=&width=1424&height=82")
            await inter.response.send_message(embed=embed1, ephemeral=True)
        if second_lobby:
            second_lobby_list = "\n".join(
                [f"* **{team['team_name']}** ( {idx + 21} Команда )" for idx, team in enumerate(second_lobby)]
            )
            embed2 = disnake.Embed(
                title="Список зарегистрированных команд",
                description=f"**Второе лобби**\n{second_lobby_list}",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed2.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352422198534602792/standard_13.gif?ex=67ddf4d2&is=67dca352&hm=78cc04b7affe681565f1f7effbdc4a73224df318209d5b578357ecc0f10781de&=&width=1424&height=82")
            await inter.followup.send(embed=embed2, ephemeral=True)

def setup(bot):
    bot.add_cog(ScrimTeams(bot))