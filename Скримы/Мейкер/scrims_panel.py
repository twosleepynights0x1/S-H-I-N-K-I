import disnake
from disnake.ext import commands
import json
from pathlib import Path
from typing import List, Dict
import os
from datetime import datetime, timedelta

TRIOS_ALLOW_PATH = Path("data/trios_allow.json")
TRIOS_REG_PATH = Path("data/trios_reg.json")
EVENT_PATH = Path("data/event.json")
VOICE_DATA_PATH = Path("data/trios_voice.json")
SPOT_PICKER_PATH = Path("data/spot_picker_trio.json")

CAPTAIN_CHANNEL_ID = 1351353917740679270
CAPTAIN_ROLE_ID = 1072598159894782184
MEMBER_ROLE_ID = 1131334572051808296
EVENT_MAKER_ROLE_ID = 652889442524069898
CATEGORY_ID = 1352446041655345225

class EventModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Название мероприятия",
                placeholder="Введите название мероприятия",
                custom_id="event_name",
                style=disnake.TextInputStyle.short,
                max_length=100,
            ),
            disnake.ui.TextInput(
                label="Описание мероприятия",
                placeholder="Введите описание мероприятия",
                custom_id="event_description",
                style=disnake.TextInputStyle.paragraph,
                max_length=1000,
            ),
            disnake.ui.TextInput(
                label="Место проведения",
                placeholder="Введите место проведения (ссылка или текст)",
                custom_id="event_location",
                style=disnake.TextInputStyle.short,
                max_length=100,
            ),
            disnake.ui.TextInput(
                label="Время начала (день месяц время)",
                placeholder="Пример: 23 03 20:00",
                custom_id="event_start_time",
                style=disnake.TextInputStyle.short,
                max_length=20,
            ),
            disnake.ui.TextInput(
                label="Длительность (в минутах)",
                placeholder="Введите длительность мероприятия",
                custom_id="event_duration",
                style=disnake.TextInputStyle.short,
                max_length=5,
            ),
        ]
        super().__init__(title="Создание мероприятия", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        event_name = inter.text_values["event_name"]
        event_description = inter.text_values["event_description"]
        event_location = inter.text_values["event_location"]
        event_start_time = inter.text_values["event_start_time"]
        event_duration = inter.text_values["event_duration"]

        await inter.response.defer(ephemeral=True)

        try:
            start_time = datetime.strptime(event_start_time, "%d %m %H:%M")
            start_time = start_time.replace(year=datetime.now().year)
            event_duration = int(event_duration)
            end_time = start_time + timedelta(minutes=event_duration)

            entity_metadata = disnake.GuildScheduledEventMetadata(location=event_location)

            event = await inter.guild.create_scheduled_event(
                name=event_name,
                description=event_description,
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
                entity_type=disnake.GuildScheduledEventEntityType.external,
                privacy_level=disnake.GuildScheduledEventPrivacyLevel.guild_only,
                entity_metadata=entity_metadata,
            )

            cog = inter.bot.get_cog("ScrimsPanel")
            cog.current_event_id = event.id
            cog.save_event_id()

            embed = disnake.Embed(
                title="Мероприятие создано!",
                description=(
                    f"**Название:** {event.name}\n"
                    f"**Описание:** {event_description}\n"
                    f"**Место:** {event_location}\n"
                    f"**Начало:** {start_time.strftime('%d.%m.%Y %H:%M')}\n"
                    f"**Окончание:** {end_time.strftime('%d.%m.%Y %H:%M')}"
                ),
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353441516424790056/standard_17.gif?ex=67e1aa23&is=67e058a3&hm=b8254d2fc3a5f613445cb97ae2e6006037242945afba928d05d6bf810a8bf8b4&=")
            embed.set_footer(
                text=f"Мейкер: {inter.author.display_name}",
                icon_url=inter.author.display_avatar.url
            )
            await inter.edit_original_response(embed=embed)

        except ValueError as e:
            embed = disnake.Embed(
                title="Ошибка",
                description=(
                    f"**Ошибка:** {e}\n"
                    "Убедитесь, что:\n"
                    "- Время начала в формате `день месяц время` (например, `23 03 20:00`).\n"
                    "- Длительность — целое число (в минутах)."
                ),
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await inter.edit_original_response(embed=embed)
        except Exception as e:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"Произошла ошибка при создании мероприятия: {e}",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await inter.edit_original_response(embed=embed)

class SpotPickerModal(disnake.ui.Modal):
    def __init__(self, lobby: str):
        self.lobby = lobby
        components = [
            disnake.ui.TextInput(
                label=f"Ссылка на спот пикер 1 ({lobby})",
                placeholder=f"Введите первую ссылку для {lobby} (обязательно)",
                custom_id="spot_picker_link1",
                style=disnake.TextInputStyle.short,
                max_length=200,
                required=True
            ),
            disnake.ui.TextInput(
                label=f"Пароль 1 ({lobby})",
                placeholder=f"Введите пароль для первого спот пикера {lobby} (обязательно)",
                custom_id="spot_picker_password1",
                style=disnake.TextInputStyle.short,
                max_length=50,
                required=True
            ),
            disnake.ui.TextInput(
                label=f"Ссылка на спот пикер 2 ({lobby})",
                placeholder=f"Введите вторую ссылку для {lobby} (необязательно)",
                custom_id="spot_picker_link2",
                style=disnake.TextInputStyle.short,
                max_length=200,
                required=False
            ),
            disnake.ui.TextInput(
                label=f"Пароль 2 ({lobby})",
                placeholder=f"Введите пароль для второго спот пикера {lobby} (необязательно)",
                custom_id="spot_picker_password2",
                style=disnake.TextInputStyle.short,
                max_length=50,
                required=False
            ),
        ]
        super().__init__(title=f"Настройка спот пикеров для {lobby}", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        spot_picker_link1 = inter.text_values["spot_picker_link1"]
        spot_picker_password1 = inter.text_values["spot_picker_password1"]
        spot_picker_link2 = inter.text_values.get("spot_picker_link2", "")
        spot_picker_password2 = inter.text_values.get("spot_picker_password2", "")

        try:
            with open(SPOT_PICKER_PATH, "r", encoding="utf-8") as f:
                spot_picker_data = json.load(f)

            lobby_key = "lobby1" if self.lobby == "Лобби 1" else "lobby2"
            spot_picker_data[lobby_key] = {
                "spot_picker1": {
                    "link": spot_picker_link1,
                    "password": spot_picker_password1
                },
                "spot_picker2": {
                    "link": spot_picker_link2,
                    "password": spot_picker_password2
                }
            }

            with open(SPOT_PICKER_PATH, "w", encoding="utf-8") as f:
                json.dump(spot_picker_data, f, indent=4, ensure_ascii=False)

            description = (
                f"**Спот пикер 1:**\n"
                f"Ссылка: {spot_picker_link1}\n"
                f"Пароль: {spot_picker_password1}\n"
            )
            if spot_picker_link2 or spot_picker_password2:
                description += (
                    f"**Спот пикер 2:**\n"
                    f"Ссылка: {spot_picker_link2 or 'Не указана'}\n"
                    f"Пароль: {spot_picker_password2 or 'Не указан'}\n"
                )

            embed = disnake.Embed(
                title=f"Спот пикеры настроены для {self.lobby}!",
                description=description,
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353441516424790056/standard_17.gif?ex=67e1aa23&is=67e058a3&hm=b8254d2fc3a5f613445cb97ae2e6006037242945afba928d05d6bf810a8bf8b4&=")
            embed.set_footer(
                text=f"Мейкер: {inter.author.display_name}",
                icon_url=inter.author.display_avatar.url
            )
            await inter.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"Произошла ошибка при сохранении спот пикеров: {e}",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await inter.edit_original_response(embed=embed)

class ScrimsPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_file = "data/trios_reg.json"
        self.voice_data_file = "data/trios_voice.json"
        self.spot_picker_file = "data/spot_picker_trio.json"
        self.captain_channel_id = CAPTAIN_CHANNEL_ID
        self.captain_role_id = CAPTAIN_ROLE_ID
        self.member_role_id = MEMBER_ROLE_ID
        self.event_maker_role_id = EVENT_MAKER_ROLE_ID
        self.category_id = CATEGORY_ID
        self.current_event_id = None
        for path in [TRIOS_ALLOW_PATH, TRIOS_REG_PATH, EVENT_PATH, VOICE_DATA_PATH, SPOT_PICKER_PATH]:
            path.parent.mkdir(exist_ok=True, parents=True)
            if not path.exists():
                with open(path, "w", encoding="utf-8") as f:
                    if path in [TRIOS_REG_PATH, VOICE_DATA_PATH]:
                        json.dump([], f, ensure_ascii=False)
                    elif path == TRIOS_ALLOW_PATH:
                        json.dump({"allow_registration": False}, f, ensure_ascii=False)
                    elif path == EVENT_PATH:
                        json.dump({"event_id": None}, f, ensure_ascii=False)
                    elif path == SPOT_PICKER_PATH:
                        json.dump({
                            "lobby1": {
                                "spot_picker1": {"link": "", "password": ""},
                                "spot_picker2": {"link": "", "password": ""}
                            },
                            "lobby2": {
                                "spot_picker1": {"link": "", "password": ""},
                                "spot_picker2": {"link": "", "password": ""}
                            }
                        }, f, ensure_ascii=False)
        self.load_event_id()

    def load_event_id(self):
        try:
            with open(EVENT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.current_event_id = data.get("event_id")
        except Exception as e:
            print(f"Ошибка при загрузке ID мероприятия: {e}")
            self.current_event_id = None

    def save_event_id(self):
        try:
            with open(EVENT_PATH, "w", encoding="utf-8") as f:
                json.dump({"event_id": self.current_event_id}, f, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении ID мероприятия: {e}")

    async def check_event_exists(self, guild: disnake.Guild) -> bool:
        if not self.current_event_id:
            return False
        try:
            await guild.fetch_scheduled_event(self.current_event_id)
            return True
        except disnake.NotFound:
            self.current_event_id = None
            self.save_event_id()
            return False
        except Exception as e:
            print(f"Ошибка при проверке мероприятия: {e}")
            return False

    def get_trios_status(self) -> bool:
        with open(TRIOS_ALLOW_PATH, "r", encoding="utf-8") as f:
            return json.load(f)["allow_registration"]

    def set_trios_status(self, status: bool):
        with open(TRIOS_ALLOW_PATH, "w", encoding="utf-8") as f:
            json.dump({"allow_registration": status}, f, ensure_ascii=False)

    def get_registered_teams(self) -> List[Dict]:
        try:
            with open(TRIOS_REG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при чтении файла команд: {e}")
            return []

    async def create_panel_embed(self) -> disnake.Embed:
        status_text = "🟢 Открыта" if self.get_trios_status() else "🔴 Закрыта"
        embed = disnake.Embed(
            title="Панель управления скримами",
            description="Текущие настройки скримов:",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.add_field(name="Регистрация на триос:", value=status_text, inline=False)
        if self.current_event_id:
            embed.add_field(name="Текущее мероприятие:", value="Активно", inline=False)
        return embed

    async def create_panel_components(self) -> List[disnake.ui.ActionRow]:
        is_open = self.get_trios_status()
        open_btn = disnake.ui.Button(
            style=disnake.ButtonStyle.green if not is_open else disnake.ButtonStyle.grey,
            label="Открыть регистрацию",
            custom_id="open_reg",
            disabled=is_open
        )
        close_btn = disnake.ui.Button(
            style=disnake.ButtonStyle.red if is_open else disnake.ButtonStyle.grey,
            label="Закрыть регистрацию",
            custom_id="close_reg",
            disabled=not is_open
        )
        show_teams_btn = disnake.ui.Button(
            style=disnake.ButtonStyle.blurple,
            label="Показать список команд",
            custom_id="show_teams"
        )
        spot_picker_btn = disnake.ui.Button(
            style=disnake.ButtonStyle.blurple,
            label="Спот пикер",
            custom_id="spot_picker"
        )
        event_mgmt = disnake.ui.Select(
            placeholder="Управление ивентом",
            custom_id="event_management",
            options=[
                disnake.SelectOption(label="Создать мероприятие", value="create_event"),
                disnake.SelectOption(label="Завершить мероприятие", value="end_event"),
                disnake.SelectOption(label="Создать голосовые комнаты", value="create_vc"),
                disnake.SelectOption(label="Удалить голосовые комнаты", value="delete_vc"),
                disnake.SelectOption(label="Поделиться спот-пикером", value="share_spot_picker"),
                disnake.SelectOption(label="Очистить спот-пикер", value="clear_spot_picker"),
                disnake.SelectOption(label="Завершить скримы", value="close_scrims", description="Удалить все зарегистрированные команды")
            ]
        )
        return [
            disnake.ui.ActionRow(open_btn, close_btn),
            disnake.ui.ActionRow(show_teams_btn, spot_picker_btn),
            disnake.ui.ActionRow(event_mgmt)
        ]

    @commands.slash_command(
        name="scrims_panel",
        description="Панель управления скримами",
        default_member_permissions=disnake.Permissions(administrator=True)
    )
    async def scrims_panel(self, inter: disnake.ApplicationCommandInteraction):
        await self.check_event_exists(inter.guild)
        embed = await self.create_panel_embed()
        components = await self.create_panel_components()
        await inter.response.send_message(embed=embed, components=components)

    async def update_panel(self, inter: disnake.MessageInteraction):
        await self.check_event_exists(inter.guild)
        embed = await self.create_panel_embed()
        components = await self.create_panel_components()
        await inter.edit_original_response(embed=embed, components=components)

    async def create_voice_channels(self, inter: disnake.MessageInteraction):
        if not os.path.exists(self.data_file):
            embed = disnake.Embed(
                title="Ошибка",
                description="Файл с данными о командах не найден!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.channel.send(embed=embed)
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
            await inter.channel.send(embed=embed)
            return

        category = inter.guild.get_channel(self.category_id)
        if not category or not isinstance(category, disnake.CategoryChannel):
            embed = disnake.Embed(
                title="Ошибка",
                description="Категория для создания голосовых каналов не найдена!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.channel.send(embed=embed)
            return

        if os.path.exists(self.voice_data_file):
            with open(self.voice_data_file, "r", encoding="utf-8") as f:
                voice_channel_ids = json.load(f)
            if voice_channel_ids:
                existing_channels = [inter.guild.get_channel(channel_id) for channel_id in voice_channel_ids]
                if any(channel is not None and isinstance(channel, disnake.VoiceChannel) for channel in existing_channels):
                    embed = disnake.Embed(
                        title="Ошибка",
                        description="Голосовые комнаты для команд уже созданы!",
                        color=disnake.Color.from_rgb(250, 77, 252)
                    )
                    embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
                    await inter.channel.send(embed=embed)
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

        with open(self.voice_data_file, "w", encoding="utf-8") as f:
            json.dump(voice_channel_ids, f, indent=4, ensure_ascii=False)

        embed = disnake.Embed(
            title="Голосовые каналы созданы",
            description="\n".join(created_channels),
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352445685798011031/standard_14.gif?ex=67de0ab2&is=67dcb932&hm=be3496602330676bd5e71dcb5731175187cff51599c26a002a40b08b4d063256&=&width=1424&height=82")
        embed.set_footer(
            text=f"Мейкер: {inter.author.display_name}",
            icon_url=inter.author.display_avatar.url
        )
        await inter.channel.send(embed=embed)

    async def delete_voice_channels(self, inter: disnake.MessageInteraction):
        if not os.path.exists(self.voice_data_file):
            embed = disnake.Embed(
                title="Ошибка",
                description="Файл с данными о голосовых каналах не найден!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.channel.send(embed=embed)
            return

        with open(self.voice_data_file, "r", encoding="utf-8") as f:
            voice_channel_ids = json.load(f)

        if not voice_channel_ids:
            embed = disnake.Embed(
                title="Ошибка",
                description="Нет голосовых каналов для удаления.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.channel.send(embed=embed)
            return

        deleted_channels = []
        for channel_id in voice_channel_ids:
            channel = inter.guild.get_channel(channel_id)
            if channel and isinstance(channel, disnake.VoiceChannel):
                await channel.delete(reason="Завершение скримов")
                deleted_channels.append(f"<#{channel_id}>")

        with open(self.voice_data_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)

        embed = disnake.Embed(
            title="Скримы завершены",
            description="Все голосовые каналы успешно удалены.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352445993937014814/standard_15.gif?ex=67de0afc&is=67dcb97c&hm=4107c81680fbcfb45e95a4a646ad3851095ac749424595d4efd34daf78dbf055&=&width=1424&height=82")
        embed.set_footer(
            text=f"Мейкер: {inter.author.display_name}",
            icon_url=inter.author.display_avatar.url
        )
        await inter.channel.send(embed=embed)

    async def share_spot_picker(self, inter: disnake.MessageInteraction):
        captain_channel = inter.guild.get_channel(self.captain_channel_id)
        if not captain_channel:
            embed = disnake.Embed(
                title="Ошибка",
                description="Канал капитанов не найден!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.channel.send(embed=embed)
            return

        try:
            with open(self.spot_picker_file, "r", encoding="utf-8") as f:
                spot_picker_data = json.load(f)

            description = "Используйте указанные ниже ссылки и пароли для выбора спотов. На каждый спот разрешен контест из 2 команд. За неподчинение команда может быть дисквалифицирована.\n\n"

            lobby1 = spot_picker_data["lobby1"]
            lobby2 = spot_picker_data["lobby2"]

            if lobby1["spot_picker1"]["link"] or lobby1["spot_picker1"]["password"]:
                description += "Лобби 1\n"
                description += f"> {lobby1['spot_picker1']['link']}\n"
                description += f"> Пароль: **{lobby1['spot_picker1']['password']}**\n"
                if lobby1["spot_picker2"]["link"] or lobby1["spot_picker2"]["password"]:
                    description += f"\n> {lobby1['spot_picker2']['link']}\n"
                    description += f"> Пароль: **{lobby1['spot_picker2']['password']}**\n"
                description += "\n"

            if lobby2["spot_picker1"]["link"] or lobby2["spot_picker1"]["password"]:
                description += "Лобби 2\n"
                description += f"> {lobby2['spot_picker1']['link']}\n"
                description += f"> Пароль: **{lobby2['spot_picker1']['password']}**\n"
                if lobby2["spot_picker2"]["link"] or lobby2["spot_picker2"]["password"]:
                    description += f"\n> {lobby2['spot_picker2']['link']}\n"
                    description += f"> Пароль: **{lobby2['spot_picker2']['password']}**\n"
                description += "\n"

            if description == "Используйте указанные ниже ссылки и пароли для выбора спотов. На каждый спот разрешен контест из 2 команд. За неподчинение команда может быть дисквалифицирована.\n\n":
                embed = disnake.Embed(
                    title="Ошибка",
                    description="Нет данных о спот-пикерах для отправки!",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
                await inter.channel.send(embed=embed)
                return

            embed = disnake.Embed(
                title="Спот-пикеры для выбора спотов",
                description=description.strip(),
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353441516424790056/standard_17.gif?ex=67e1aa23&is=67e058a3&hm=b8254d2fc3a5f613445cb97ae2e6006037242945afba928d05d6bf810a8bf8b4&=")
            embed.set_footer(
                text=f"Мейкер: {inter.author.display_name}",
                icon_url=inter.author.display_avatar.url
            )

            await captain_channel.send(embed=embed)
            await inter.channel.send(embed=disnake.Embed(
                title="Спот-пикеры отправлены!",
                description="Данные успешно отправлены в канал капитанов.",
                color=disnake.Color.from_rgb(250, 77, 252)
            ).set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353441516424790056/standard_17.gif?ex=67e1aa23&is=67e058a3&hm=b8254d2fc3a5f613445cb97ae2e6006037242945afba928d05d6bf810a8bf8b4&="))

        except Exception as e:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"Произошла ошибка при отправке спот-пикеров: {e}",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.channel.send(embed=embed)

    async def clear_spot_picker(self, inter: disnake.MessageInteraction):
        try:
            with open(self.spot_picker_file, "w", encoding="utf-8") as f:
                json.dump({
                    "lobby1": {
                        "spot_picker1": {"link": "", "password": ""},
                        "spot_picker2": {"link": "", "password": ""}
                    },
                    "lobby2": {
                        "spot_picker1": {"link": "", "password": ""},
                        "spot_picker2": {"link": "", "password": ""}
                    }
                }, f, indent=4, ensure_ascii=False)

            embed = disnake.Embed(
                title="Спот-пикеры очищены!",
                description="Данные спот-пикеров успешно сброшены.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352450855793852527/standard_16.gif?ex=67de0f83&is=67dcbe03&hm=702aed7e85681e96aff73f345a600f9da45a6adbfe9443ffca0ef9def862b222&=&width=1424&height=82")
            embed.set_footer(
                text=f"Мейкер: {inter.author.display_name}",
                icon_url=inter.author.display_avatar.url
            )
            await inter.channel.send(embed=embed)

        except Exception as e:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"Произошла ошибка при очистке спот-пикеров: {e}",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.channel.send(embed=embed)

    async def close_scrims(self, inter: disnake.MessageInteraction):
        if not os.path.exists(self.data_file):
            embed = disnake.Embed(
                title="Ошибка",
                description="Файл с данными о командах не найден!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.channel.send(embed=embed)
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
            await inter.channel.send(embed=embed)
            return

        for team in data:
            captain = inter.guild.get_member(team["captain_id"])
            if captain:
                captain_role = inter.guild.get_role(self.captain_role_id)
                if captain_role:
                    await captain.remove_roles(captain_role, reason="Завершение скримов")

            for teammate_id in team["teammates"].values():
                teammate = inter.guild.get_member(teammate_id)
                if teammate:
                    member_role = inter.guild.get_role(self.member_role_id)
                    if member_role:
                        await teammate.remove_roles(member_role, reason="Завершение скримов")

        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)

        embed = disnake.Embed(
            title="Скримы завершены",
            description="Все команды успешно удалены, а роли сняты.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352445993937014814/standard_15.gif?ex=67de0afc&is=67dcb97c&hm=4107c81680fbcfb45e95a4a646ad3851095ac749424595d4efd34daf78dbf055&=&width=1424&height=82")
        embed.set_footer(
            text=f"Мейкер: {inter.author.display_name}",
            icon_url=inter.author.display_avatar.url
        )
        await inter.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if not inter.author.guild_permissions.administrator:
            return await inter.response.send_message("Недостаточно прав!", ephemeral=True)
        
        custom_id = inter.component.custom_id
        
        if custom_id == "open_reg":
            self.set_trios_status(True)
            await inter.response.defer()
            await self.update_panel(inter)
            
        elif custom_id == "close_reg":
            self.set_trios_status(False)
            await inter.response.defer()
            await self.update_panel(inter)
            
        elif custom_id == "show_teams":
            await self.show_teams_list(inter)
            
        elif custom_id == "spot_picker":
            embed = disnake.Embed(
                title="Выбор лобби для спот пикеров",
                description="Выберите лобби для настройки спот пикеров:",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            components = [
                disnake.ui.ActionRow(
                    disnake.ui.Button(
                        label="Лобби 1",
                        style=disnake.ButtonStyle.blurple,
                        custom_id="spot_picker_lobby1"
                    ),
                    disnake.ui.Button(
                        label="Лобби 2",
                        style=disnake.ButtonStyle.blurple,
                        custom_id="spot_picker_lobby2"
                    )
                )
            ]
            await inter.response.send_message(embed=embed, components=components, ephemeral=True)
            
        elif custom_id == "spot_picker_lobby1":
            await inter.response.send_modal(modal=SpotPickerModal("Лобби 1"))
            
        elif custom_id == "spot_picker_lobby2":
            await inter.response.send_modal(modal=SpotPickerModal("Лобби 2"))
            
        elif custom_id.startswith("teams_prev_"):
            page = int(custom_id.split("_")[2]) - 1
            await inter.response.defer()
            await self.show_teams_list(inter, page)
            
        elif custom_id.startswith("teams_next_"):
            page = int(custom_id.split("_")[2]) + 1
            await inter.response.defer()
            await self.show_teams_list(inter, page)

    @commands.Cog.listener()
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        if not inter.author.guild_permissions.administrator:
            return await inter.response.send_message("Недостаточно прав!", ephemeral=True)
        
        custom_id = inter.component.custom_id
        
        if custom_id == "event_management":
            has_permission = any(
                role.id == self.event_maker_role_id or role.permissions.administrator
                for role in inter.author.roles
            )
            if not has_permission:
                embed = disnake.Embed(
                    title="Ошибка",
                    description="**У вас нет прав для управления мероприятиями!**",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
                await inter.response.send_message(embed=embed, ephemeral=True)
                return

            if "create_event" in inter.values:
                await inter.response.send_modal(modal=EventModal())
                return

            await inter.response.defer()
            
            if "end_event" in inter.values:
                if self.current_event_id:
                    try:
                        event = await inter.guild.fetch_scheduled_event(self.current_event_id)
                        await event.delete()
                        self.current_event_id = None
                        self.save_event_id()
                        embed = disnake.Embed(
                            title="Мероприятие завершено!",
                            description="Текущее мероприятие успешно завершено.",
                            color=disnake.Color.from_rgb(250, 77, 252)
                        )
                        embed.set_thumbnail(url=inter.guild.me.avatar.url)
                        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353441516424790056/standard_17.gif?ex=67e1aa23&is=67e058a3&hm=b8254d2fc3a5f613445cb97ae2e6006037242945afba928d05d6bf810a8bf8b4&=")
                        embed.set_footer(
                            text=f"Мейкер: {inter.author.display_name}",
                            icon_url=inter.author.display_avatar.url
                        )
                        await inter.channel.send(embed=embed)
                        await self.update_panel(inter)
                    except disnake.NotFound:
                        self.current_event_id = None
                        self.save_event_id()
                        embed = disnake.Embed(
                            title="Ошибка",
                            description="Мероприятие не найдено (возможно, уже завершено).",
                            color=disnake.Color.from_rgb(250, 77, 252)
                        )
                        embed.set_thumbnail(url=inter.guild.me.avatar.url)
                        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
                        await inter.channel.send(embed=embed)
                        await self.update_panel(inter)
                    except Exception as e:
                        embed = disnake.Embed(
                            title="Ошибка",
                            description=f"Произошла ошибка при завершении мероприятия: {e}",
                            color=disnake.Color.from_rgb(250, 77, 252)
                        )
                        embed.set_thumbnail(url=inter.guild.me.avatar.url)
                        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
                        await inter.channel.send(embed=embed)
                else:
                    embed = disnake.Embed(
                        title="Ошибка",
                        description="Нет активного мероприятия для завершения.",
                        color=disnake.Color.from_rgb(250, 77, 252)
                    )
                    embed.set_thumbnail(url=inter.guild.me.avatar.url)
                    embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
                    await inter.channel.send(embed=embed)
            
            elif "create_vc" in inter.values:
                await self.create_voice_channels(inter)
            
            elif "delete_vc" in inter.values:
                await self.delete_voice_channels(inter)
            
            elif "share_spot_picker" in inter.values:
                await self.share_spot_picker(inter)
            
            elif "clear_spot_picker" in inter.values:
                await self.clear_spot_picker(inter)
            
            elif "close_scrims" in inter.values:
                await self.close_scrims(inter)
        
        elif custom_id.startswith("team_select_") and inter.values:
            selected_value = inter.values[0]
            if selected_value.startswith("disband_"):
                team_index = int(selected_value.split("_")[1])
                await self.disband_team(inter, team_index)
            page = int(custom_id.split("_")[2])
            await self.show_teams_list(inter, page)

    async def show_teams_list(self, inter: disnake.MessageInteraction, page: int = 0):
        teams = self.get_registered_teams()
        if not teams:
            if inter.response.is_done():
                await inter.edit_original_response(content="Нет зарегистрированных команд!", components=[])
            else:
                await inter.response.send_message("Нет зарегистрированных команд!", ephemeral=True)
            return
        
        teams_list = []
        for idx, team in enumerate(teams):
            captain_tag = f"<@{team['captain_id']}>"
            teammate1_tag = f"<@{team['teammates']['teammate1']}>"
            teammate2_tag = f"<@{team['teammates']['teammate2']}>"
            team_info = (
                f"{idx + 1}. {team['team_name']}\n"
                f"{captain_tag} - Капитан\n"
                f"{teammate1_tag} - Тиммейт\n"
                f"{teammate2_tag} - Тиммейт\n"
                "\n"
            )
            teams_list.append(team_info)
        
        lobby_size = 20
        pages = [teams_list[i:i + lobby_size] for i in range(0, len(teams_list), lobby_size)]
        
        if page >= len(pages):
            page = 0
        elif page < 0:
            page = len(pages) - 1
        
        current_lobby = pages[page]
        lobby_title = "Первое лобби" if page == 0 else f"Второе лобби (Страница {page + 1})"
        
        lobby_info = "".join(current_lobby) if current_lobby else "Команды отсутствуют"
        embed = disnake.Embed(
            title="Список зарегистрированных команд",
            description=f"**{lobby_title}**\n\n{lobby_info}",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352422198534602792/standard_13.gif?ex=67ddf4d2&is=67dca352&hm=78cc04b7affe681565f1f7effbdc4a73224df318209d5b578357ecc0f10781de&=&width=1424&height=82")
        
        options = [
            disnake.SelectOption(
                label=f"Расформировать - {team['team_name']}",
                value=f"disband_{idx + page*lobby_size}"
            ) for idx, team in enumerate(teams[page*lobby_size:(page+1)*lobby_size])
        ]
        
        components = [disnake.ui.ActionRow(
            disnake.ui.Select(
                placeholder="Выберите команду для расформирования",
                custom_id=f"team_select_{page}",
                options=options if options else [disnake.SelectOption(label="Нет команд", value="none")]
            )
        )]
        
        if len(pages) > 1:
            buttons = []
            if page > 0:
                buttons.append(disnake.ui.Button(label="◀ Назад", custom_id=f"teams_prev_{page}"))
            if page < len(pages) - 1:
                buttons.append(disnake.ui.Button(label="Вперед ▶", custom_id=f"teams_next_{page}"))
            components.append(disnake.ui.ActionRow(*buttons))
        
        if inter.response.is_done():
            await inter.edit_original_response(embed=embed, components=components)
        else:
            await inter.response.send_message(embed=embed, components=components)

    async def disband_team(self, inter: disnake.MessageInteraction, team_index: int):
        try:
            has_permission = any(
                role.id == self.event_maker_role_id or role.permissions.administrator
                for role in inter.author.roles
            )
            if not has_permission:
                embed = disnake.Embed(
                    title="Ошибка",
                    description="У вас нет прав для расформирования команды!",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
                await inter.response.send_message(embed=embed)
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

            if team_index >= len(data):
                embed = disnake.Embed(
                    title="Ошибка",
                    description="Команда с указанным номером не найдена!",
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
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_footer(
                text=f"Мейкер: {inter.author.display_name}",
                icon_url=inter.author.display_avatar.url
            )

            await inter.channel.send(embed=embed)

            if captain:
                try:
                    await captain.send(embed=embed)
                except disnake.Forbidden:
                    print(f"Не удалось отправить сообщение капитану {captain_id}: нет доступа")
                except Exception as e:
                    print(f"Ошибка при отправке ЛС капитану {captain_id}: {e}")

            await inter.edit_original_response(content="Команда расформирована, уведомления отправлены.")

        except Exception as e:
            print(f"Ошибка при расформировании команды: {e}")
            embed = disnake.Embed(
                title="Ошибка",
                description="Произошла ошибка при расформировании команды. Попробуйте позже.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(ScrimsPanel(bot))