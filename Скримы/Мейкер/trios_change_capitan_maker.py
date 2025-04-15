import disnake
from disnake.ext import commands
import json
import os

class MakerChangeCapitanTrios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/scrim_reg.json"
        CONFIG_PATH = os.path.join('conf', 'config.json')
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")
        self.captain_role_id = config["scrims"]["CapitanRole"]
        self.member_role_id = config["scrims"]["ScrimMemberRole"]
        self.event_maker_role_id = config["scrims"]["EventMakerRole"]

    @commands.slash_command(name="maker_change_capitan_trios", description="Передать роль капитана другому участнику (только для ивент-мейкеров)")
    async def maker_change_capitan(
        self,
        inter: disnake.ApplicationCommandInteraction,
        team_name: str = commands.Param(description="Название команды"),
        new_captain: disnake.Member = commands.Param(description="Новый капитан команды")
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
                description="Файл данных не найден!",
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
        current_captain_id = team["captain_id"]
        if new_captain.id == inter.author.id:
            embed = disnake.Embed(
                title="Ошибка",
                description="Вы не можете передать роль капитана самому себе!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        current_captain = inter.guild.get_member(current_captain_id)
        if current_captain:
            captain_role = inter.guild.get_role(self.captain_role_id)
            if captain_role:
                await current_captain.remove_roles(captain_role, reason="Передача роли капитана ивент-мейкером")
        if new_captain:
            captain_role = inter.guild.get_role(self.captain_role_id)
            if captain_role:
                await new_captain.add_roles(captain_role, reason="Назначение новым капитаном ивент-мейкером")
        data[team_index]["captain_id"] = new_captain.id
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        embed = disnake.Embed(
            title="Капитан успешно изменен!",
            description=(
                f"**Команда:** {team['team_name']}\n"
                f"**Новый капитан:** {new_captain.mention} ({new_captain})"
            ),
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353445882170970172/standard_18.gif?ex=67e1ae34&is=67e05cb4&hm=117584818324c88d4999813a71f7c807ce468d8264197e7570040657c05d91cb&=")
        embed.set_footer(
            text=f"Инициатор: {inter.user.display_name}",
            icon_url=inter.user.display_avatar.url
        )
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(MakerChangeCapitanTrios(bot))