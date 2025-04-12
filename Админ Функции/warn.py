import disnake
import json
import uuid
import os
from disnake.ext import commands
from datetime import datetime, timedelta

CONFIG_PATH = os.path.join('conf', 'config.json')
WARN_DATA_PATH = os.path.join("data", "warns.json")
PROFILE_DATA_PATH = os.path.join("data", "profiles.json")
MUTE_LIST_PATH = os.path.join("data", "user_mute_list.json")

class ReasonModal(disnake.ui.Modal):
    def __init__(self, cog, member):
        self.cog = cog
        self.member = member
        components = [
            disnake.ui.TextInput(
                label="Введите причину варна",
                custom_id="reason_input",
                style=disnake.TextInputStyle.paragraph,
                placeholder="Укажите причину варна...",
                min_length=1,
                max_length=500
            )
        ]
        super().__init__(title="Укажите свою причину", components=components)

    async def callback(self, modal_inter: disnake.ModalInteraction):
        reason = modal_inter.text_values["reason_input"]
        await self.cog.warn_user(modal_inter, self.member, reason)

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")
        self.MUTE_ROLE_ID = config["roles"]["moderation"]["MuteGlobalRole"]
        self.allowed_roles = config["roles"]["administration"]["AdminRoles"]
        self.LOG_CHANNEL_ID = config["channels"]["logs"]["WarnLogChannel"]

    async def send_to_log_channel(self, embed: disnake.Embed):
        log_channel = self.bot.get_channel(self.LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)

    async def warn_user(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        try:
            with open(WARN_DATA_PATH, "r", encoding="utf-8") as file:
                warns = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            warns = {}
        try:
            with open(PROFILE_DATA_PATH, "r", encoding="utf-8") as file:
                profiles = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            profiles = {}
        user_id = str(member.id)
        warn_id = str(uuid.uuid4())
        warn_entry = {"id": warn_id, "reason": reason, "time": datetime.utcnow().isoformat()}
        if user_id not in warns:
            warns[user_id] = {"current_warns": 0}
        warns[user_id]["current_warns"] += 1
        if user_id not in profiles:
            profiles[user_id] = {"warn_history": []}
        if "warn_history" not in profiles[user_id]:
            profiles[user_id]["warn_history"] = []
        profiles[user_id]["warn_history"].append(warn_entry)
        with open(WARN_DATA_PATH, "w", encoding="utf-8") as file:
            json.dump(warns, file, indent=4, ensure_ascii=False)
        with open(PROFILE_DATA_PATH, "w", encoding="utf-8") as file:
            json.dump(profiles, file, indent=4, ensure_ascii=False)
        embed = disnake.Embed(
            title="Выдан варн",
            description=(f"**Участник:** {member.mention}\n"
                         f"**Причина:** {reason}\n"
                         f"**Всего варнов:** {warns[user_id]['current_warns']}"),
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            embed.set_thumbnail(url=member.default_avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1351375100108341279/standard_5.gif?ex=67da25a3&is=67d8d423&hm=211427879907204f2b63e9bf47f336525fbb8c1d4d4bc9339ef1ba1ac75d5117&=")
        embed.set_footer(
            text=f"Администратор: {inter.user.display_name}",
            icon_url=inter.user.display_avatar.url
        )
        await inter.response.send_message(embed=embed, ephemeral=True)
        try:
            await member.send(embed=embed)
        except disnake.Forbidden:
            await inter.followup.send(f"Не удалось отправить сообщение в ЛС пользователю {member.mention}. Возможно, у него закрыты ЛС.", ephemeral=True)
        await self.send_to_log_channel(embed)
        if warns[user_id]["current_warns"] >= 3:
            mute_time = datetime.utcnow()
            unmute_time = mute_time + timedelta(days=1)
            await member.add_roles(disnake.Object(self.MUTE_ROLE_ID))
            try:
                with open(MUTE_LIST_PATH, "r", encoding="utf-8") as file:
                    mute_list = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                mute_list = []
            mute_list.append({
                "user_id": member.id,
                "mute_time": mute_time.isoformat(),
                "unmute_time": unmute_time.isoformat()
            })
            with open(MUTE_LIST_PATH, "w", encoding="utf-8") as file:
                json.dump(mute_list, file, indent=4)
            del warns[user_id]
            with open(WARN_DATA_PATH, "w", encoding="utf-8") as file:
                json.dump(warns, file, indent=4, ensure_ascii=False)
            mute_embed = disnake.Embed(
                title="Участник получил глобальный мут",
                description=(f"**Участник:** {member.mention}\n"
                             f"**Причина:** Набрано 3 варна\n"
                             f"**Время мута:** 24 часа"),
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            mute_embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1351375100108341279/standard_5.gif?ex=67da25a3&is=67d8d423&hm=211427879907204f2b63e9bf47f336525fbb8c1d4d4bc9339ef1ba1ac75d5117&=")
            if member.avatar:
                mute_embed.set_thumbnail(url=member.avatar.url)
            else:
                mute_embed.set_thumbnail(url=member.default_avatar.url)
            await inter.followup.send(embed=mute_embed, ephemeral=True)
            try:
                await member.send(embed=mute_embed)
            except disnake.Forbidden:
                await inter.followup.send(f"Не удалось отправить сообщение в ЛС пользователю {member.mention}. Возможно, у него закрыты ЛС.", ephemeral=True)
            await self.send_to_log_channel(mute_embed)

    @commands.slash_command(
        name="warn",
        description="Выдать предупреждение участнику",
        options=[
            disnake.Option(
                name="member",
                description="Укажите пользователя, для варна",
                type=disnake.OptionType.user,
                required=True
            ),
            disnake.Option(
                name="reason",
                description="Укажите причину варна",
                type=disnake.OptionType.string,
                required=True,
                choices=[
                    disnake.OptionChoice(name="[0.0] Своя причина", value="custom_reason"),
                    disnake.OptionChoice(name="[0.0] По решению администрации", value="По решению администрации"),
                    disnake.OptionChoice(name="[1.3] Рекламные/коммерческие ссылки и самореклама", value="[1.3] Рекламные/коммерческие ссылки и самореклама в любом её виде"),
                    disnake.OptionChoice(name="[1.4] Читы", value="[1.4] Читы"),
                    disnake.OptionChoice(name="[1.5] Манипулирование правилами", value="[1.5] Манипулирование правилами сервера в собственных целях"),
                    disnake.OptionChoice(name="[1.6] Обман участников", value="[1.6] Обман других участников"),
                    disnake.OptionChoice(name="[1.7] Продажа/обмен/попрошайничество", value="[1.7] Продажа/обмен/попрошайничество/навязывание услуг"),
                    disnake.OptionChoice(name="[2.1] Звуковой флуд", value="[2.1] Звуковой флуд"),
                    disnake.OptionChoice(name="[2.4] Вызывающее поведение", value="[2.4] Вызывающее поведение"),
                    disnake.OptionChoice(name="[2.5] Помеха созданию пати", value="[2.5] Помеха созданию пати"),
                    disnake.OptionChoice(name="[3.1] Флуд/Спам/Медиа флуд", value="[3.1] Флуд/Спам/Медиа флуд"),
                    disnake.OptionChoice(name="[3.2] Оскорбления и провокации", value="[3.2] Оскорбления и провокации"),
                    disnake.OptionChoice(name="[3.3] Каналы не по назначению", value="[3.3] Использование каналов не по назначению"),
                    disnake.OptionChoice(name="[3.4] Запрещённые сообщения", value="[3.4] Запрещённые сообщения"),
                    disnake.OptionChoice(name="[3.5] Злоупотребление командами", value="[3.5] Злоупотребление командами/упоминанием Staff ролей")
                ]
            )
        ]
    )
    async def warn(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        if not any(role.id in self.allowed_roles for role in inter.user.roles) and not inter.user.guild_permissions.administrator:
            embed = disnake.Embed(
                title="Ошибка",
                description="**У вас нет прав для использования этой команды**",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        if reason == "custom_reason":
            modal = ReasonModal(self, member)
            await inter.response.send_modal(modal)
        else:
            await self.warn_user(inter, member, reason)

    @commands.slash_command(
        name="unwarn",
        description="Снять последнее предупреждение с участника",
        options=[
            disnake.Option(
                name="member",
                description="Укажите пользователя, для снятия варна",
                type=disnake.OptionType.user,
                required=True
            )
        ]
    )
    async def unwarn(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        if not any(role.id in self.allowed_roles for role in inter.user.roles) and not inter.user.guild_permissions.administrator:
            embed = disnake.Embed(
                title="Ошибка",
                description="**У вас нет прав для использования этой команды**",
                color=disnake.Color.from_rgb(250, 77, 252))
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        try:
            with open(WARN_DATA_PATH, "r", encoding="utf-8") as file:
                warns = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            warns = {}
        try:
            with open(PROFILE_DATA_PATH, "r", encoding="utf-8") as file:
                profiles = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            profiles = {}
        user_id = str(member.id)
        if user_id not in warns or warns[user_id]["current_warns"] == 0:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"**У участника {member.mention} нет варнов**",
                color=disnake.Color.from_rgb(250, 77, 252))
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            else:
                embed.set_thumbnail(url=member.default_avatar.url)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        warns[user_id]["current_warns"] -= 1
        with open(WARN_DATA_PATH, "w", encoding="utf-8") as file:
            json.dump(warns, file, indent=4, ensure_ascii=False)
        embed = disnake.Embed(
            title="Снят варн",
            description=(f"**Участник:** {member.mention}\n"
                         f"**Всего варнов:** {warns[user_id]['current_warns']}"),
            color=disnake.Color.from_rgb(250, 77, 252))
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            embed.set_thumbnail(url=member.default_avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352018538021392486/standard_7.gif?ex=67dc7ce2&is=67db2b62&hm=134b689a8e7369a5e4898abe9580407da4de268448d7055fdca54d291d088865&=")
        embed.set_footer(
            text=f"Администратор: {inter.user.display_name}",
            icon_url=inter.user.display_avatar.url
        )
        await inter.response.send_message(embed=embed, ephemeral=True)
        try:
            await member.send(embed=embed)
        except disnake.Forbidden:
            await inter.followup.send(f"Не удалось отправить сообщение в ЛС пользователю {member.mention}. Возможно, у него закрыты ЛС.", ephemeral=True)
        await self.send_to_log_channel(embed)

def setup(bot):
    bot.add_cog(Warn(bot))