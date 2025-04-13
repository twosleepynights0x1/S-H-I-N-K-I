import disnake
from disnake.ext import commands
import json
import os

class MakerScrimTeams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/trios_reg.json"
        CONFIG_PATH = os.path.join('conf', 'config.json')
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")
        self.event_maker_role_id = config["scrims"]["EventMakerRole"]

    @commands.slash_command(name="maker_scrim_teams_trios", description="Показать список зарегистрированных команд (только для ивент-мейкеров)")
    async def maker_scrim_teams_trios(self, inter: disnake.ApplicationCommandInteraction):
        if not any(
            role.id == self.event_maker_role_id or role.permissions.administrator
            for role in inter.author.roles
        ):
            embed = disnake.Embed(
                title="Ошибка",
                description="У вас нет прав для использования этой команды!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        if not os.path.exists(self.data_file):
            embed = disnake.Embed(
                title="Ошибка",
                description="Файл с данными о командах не найден!",
                color=disnake.Color.red()
            )
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
            await inter.response.send_message(embed=embed)
            return
        teams_list = []
        for team in data:
            captain = inter.guild.get_member(team["captain_id"])
            teammate1 = inter.guild.get_member(team["teammates"]["teammate1"])
            teammate2 = inter.guild.get_member(team["teammates"]["teammate2"])
            team_info = (
                f"* > **{team['team_name']}**\n"
                f"* > {captain.mention} ({captain})\n"
                f"* > {teammate1.mention} ({teammate1})\n"
                f"* > {teammate2.mention} ({teammate2})\n"
            )
            teams_list.append(team_info)
        first_lobby = teams_list[:20]
        second_lobby = teams_list[20:]
        if first_lobby:
            first_lobby_info = "\n".join(first_lobby)
            embed1 = disnake.Embed(
                title="Список зарегистрированных команд",
                description=f"**Первое лобби**\n\n{first_lobby_info}",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed1.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352422198534602792/standard_13.gif?ex=67ddf4d2&is=67dca352&hm=78cc04b7affe681565f1f7effbdc4a73224df318209d5b578357ecc0f10781de&=&width=1424&height=82")
            await inter.response.send_message(embed=embed1)
        if second_lobby:
            second_lobby_info = "\n".join(second_lobby)
            embed2 = disnake.Embed(
                title="Список зарегистрированных команд",
                description=f"**Второе лобби**\n{second_lobby_info}",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed2.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352422198534602792/standard_13.gif?ex=67ddf4d2&is=67dca352&hm=78cc04b7affe681565f1f7effbdc4a73224df318209d5b578357ecc0f10781de&=&width=1424&height=82")
            await inter.followup.send(embed=embed2)

def setup(bot):
    bot.add_cog(MakerScrimTeams(bot))