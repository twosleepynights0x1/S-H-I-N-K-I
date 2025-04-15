import disnake
from disnake.ext import commands
import json
import os

class ScrimRegistration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/scrim_reg.json"
        self.allow_reg_file = "data/trios_allow.json"
        config_path = os.path.join('conf', 'config.json')
        with open(config_path, 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)
        self.captain_role_id = config['scrims']['CapitanRole']
        self.member_role_id = config['scrims']['ScrimMemberRole']
        self.log_channel_id = config['channels']['logs']['ScrimRegChannel']
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.allow_reg_file), exist_ok=True)

    def is_registration_allowed(self):
        # Проверяем, существует ли файл
        if not os.path.exists(self.allow_reg_file):
            print(f"Файл {self.allow_reg_file} не существует, создаём новый с allow_registration=False")
            with open(self.allow_reg_file, "w", encoding="utf-8") as f:
                json.dump({"allow_registration": False}, f, ensure_ascii=False)
            return False
        
        # Пытаемся прочитать файл
        try:
            with open(self.allow_reg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"Содержимое {self.allow_reg_file}: {data}")
            allow_registration = data.get("allow_registration", False)
            print(f"Значение allow_registration: {allow_registration}")
            return allow_registration
        except json.JSONDecodeError as e:
            print(f"Ошибка декодирования JSON в файле {self.allow_reg_file}: {e}")
            return False
        except Exception as e:
            print(f"Ошибка при чтении файла {self.allow_reg_file}: {e}")
            return False

    @commands.slash_command(name="scrim_reg", description="Зарегистрировать команду для скримов")
    async def scrim_reg(
        self,
        inter: disnake.ApplicationCommandInteraction,
        mode: str = commands.Param(
            description="Режим скримов",
            choices=["Трио"]
        ),
        team_name: str = commands.Param(description="Название команды"),
        teammate1: disnake.Member = commands.Param(description="Первый тиммейт"),
        teammate2: disnake.Member = commands.Param(description="Второй тиммейт")
    ):
        await inter.response.defer(ephemeral=True)
        if not self.is_registration_allowed():
            embed = disnake.Embed(
                title="Регистрация закрыта",
                description="В данный момент регистрация команд закрыта.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        if not os.path.exists(self.data_file):
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False)
        with open(self.data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        captain_id = inter.author.id
        for team in data:
            if captain_id == team["captain_id"]:
                embed = disnake.Embed(
                    title="Ошибка регистрации",
                    description="Вы уже зарегистрированы как капитан другой команды!",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                embed.set_thumbnail(url=inter.guild.me.avatar.url)
                embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
                await inter.edit_original_response(embed=embed)
                return
        for team in data:
            if captain_id in team["teammates"].values():
                embed = disnake.Embed(
                    title="Ошибка регистрации",
                    description="Вы уже зарегистрированы как тиммейт в другой команде!",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                embed.set_thumbnail(url=inter.guild.me.avatar.url)
                embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
                await inter.edit_original_response(embed=embed)
                return
        for team in data:
            if teammate1.id in team["teammates"].values() or teammate2.id in team["teammates"].values():
                embed = disnake.Embed(
                    title="Ошибка регистрации",
                    description="Один из тиммейтов уже зарегистрирован в другой команде!",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                embed.set_thumbnail(url=inter.guild.me.avatar.url)
                embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
                await inter.edit_original_response(embed=embed)
                return
        if captain_id in [teammate1.id, teammate2.id]:
            embed = disnake.Embed(
                title="Ошибка регистрации",
                description="Капитан не может быть тиммейтом!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        if teammate1.id == teammate2.id:
            embed = disnake.Embed(
                title="Ошибка регистрации",
                description="Нельзя добавить одного и того же участника дважды!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        for team in data:
            if team_name.lower() == team["team_name"].lower():
                embed = disnake.Embed(
                    title="Ошибка регистрации",
                    description="Команда с таким названием уже зарегистрирована!",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                embed.set_thumbnail(url=inter.guild.me.avatar.url)
                embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
                await inter.edit_original_response(embed=embed)
                return
        team_data = {
            "mode": mode,
            "team_name": team_name,
            "captain_id": captain_id,
            "teammates": {
                "teammate1": teammate1.id,
                "teammate2": teammate2.id
            }
        }
        data.append(team_data)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        captain = inter.guild.get_member(captain_id)
        if captain:
            captain_role = inter.guild.get_role(self.captain_role_id)
            if captain_role:
                await captain.add_roles(captain_role, reason="Регистрация команды")
        for teammate in [teammate1, teammate2]:
            member_role = inter.guild.get_role(self.member_role_id)
            if member_role:
                await teammate.add_roles(member_role, reason="Регистрация команды")
        embed = disnake.Embed(
            title="Регистрация команды успешна!",
            description=(
                f"**Режим:** {mode}\n"
                f"**Название команды:** **{team_name}**\n"
                f"**Капитан:** {inter.author.mention} ({inter.author})\n"
                f"**Тиммейт 1:** {teammate1.mention} ({teammate1})\n"
                f"**Тиммейт 2:** {teammate2.mention} ({teammate2})"
            ),
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=inter.guild.me.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352417883795226645/standard_12.gif?ex=67ddf0ce&is=67dc9f4e&hm=80bce8b98146a02897360be01efdc3233687416a4abe65b07f84b3f108a969dd&=&width=1424&height=82")
        await inter.edit_original_response(embed=embed)
        await self.send_log(embed)

    async def send_log(self, embed: disnake.Embed):
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(ScrimRegistration(bot))