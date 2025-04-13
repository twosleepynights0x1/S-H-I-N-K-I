import disnake
from disnake.ext import commands
import json
import os

class MakerScrimClose(commands.Cog):
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

    @commands.slash_command(name="maker_scrim_trios_close", description="Завершить событие и удалить все команды")
    async def maker_scrim_trios_close(self, inter: disnake.ApplicationCommandInteraction):
        if not any(
            role.id == self.event_maker_role_id or role.permissions.administrator
            for role in inter.author.roles
        ):
            embed = disnake.Embed(
                title="Ошибка",
                description="У вас нет прав для использования этой команды!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url)
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
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            embed = disnake.Embed(
                title="Ошибка",
                description="Нет зарегистрированных команд для удаления.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        for team in data:
            captain = inter.guild.get_member(team["captain_id"])
            if captain:
                captain_role = inter.guild.get_role(self.captain_role_id)
                if captain_role:
                    await captain.remove_roles(captain_role, reason="Завершение события")
            for teammate_id in team["teammates"].values():
                teammate = inter.guild.get_member(teammate_id)
                if teammate:
                    member_role = inter.guild.get_role(self.member_role_id)
                    if member_role:
                        await teammate.remove_roles(member_role, reason="Завершение события")
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        embed = disnake.Embed(
            title="Скримы завершены",
            description=(
                "Все команды успешно удалены, а роли сняты.\n"
            ),
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352445993937014814/standard_15.gif?ex=67de0afc&is=67dcb97c&hm=4107c81680fbcfb45e95a4a646ad3851095ac749424595d4efd34daf78dbf055&=&width=1424&height=82")
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(MakerScrimClose(bot))