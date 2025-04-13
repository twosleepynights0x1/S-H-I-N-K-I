import disnake
from disnake.ext import commands
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

class ActivityTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stats_file = Path("data/activity_stats.json")
        self.stats_file.parent.mkdir(exist_ok=True, parents=True)
        self.voice_join_times = {}
        if not self.stats_file.exists():
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False)
        self.load_stats()

    def load_stats(self):
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке статистики: {e}")
            return {}

    def save_stats(self, stats_data):
        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении статистики: {e}")

    def get_current_month(self):
        return datetime.now().strftime("%Y-%m")

    def update_stats(self, user_id: int, messages: int = 0, voice_time: int = 0):
        stats_data = self.load_stats()
        user_id_str = str(user_id)
        current_month = self.get_current_month()
        if user_id_str not in stats_data:
            stats_data[user_id_str] = {}
        if current_month not in stats_data[user_id_str]:
            stats_data[user_id_str][current_month] = {"messages": 0, "voice_time": 0}
        stats_data[user_id_str][current_month]["messages"] += messages
        stats_data[user_id_str][current_month]["voice_time"] += voice_time
        self.save_stats(stats_data)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        self.update_stats(message.author.id, messages=1)
        print(f"{datetime.now()}: Пользователь {message.author.id} отправил сообщение. Обновлена статистика.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.bot:
            return
        current_time = datetime.now()
        user_id = member.id
        if before.channel is None and after.channel is not None:
            self.voice_join_times[user_id] = current_time
            print(f"{current_time}: Пользователь {user_id} присоединился к голосовому каналу {after.channel.id}.")
        elif before.channel is not None and after.channel is None:
            if user_id in self.voice_join_times:
                join_time = self.voice_join_times[user_id]
                time_spent = int((current_time - join_time).total_seconds())
                self.update_stats(user_id, voice_time=time_spent)
                print(f"{current_time}: Пользователь {user_id} покинул голосовой канал. Проведено времени: {time_spent} секунд.")
                del self.voice_join_times[user_id]

def setup(bot: commands.Bot):
    bot.add_cog(ActivityTracker(bot))