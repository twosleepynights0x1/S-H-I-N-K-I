import disnake
from disnake.ext import commands
import json
import os

class MakerChangeMemberTrios(commands.Cog):
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

    @commands.slash_command(name="maker_change_member_trios", description="Заменить тиммейта в команде (только для ивент-мейкеров)")
    async def maker_change_member(
        self,
        inter: disnake.ApplicationCommandInteraction,
        team_name: str = commands.Param(description="Название команды"),
        old_member: disnake.Member = commands.Param(description="Тиммейт, которого нужно заменить"),
        new_member: disnake.Member = commands.Param(description="Новый тиммейт")
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
        if old_member.id not in team["teammates"].values():
            embed = disnake.Embed(
                title="Ошибка",
                description="Указанный участник не является тиммейтом этой команды!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        if old_member.id == new_member.id:
            embed = disnake.Embed(
                title="Ошибка",
                description="Нельзя заменить участника на самого себя!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        if old_member:
            member_role = inter.guild.get_role(self.member_role_id)
            if member_role:
                await old_member.remove_roles(member_role, reason="Замена тиммейта ивент-мейкером")
        if new_member:
            member_role = inter.guild.get_role(self.member_role_id)
            if member_role:
                await new_member.add_roles(member_role, reason="Назначение новым тиммейтом ивент-мейкером")
        for key, value in team["teammates"].items():
            if value == old_member.id:
                team["teammates"][key] = new_member.id
                break
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        embed = disnake.Embed(
            title="Тиммейт успешно заменен!",
            description=(
                f"**Команда:** {team['team_name']}\n"
                f"**Старый тиммейт:** {old_member.mention} ({old_member})\n"
                f"**Новый тиммейт:** {new_member.mention} ({new_member})"
            ),
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353449531215319091/standard_19.gif?ex=67e1b19a&is=67e0601a&hm=04f610f00ec498190b96eb8ac9193941646fdb5cc8e53c1cafe8e9ecab287cb7&=")
        embed.set_footer(
            text=f"Инициатор: {inter.user.display_name}",
            icon_url=inter.user.display_avatar.url
        )
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(MakerChangeMemberTrios(bot))