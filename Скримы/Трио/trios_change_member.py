import disnake
from disnake.ext import commands
import json
import os

class TriosChangeMember(commands.Cog):
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
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

    @commands.slash_command(name="change_member_trios", description="Заменить тиммейта в команде")
    async def change_member(
        self,
        inter: disnake.ApplicationCommandInteraction,
        old_member: disnake.Member = commands.Param(description="Тиммейт, которого нужно заменить"),
        new_member: disnake.Member = commands.Param(description="Новый тиммейт")
    ):
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
        captain_id = inter.author.id
        team_found = False
        team_index = None
        for index, team in enumerate(data):
            if team["captain_id"] == captain_id:
                team_found = True
                team_index = index
                break
        if not team_found:
            embed = disnake.Embed(
                title="Ошибка",
                description="Вы не являетесь капитаном команды!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        team = data[team_index]
        if old_member.id not in team["teammates"].values():
            embed = disnake.Embed(
                title="Ошибка",
                description="Указанный участник не является тиммейтом вашей команды!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        if new_member.id == captain_id:
            embed = disnake.Embed(
                title="Ошибка",
                description="Капитан не может быть тиммейтом!",
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
                await old_member.remove_roles(member_role, reason="Замена тиммейта")
        if new_member:
            member_role = inter.guild.get_role(self.member_role_id)
            if member_role:
                await new_member.add_roles(member_role, reason="Назначение новым тиммейтом")
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
    bot.add_cog(TriosChangeMember(bot))