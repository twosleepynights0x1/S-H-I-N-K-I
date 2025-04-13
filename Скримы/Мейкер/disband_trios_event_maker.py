import disnake
from disnake.ext import commands
import json
import os

class MakerDisbandTrios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/trios_reg.json"
        CONFIG_PATH = os.path.join('conf', 'config.json')
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")
        self.captain_role_id = config["scrims"]["CapitanRole"]
        self.member_role_id = config["scrims"]["ScrimMemberRole"]
        self.event_maker_role_id = config["scrims"]["EventMakerRole"]

    @commands.slash_command(name="maker_disband_trios", description="Расформировать указанную команду (только для ивент-мейкеров)")
    async def maker_disband_trios(
        self,
        inter: disnake.ApplicationCommandInteraction,
        team_name: str = commands.Param(description="Название команды для расформирования")
    ):
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
        await inter.response.defer()
        if not os.path.exists(self.data_file):
            embed = disnake.Embed(
                title="Ошибка",
                description="Файл с данными о командах не найден!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        team_index = None
        for index, team in enumerate(data):
            if team["team_name"].lower() == team_name.lower():
                team_index = index
                break
        if team_index is None:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"Команда с названием **{team_name}** не найдена!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        team = data[team_index]
        team_name = team["team_name"]
        captain_id = team["captain_id"]
        teammate1_id = team["teammates"]["teammate1"]
        teammate2_id = team["teammates"]["teammate2"]
        data.pop(team_index)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        captain = inter.guild.get_member(captain_id)
        if captain:
            captain_role = inter.guild.get_role(self.captain_role_id)
            if captain_role:
                await captain.remove_roles(captain_role, reason="Расформирование команды администратором")
        for teammate_id in [teammate1_id, teammate2_id]:
            teammate = inter.guild.get_member(teammate_id)
            if teammate:
                member_role = inter.guild.get_role(self.member_role_id)
                if member_role:
                    await teammate.remove_roles(member_role, reason="Расформирование команды администратором")
        embed = disnake.Embed(
            title="Команда расформирована",
            description=f"Команда **{team_name}** успешно расформирована",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352450855793852527/standard_16.gif?ex=67de0f83&is=67dcbe03&hm=702aed7e85681e96aff73f345a600f9da45a6adbfe9443ffca0ef9def862b222&=&width=1424&height=82")
        embed.set_footer(
            text=f"Инициатор: {inter.user.display_name}",
            icon_url=inter.user.display_avatar.url
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(
            text=f"Мейкер: {inter.user.display_name}",
            icon_url=inter.user.display_avatar.url
        )
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(MakerDisbandTrios(bot))