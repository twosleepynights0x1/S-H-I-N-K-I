import disnake
from disnake.ext import commands
from datetime import datetime
import json
import os

class MessageLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join("conf", "config.json")
        self.log_channel_id = self._load_config()

    def _load_config(self):
        """Загружает ID канала для логов удалённых сообщений из конфига."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config["channels"]["logs"]["MessageDelLogChannel"]
        except FileNotFoundError:
            print(f"❌ Ошибка: Конфиг не найден ({self.config_path})")
            return None
        except KeyError:
            print("❌ Ошибка: В конфиге отсутствует MessageDelLogChannel")
            return None
        except json.JSONDecodeError:
            print("❌ Ошибка: Некорректный JSON в конфиге")
            return None

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        if message.author.bot or not message.content:
            return

        if not self.log_channel_id:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if not log_channel:
            return

        embed = disnake.Embed(
            title="🗑️ Сообщение удалено",
            description=(
                f"**Участник:** {message.author.mention}\n"
                f"**ID:** {message.author.id}\n"
                f"**Канал:** {message.channel.mention}\n"
                f"**Удалённое сообщение:**\n```{message.content}```"
            ),
            color=disnake.Color.from_rgb(250, 77, 252),
            timestamp=datetime.now() 
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353787288009707612/standard_23.gif")
        
        await log_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(MessageLogger(bot))