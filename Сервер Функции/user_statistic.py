import disnake
from disnake.ext import commands, tasks
import json
import os
import stat
from datetime import datetime
import random
import sys
import traceback

class ActivityTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        module_dir = os.path.abspath(os.path.dirname(__file__))
        project_root = os.path.dirname(module_dir)
        self.stats_file = os.path.join(project_root, "data", "activity_stats.json")

        data_dir = os.path.dirname(self.stats_file)
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception as e:
                print(f"[__init__] Ошибка при создании директории {data_dir}: {e}", flush=True)
                traceback.print_exc()
                raise
        try:
            dir_stat = os.stat(data_dir)
            if not os.access(data_dir, os.W_OK):
                print(f"[__init__] Нет прав на запись в директорию {data_dir}. Попробуйте исправить права доступа.", flush=True)
                raise PermissionError(f"Нет прав на запись в директорию {data_dir}")
        except Exception as e:
            print(f"[__init__] Ошибка при проверке прав доступа к директории {data_dir}: {e}", flush=True)
            traceback.print_exc()
            raise

        self.voice_join_times = {}
        self.max_level = 50

        self.LEVEL_UP_CHANNEL_ID = 1351353917740679270

        self.VOICE_LEVEL_XP = {}
        for level in range(1, 11):
            self.VOICE_LEVEL_XP[level] = 7500
        for level in range(11, 21):
            self.VOICE_LEVEL_XP[level] = 7500
        for level in range(21, 31):
            self.VOICE_LEVEL_XP[level] = 10000
        for level in range(31, 41):
            self.VOICE_LEVEL_XP[level] = 11000
        for level in range(41, 51):
            self.VOICE_LEVEL_XP[level] = 18000

        self.LEVEL_ROLES = {
            1: 1363902795924636002,
            10: 1078684295708815380,
            20: 1363902791546048573,
            30: 1363902786680389702,
            40: 1363902781743955999,
            50: 1363902776589025572,
        }

        self.stats_data = self.load_stats()
        self.update_voice_exp.start()

    def cog_unload(self):
        self.update_voice_exp.cancel()
        self.save_stats(self.stats_data)

    def load_stats(self):
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            stats_data = {}
            self.save_stats(stats_data)
            return stats_data
        except Exception as e:
            print(f"[load_stats] Ошибка при загрузке статистики из {self.stats_file}: {e}", flush=True)
            traceback.print_exc()
            raise

    def save_stats(self, stats_data):
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[save_stats] Ошибка при сохранении статистики в {self.stats_file}: {e}", flush=True)
            traceback.print_exc()
            raise

    def calculate_exp_for_level(self, level: int) -> int:
        if level >= self.max_level:
            return 0
        return self.VOICE_LEVEL_XP.get(level, 0)

    def get_level_info(self, current_exp: int) -> tuple[int, int, int, float]:
        level = 0
        total_exp = current_exp
        cumulative_exp = 0
        while level < self.max_level:
            next_level = level + 1
            exp_needed = self.calculate_exp_for_level(next_level)
            if exp_needed == 0:
                break
            cumulative_exp += exp_needed
            if total_exp < cumulative_exp:
                break
            level += 1
        if level >= self.max_level:
            return level, total_exp - cumulative_exp, 0, 0.0
        next_level_exp = self.calculate_exp_for_level(level + 1)
        progress = (total_exp - (cumulative_exp - exp_needed)) / next_level_exp if next_level_exp > 0 else 0.0
        return level, total_exp - (cumulative_exp - exp_needed), next_level_exp, progress

    def create_xp_bar(self, progress: float) -> str:
        total_length = 16
        filled_length = int(total_length * progress)
        bar = "🟪" * filled_length + "⬜" * (total_length - filled_length)
        return bar

    def decline_noun(self, number: int, forms: tuple[str, str, str]) -> str:
        if number % 100 in [11, 12, 13, 14]:
            return f"{number} {forms[2]}"
        
        last_digit = number % 10
        if last_digit == 1:
            return f"{number} {forms[0]}"
        elif last_digit in [2, 3, 4]:
            return f"{number} {forms[1]}"
        else:
            return f"{number} {forms[2]}"

    def format_time(self, minutes: int) -> str:
        if minutes < 60:
            return f"`{minutes}m`"
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"`{hours}h {remaining_minutes}m`"

    def get_user_rank(self, user_id: int, category_key: str) -> int:
        stats_data = self.stats_data
        sorted_users = sorted(
            stats_data.items(),
            key=lambda x: x[1][category_key],
            reverse=True
        )
        for rank, (uid, _) in enumerate(sorted_users, start=1):
            if uid == str(user_id):
                return rank
        return -1

    async def assign_level_role(self, member: disnake.Member, level: int):
        if level in self.LEVEL_ROLES:
            role_id = self.LEVEL_ROLES[level]
            role = member.guild.get_role(role_id)
            if role and role not in member.roles:
                try:
                    await member.add_roles(role)
                except Exception as e:
                    print(f"[assign_level_role] Ошибка при выдаче роли {role_id} пользователю {member.id}: {e}", flush=True)

    async def send_level_up_message(self, member: disnake.Member, new_level: int):
        channel = self.bot.get_channel(self.LEVEL_UP_CHANNEL_ID)
        if not channel:
            channel = member.guild.system_channel or (await member.guild.text_channels())[0]

        role = None
        if new_level in self.LEVEL_ROLES:
            role_id = self.LEVEL_ROLES[new_level]
            role = member.guild.get_role(role_id)

        if role:
            embed = disnake.Embed(
                title="Повышение уровня ^^",
                description=(
                    f"Пользователь {member.mention}!"
                    f"Достиг **{new_level} уровня**\n"
                    f"Получена роль {role.mention}"
                ),
                color=disnake.Color.from_rgb(250, 77, 252)
            )
        else:
            embed = disnake.Embed(
                title="Повышение уровня ^^",
                description=(
                    f"Пользователь {member.mention}!\n"
                    f"Достиг **{new_level} уровня**"
                ),
                color=disnake.Color.from_rgb(250, 77, 252)
            )

        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1365811390958403707/level_up.gif")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url)

        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"[send_level_up_message] Ошибка при отправке сообщения о повышении уровня для {member.id}: {e}", flush=True)

    async def update_stats(self, user_id: int, messages: int = 0, voice_time: int = 0, member: disnake.Member = None):
        try:
            stats_data = self.load_stats()
        except Exception as e:
            print(f"[update_stats] Ошибка при загрузке статистики: {e}", flush=True)
            traceback.print_exc()
            stats_data = {}

        user_id_str = str(user_id)

        if user_id_str not in stats_data:
            stats_data[user_id_str] = {
                "exp": 0,
                "messages": 0,
                "voice_time": 0,
                "level": 0
            }

        old_level = stats_data[user_id_str]["level"]

        text_exp_gain = messages * random.randint(10, 10)
        voice_exp_gain = (voice_time // 60) * random.randint(4, 4)

        stats_data[user_id_str]["exp"] += text_exp_gain + voice_exp_gain
        stats_data[user_id_str]["messages"] += messages
        stats_data[user_id_str]["voice_time"] += voice_time

        level, _, _, _ = self.get_level_info(stats_data[user_id_str]["exp"])
        stats_data[user_id_str]["level"] = level

        try:
            self.save_stats(stats_data)
            self.stats_data = stats_data
        except Exception as e:
            print(f"[update_stats] Ошибка при сохранении статистики: {e}", flush=True)
            traceback.print_exc()

        if level > old_level and member:
            await self.send_level_up_message(member, level)
            await self.assign_level_role(member, level)

        return text_exp_gain, voice_exp_gain

    @tasks.loop(seconds=60)
    async def update_voice_exp(self):
        current_time = datetime.now()
        for user_id, join_time in list(self.voice_join_times.items()):
            time_spent = int((current_time - join_time).total_seconds())
            if time_spent >= 60:
                member = self.bot.get_user(user_id)
                if member:
                    member = (await self.bot.guilds[0].fetch_member(user_id)) if self.bot.guilds else None
                _, voice_exp = await self.update_stats(user_id, voice_time=time_spent, member=member)
                self.voice_join_times[user_id] = current_time

    @update_voice_exp.before_loop
    async def before_update_voice_exp(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        text_exp, _ = await self.update_stats(message.author.id, messages=1, member=message.author)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.bot:
            return
        current_time = datetime.now()
        user_id = member.id

        if before.channel is None and after.channel is not None:
            self.voice_join_times[user_id] = current_time
        elif before.channel is not None and after.channel is None:
            if user_id in self.voice_join_times:
                join_time = self.voice_join_times[user_id]
                time_spent = int((current_time - join_time).total_seconds())
                if time_spent > 0:
                    _, voice_exp = await self.update_stats(user_id, voice_time=time_spent, member=member)
                del self.voice_join_times[user_id]

    @commands.slash_command(description="Показать уровень участника")
    async def test_level(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        await inter.response.defer()
        
        member = member or inter.author
        stats_data = self.stats_data
        user_id_str = str(member.id)

        if user_id_str not in stats_data:
            await inter.edit_original_response(f"{member.mention} ещё не имеет статистики активности.")
            return

        level, current_exp, exp_needed, progress = self.get_level_info(stats_data[user_id_str]["exp"])
        messages = stats_data[user_id_str]["messages"]
        voice_minutes = stats_data[user_id_str]["voice_time"] // 60

        chat_rank = self.get_user_rank(member.id, "messages")
        voice_rank = self.get_user_rank(member.id, "voice_time")

        description = (
            f"💎 Текущий уровень — **{level}**\n"
            f"⚡ Текущий опыт — **{current_exp}** XP\n"
            f"⚡ Необходимый опыт для следующего уровня — **{exp_needed if level < self.max_level else 'MAX'}** XP\n"
            f"💬 Сообщений отправлено — **{messages}**\n"
            f"🎙️ Время в голосовых каналах — **{self.format_time(voice_minutes)}**\n"
            f"🏅 Место в чат рейтинге — **{chat_rank if chat_rank != -1 else 'N/A'}**\n"
            f"🏅 Место в войс рейтинге — **{voice_rank if voice_rank != -1 else 'N/A'}**\n"
            f"{self.create_xp_bar(progress) if level < self.max_level else 'MAX'}"
        )

        embed = disnake.Embed(
            title="Статистика участника",
            description=description,
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1365810764408950915/level.gif")
        embed.set_footer(
            text=f"Пользователь: {inter.user.display_name}",
            icon_url=inter.user.avatar.url if inter.user.avatar else None
        )

        await inter.edit_original_response(embed=embed)

    @commands.slash_command(description="Показать лидерборд по активности")
    async def test_leaderboard(
        self,
        inter: disnake.ApplicationCommandInteraction,
        category: str = commands.Param(
            choices=["Рейтинг по чату", "Рейтинг по войсу"],
            description="Выберите категорию рейтинга"
        )
    ):
        await inter.response.defer()
        await self.show_leaderboard(inter, category, page=0)

    async def show_leaderboard(self, inter: disnake.MessageInteraction, category: str, page: int):
        stats_data = self.stats_data
        if not stats_data:
            embed = disnake.Embed(
                title="Лидерборд по активности",
                description="Нет данных для отображения лидерборда.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.icon.url if inter.guild.icon else None)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1365811158355021937/leaderboard.gif")
            embed.set_footer(
                text=f"Пользователь: {inter.user.display_name}",
                icon_url=inter.user.avatar.url if inter.user.avatar else None
            )
            await inter.edit_original_response(embed=embed, components=[])
            return

        category_key = "messages" if category == "Рейтинг по чату" else "voice_time"
        category_title = "Рейтинг по сообщениям в чатах" if category == "Рейтинг по чату" else "Рейтинг по активности в войс-каналах"

        sorted_users = sorted(
            stats_data.items(),
            key=lambda x: x[1][category_key],
            reverse=True
        )

        if not sorted_users:
            embed = disnake.Embed(
                title=category_title,
                description="Нет данных для отображения лидерборда.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.icon.url if inter.guild.icon else None)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1365811158355021937/leaderboard.gif")
            embed.set_footer(
                text=f"Пользователь: {inter.user.display_name}",
                icon_url=inter.user.avatar.url if inter.user.avatar else None
            )
            await inter.edit_original_response(embed=embed, components=[])
            return

        page_size = 10
        pages = [sorted_users[i:i + page_size] for i in range(0, len(sorted_users), page_size)]
        if page < 0:
            page = len(pages) - 1
        elif page >= len(pages):
            page = 0
        current_page = pages[page]

        leaderboard_text = ""
        for idx, (user_id, stats) in enumerate(current_page, start=page * page_size + 1):
            member = inter.guild.get_member(int(user_id))
            if not member:
                continue
            metric_value = stats[category_key]
            if category_key == "voice_time":
                metric_value = metric_value // 60
                metric_text = self.format_time(metric_value)
            else:
                metric_text = f"{metric_value}"
            leaderboard_text += f"🏆 **{idx}. {member.display_name}** — `{metric_text}`\n"

        embed = disnake.Embed(
            title=category_title,
            description=leaderboard_text or "Нет данных для этой страницы.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=inter.guild.icon.url if inter.guild.icon else None)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1365811158355021937/leaderboard.gif")
        embed.set_footer(
            text=f"Страница {page + 1} из {len(pages)} | Пользователь: {inter.user.display_name}",
            icon_url=inter.user.avatar.url if inter.user.avatar else None
        )

        components = []
        buttons = []
        category_id = category.replace(" ", "_")
        if page > 0:
            buttons.append(disnake.ui.Button(label="◀", custom_id=f"leaderboard_prev_{category_id}_{page}"))
        buttons.append(disnake.ui.Button(label="🔄", custom_id=f"leaderboard_refresh_{category_id}_{page}"))
        if page < len(pages) - 1:
            buttons.append(disnake.ui.Button(label="▶", custom_id=f"leaderboard_next_{category_id}_{page}"))
        components.append(disnake.ui.ActionRow(*buttons))

        await inter.edit_original_response(embed=embed, components=components)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        try:
            custom_id = inter.component.custom_id
            if custom_id.startswith("leaderboard_prev_") or custom_id.startswith("leaderboard_next_") or custom_id.startswith("leaderboard_refresh_"):
                await inter.response.defer()
                parts = custom_id.split("_")
                action = parts[1]
                page = int(parts[-1])
                category = "_".join(parts[2:-1])
                category = category.replace("_", " ")

                if action == "prev":
                    new_page = page - 1
                elif action == "next":
                    new_page = page + 1
                else:
                    new_page = page

                await self.show_leaderboard(inter, category, new_page)
        except disnake.errors.NotFound:
            await inter.channel.send("Взаимодействие устарело. Пожалуйста, используйте команду заново.", ephemeral=True)
        except Exception as e:
            print(f"[on_button_click] Ошибка: {e}", flush=True)

def setup(bot: commands.Bot):
    bot.add_cog(ActivityTracker(bot))