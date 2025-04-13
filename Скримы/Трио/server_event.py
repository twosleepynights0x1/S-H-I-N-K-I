import disnake
from disnake.ext import commands
from disnake.ui import Modal, TextInput
from datetime import datetime, timedelta
import json
import os

class EventModal(Modal):
    def __init__(self):
        components = [
            TextInput(
                label="Название мероприятия",
                placeholder="Введите название мероприятия",
                custom_id="event_name",
                style=disnake.TextInputStyle.short,
                max_length=100,
            ),
            TextInput(
                label="Описание мероприятия",
                placeholder="Введите описание мероприятия",
                custom_id="event_description",
                style=disnake.TextInputStyle.paragraph,
                max_length=1000,
            ),
            TextInput(
                label="Место проведения",
                placeholder="Введите место проведения (ссылка или текст)",
                custom_id="event_location",
                style=disnake.TextInputStyle.short,
                max_length=100,
            ),
            TextInput(
                label="Время начала (день месяц время)",
                placeholder="Пример: 23 03 20:00",
                custom_id="event_start_time",
                style=disnake.TextInputStyle.short,
                max_length=20,
            ),
            TextInput(
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
            await inter.response.send_message(embed=embed, ephemeral=True)
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
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"Произошла ошибка при создании мероприятия: {e}",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await inter.response.send_message(embed=embed, ephemeral=True)

class TestCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        config_path = os.path.join('conf', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {config_path}: {e}")
        self.event_maker_role_id = config["scrims"]["EventMakerRole"]

    @commands.slash_command(
        name="maker_event_create",
        description="Создать мероприятие"
    )
    async def test_event_command(self, inter: disnake.ApplicationCommandInteraction):
        if not any(
            role.id == self.event_maker_role_id or role.permissions.administrator
            for role in inter.author.roles
        ):
            embed = disnake.Embed(
                title="Ошибка",
                description="**У вас нет прав для использования этой команды ^^**",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        await inter.response.send_modal(modal=EventModal())

def setup(bot: commands.Bot):
    bot.add_cog(TestCog(bot))