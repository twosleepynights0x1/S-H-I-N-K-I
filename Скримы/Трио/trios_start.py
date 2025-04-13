import disnake
from disnake.ext import commands
import json
import os

class ScrimsStart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "data/trios_reg.json"
        self.voice_data_file = "data/trios_voice.json"
        CONFIG_PATH = os.path.join('conf', 'config.json')
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")
        self.category_id = config["scrims"]["ScrimVoiceCategory"]
        self.member_role_id = config["scrims"]["ScrimMemberRole"]
        self.captain_role_id = config["scrims"]["CapitanRole"]

    @commands.slash_command(name="maker_create_trios", description="Создать голосовые каналы для команд")
    @commands.has_permissions(administrator=True)
    async def scrims_start_trios(self, inter: disnake.ApplicationCommandInteraction):
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
        if not data:
            embed = disnake.Embed(
                title="Ошибка",
                description="Нет зарегистрированных команд для создания голосовых каналов.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        category = inter.guild.get_channel(self.category_id)
        if not category or not isinstance(category, disnake.CategoryChannel):
            embed = disnake.Embed(
                title="Ошибка",
                description="Категория для создания голосовых каналов не найдена!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        existing_channels = [channel.name for channel in category.voice_channels]
        team_names = [f"🤖┋{team['team_name']}" for team in data]
        if any(team_name in existing_channels for team_name in team_names):
            embed = disnake.Embed(
                title="Ошибка",
                description="Голосовые комнаты для команд уже созданы!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        created_channels = []
        voice_channel_ids = []
        for team in data:
            team_name = f"🤖┋{team['team_name']}"
            captain_id = team["captain_id"]
            teammate1_id = team["teammates"]["teammate1"]
            teammate2_id = team["teammates"]["teammate2"]
            voice_channel = await category.create_voice_channel(
                name=team_name,
                user_limit=3
            )
            created_channels.append(f"<#{voice_channel.id}>")
            voice_channel_ids.append(voice_channel.id)
            await voice_channel.set_permissions(
                inter.guild.default_role,
                connect=False,
                view_channel=False
            )
            scrim_member_role = inter.guild.get_role(self.member_role_id)
            if scrim_member_role:
                await voice_channel.set_permissions(
                    scrim_member_role,
                    connect=False,
                    view_channel=True
                )
            captain_role = inter.guild.get_role(self.captain_role_id)
            if captain_role:
                await voice_channel.set_permissions(
                    captain_role,
                    connect=False,
                    view_channel=True
                )
            captain = inter.guild.get_member(captain_id)
            if captain:
                await voice_channel.set_permissions(
                    captain,
                    connect=True,
                    view_channel=True
                )
            teammate1 = inter.guild.get_member(teammate1_id)
            if teammate1:
                await voice_channel.set_permissions(
                    teammate1,
                    connect=True,
                    view_channel=True
                )
            teammate2 = inter.guild.get_member(teammate2_id)
            if teammate2:
                await voice_channel.set_permissions(
                    teammate2,
                    connect=True,
                    view_channel=True
                )
        os.makedirs(os.path.dirname(self.voice_data_file), exist_ok=True)
        with open(self.voice_data_file, "w", encoding="utf-8") as f:
            json.dump(voice_channel_ids, f, indent=4, ensure_ascii=False)
        embed = disnake.Embed(
            title="Голосовые каналы созданы",
            description="\n".join(created_channels),
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352445685798011031/standard_14.gif?ex=67de0ab2&is=67dcb932&hm=be3496602330676bd5e71dcb5731175187cff51599c26a002a40b08b4d063256&=&width=1424&height=82")
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(ScrimsStart(bot))