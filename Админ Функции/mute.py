import disnake
from disnake.ext import commands
from disnake import Embed
import datetime
import asyncio
import os
import json

if not os.path.exists('data'):
    os.makedirs('data')

CONFIG_PATH = os.path.join('conf', 'config.json')

MUTE_LIST_FILE = os.path.join('data', 'user_mute_list.json')
PROFILES_FILE = os.path.join('data', 'profiles.json')

class ReasonModal(disnake.ui.Modal):
    def __init__(self, cog, mute_type, member, time):
        self.cog = cog
        self.mute_type = mute_type
        self.member = member
        self.time = time
        components = [
            disnake.ui.TextInput(
                label="Введите причину мьюта",
                custom_id="reason_input",
                style=disnake.TextInputStyle.paragraph,
                placeholder="Укажите причину мьюта...",
                min_length=1,
                max_length=500
            )
        ]
        super().__init__(title="Укажите свою причину", components=components)

    async def callback(self, modal_inter: disnake.ModalInteraction):
        reason = modal_inter.text_values["reason_input"]
        await self.cog.mute_user(modal_inter, self.mute_type, self.member, self.time, reason)

class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")

        self.mute_roles = {
            "chat": config["roles"]["moderation"]["MuteChatRole"],
            "global": config["roles"]["moderation"]["MuteGlobalRole"],
            "voice": config["roles"]["moderation"]["MuteVoiceRole"]
        }

        self.allowed_roles = config["roles"]["administration"]["AdminRoles"]

        self.log_channel_id = config["channels"]["logs"]["CommandsLogChannel"]
        self.log_channel_mute_id = config["channels"]["logs"]["MuteLogChannel"]

    def load_profiles(self):
        if os.path.exists(PROFILES_FILE):
            with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def save_profiles(self, profiles):
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=4, ensure_ascii=False)

    def save_mute_to_profile(self, user_id, mute_time, reason, mute_type):
        profiles = self.load_profiles()
    
        mute_data = {
            "mute_time": mute_time.isoformat(),
            "reason": reason,
            "type": mute_type
        }

        if str(user_id) in profiles:
            if "mutes" not in profiles[str(user_id)]:
                profiles[str(user_id)]["mutes"] = []
            profiles[str(user_id)]["mutes"].append(mute_data)
        else:
            profiles[str(user_id)] = {"mutes": [mute_data]}

        self.save_profiles(profiles)

    def save_mute_to_list(self, user_id, mute_time, unmute_time):
        mute_data = {
            "user_id": user_id,
            "mute_time": mute_time.isoformat(),
            "unmute_time": unmute_time.isoformat()
        }

        if os.path.exists(MUTE_LIST_FILE):
            with open(MUTE_LIST_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        data.append(mute_data)
        with open(MUTE_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    async def log_action(self, interaction, member, action, time=None):
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            try:
                log_embed = disnake.Embed(title="Log", color=disnake.Color.blue())
                log_embed.add_field(name="Команда:", value=action["command"], inline=False)
                log_embed.add_field(name="Пользователь:", value=member.mention, inline=False)
                log_embed.add_field(name="Причина:", value=action["reason"], inline=False)
                if time:
                    log_embed.add_field(name="Срок мьюта:", value=time, inline=False)
                log_embed.set_thumbnail(url=member.avatar.url)
                log_embed.set_footer(
                    text=f"Администратор: {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url
                )
                log_embed.timestamp = interaction.created_at
                await log_channel.send(embed=log_embed)
                print(f"Лог отправлен: {action['command']} для пользователя {member.name}")
            except Exception as e:
                print(f"Ошибка при отправке лога: {e}")
                await interaction.followup.send("Не удалось отправить лог в канал.", ephemeral=True)
        else:
            print(f"Канал для логирования с ID {self.log_channel_id} не найден.")

    def convert_time_to_timedelta(self, time: str):
        if time.endswith("m"):
            return datetime.timedelta(minutes=int(time[:-1]))
        elif time.endswith("h"):
            return datetime.timedelta(hours=int(time[:-1]))
        elif time.endswith("d"):
            return datetime.timedelta(days=int(time[:-1]))
        else:
            raise ValueError("Неверный формат времени.")

    async def mute_user(self, inter, mute_type: str, member: disnake.Member, time: str, reason: str):
        mute_role = inter.guild.get_role(self.mute_roles[mute_type])
        if mute_role in member.roles:
            embed = Embed(
                title="Ошибка",
                description=f"{member.mention} уже замьючен!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            time_timedelta = self.convert_time_to_timedelta(time)
        except ValueError:
            embed = Embed(
                title="Ошибка",
                description="Неверный формат времени. Пример: 1m (минута), 2h (час), 3d (день).",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        # Проверяем, если это войс-мут и участник находится в голосовом канале
        if mute_type == "voice" and member.voice is not None:
            try:
                await member.move_to(None)  # Отключаем участника от голосового канала
                print(f"Участник {member.name} был отключён от голосового канала при выдаче войс-мута.")
            except Exception as e:
                print(f"Ошибка при отключении участника {member.name} от голосового канала: {e}")

        await member.add_roles(mute_role)
        mute_time = datetime.datetime.utcnow()
        unmute_time = mute_time + time_timedelta

        self.save_mute_to_list(member.id, mute_time, unmute_time)
        mute_type_name = {"chat": "Чат мут", "global": "Глобальный мут", "voice": "Голосовой мут"}[mute_type]
        self.save_mute_to_profile(member.id, mute_time, reason, mute_type_name)

        embed = Embed(
            title="Пользователь замьючен",
            description=f"Пользователь {member.mention} получил(а) **{mute_type_name}** на {time}.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=inter.guild.me.avatar.url)
        embed.add_field(name="Причина", value=reason)
        current_time = datetime.datetime.now(datetime.UTC)
        embed.add_field(name="Время выдачи", value=f"<t:{int(current_time.timestamp())}:F>")
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322584516371550270/user_mute.gif")
        embed.set_footer(
            text=f"Администратор: {inter.user.display_name}",
            icon_url=inter.user.display_avatar.url
        )

        await inter.response.send_message(embed=embed, ephemeral=True)

        try:
            await member.send(embed=embed)
        except disnake.Forbidden:
            print(f"Не удалось отправить сообщение пользователю {member.name} в личные сообщения.")

        action = {"command": mute_type_name, "reason": reason}
        await self.log_action(inter, member, action, unmute_time.strftime('%Y-%m-%d %H:%M:%S UTC'))

        log_mute_channel = self.bot.get_channel(self.log_channel_mute_id)
        if log_mute_channel:
            await log_mute_channel.send(embed=embed)
        else:
            print(f"Канал для логирования мьютов с ID {self.log_channel_mute_id} не найден.")

        await asyncio.sleep(time_timedelta.total_seconds())

        if mute_role in member.roles:
            await member.remove_roles(mute_role)
            unmute_embed = Embed(
                title="Пользователь размьючен",
                description=f"Пользователь {member.mention} был размьючен.\n\n**{mute_type_name} был снят.**",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            unmute_embed.add_field(name="Причина", value=reason)
            current_time = datetime.datetime.now(datetime.UTC)
            unmute_embed.add_field(name="Время снятия", value=f"<t:{int(current_time.timestamp())}:F>")
            unmute_embed.set_thumbnail(url=inter.guild.me.avatar.url)
            unmute_embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322818784138100820/user_unmute.gif")
            unmute_embed.set_footer(
                text=f"Администратор: {inter.user.display_name}",
                icon_url=inter.user.display_avatar.url
            )

            if log_mute_channel:
                await log_mute_channel.send(embed=unmute_embed)
            try:
                await member.send(embed=unmute_embed)
            except disnake.Forbidden:
                print(f"Не удалось отправить сообщение пользователю {member.name} в личные сообщения.")
        else:
            print(f"Пользователь {member.name} уже не имеет роли мьюта.")

    @commands.slash_command(
        name="mute",
        description="Выдать мьют пользователю",
        options=[
            disnake.Option(
                name="mute_type",
                description="Выберите тип мьюта",
                type=disnake.OptionType.string,
                required=True,
                choices=[
                    disnake.OptionChoice(name="Чат мут", value="chat"),
                    disnake.OptionChoice(name="Глобальный мут", value="global"),
                    disnake.OptionChoice(name="Голосовой мут", value="voice")
                ]
            ),
            disnake.Option(
                name="member",
                description="Укажите пользователя, которого нужно замьютить",
                type=disnake.OptionType.user,
                required=True
            ),
            disnake.Option(
                name="time",
                description="Укажите срок мьюта (например, 1m, 2h, 3d)",
                type=disnake.OptionType.string,
                required=True
            ),
            disnake.Option(
                name="reason",
                description="Укажите причину мьюта (можно выбрать или ввести свою)",
                type=disnake.OptionType.string,
                required=True,
                choices=[
                    disnake.OptionChoice(name="[0.0] Своя причина", value="custom_reason"),
                    disnake.OptionChoice(name="[0.0] По решению администрации", value="По решению администрации"),
                    disnake.OptionChoice(name="[1.1] Публикация/трансляция без согласия сторон материалы личного характера", value="[1.1] Публикация/трансляция без согласия сторон материалы личного характера"),
                    disnake.OptionChoice(name="[1.2] Публикация/трансляция материалов 18+", value="[1.2] Публикация/трансляция материалов 18+"),
                    disnake.OptionChoice(name="[1.3] Рекламные/коммерческие ссылки и самореклама", value="[1.3] Рекламные/коммерческие ссылки и самореклама в любом её виде"),
                    disnake.OptionChoice(name="[1.4] Читы", value="[1.4] Читы"),
                    disnake.OptionChoice(name="[1.5] Манипулирование правилами", value="[1.5] Манипулирование правилами сервера в собственных целях"),
                    disnake.OptionChoice(name="[1.6] Обман участников", value="[1.6] Обман других участников"),
                    disnake.OptionChoice(name="[1.7] Продажа/обмен/попрошайничество", value="[1.7] Продажа/обмен/попрошайничество/навязывание услуг"),
                    disnake.OptionChoice(name="[1.8] Помеха развитию сервера", value="[1.8] Помеха развитию сервера"),
                    disnake.OptionChoice(name="[1.9] Обход наказания", value="[1.9] Обход наказания"),
                    disnake.OptionChoice(name="[2.1] Звуковой флуд", value="[2.1] Звуковой флуд"),
                    disnake.OptionChoice(name="[2.2] Сторонние программы", value="[2.2] Использование сторонних программ"),
                    disnake.OptionChoice(name="[2.3] Намеренный слив игр", value="[2.3] Намеренный слив игр"),
                    disnake.OptionChoice(name="[2.4] Вызывающее поведение", value="[2.4] Вызывающее поведение"),
                    disnake.OptionChoice(name="[2.5] Помеха созданию пати", value="[2.5] Помеха созданию пати"),
                    disnake.OptionChoice(name="[3.1] Флуд/Спам", value="[3.1] Флуд/Спам/Медиа флуд"),
                    disnake.OptionChoice(name="[3.2] Оскорбления и провокации", value="[3.2] Оскорбления и провокации"),
                    disnake.OptionChoice(name="[3.3] Каналы не по назначению", value="[3.3] Использование каналов не по назначению"),
                    disnake.OptionChoice(name="[3.4] Запрещённые сообщения", value="[3.4] Запрещённые сообщения - на сервере присутствует автоматическая фильтрация"),
                    disnake.OptionChoice(name="[3.5] Злоупотребление командами", value="[3.5] Злоупотребление командами/упоминанием Staff ролей"),
                    disnake.OptionChoice(name="[4.1] Спам тикетами или репортами", value="[4.1] Спам тикетами или репортами"),
                    disnake.OptionChoice(name="[4.2] Агрессивное обсуждение персонала", value="[4.2] Агрессивное обсуждение действий персонала в общих каналах")
                ]
            )
        ]
    )
    async def mute(self, inter: disnake.ApplicationCommandInteraction, mute_type: str, member: disnake.Member, time: str, reason: str = "По решению администрации"):
        """Выдача роли мьюта на указанное время с выбором типа мьюта."""
        if not any(role.id in self.allowed_roles for role in inter.user.roles) and not inter.user.guild_permissions.administrator:
            embed = Embed(
                title="Ошибка",
                description="**У вас нет прав для использования этой команды ^^**",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        if reason == "custom_reason":
            modal = ReasonModal(self, mute_type, member, time)
            await inter.response.send_modal(modal)
        else:
            await self.mute_user(inter, mute_type, member, time, reason)

def setup(bot):
    bot.add_cog(Mute(bot))