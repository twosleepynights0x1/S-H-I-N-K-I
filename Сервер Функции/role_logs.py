import disnake
from disnake.ext import commands
from datetime import datetime
import json
import os

class RoleTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join("conf", "config.json")
        self.log_channel_id = self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config["channels"]["logs"]["RoleLogChannel"]
        except FileNotFoundError:
            print(f"❌ Ошибка: Файл конфигурации не найден по пути {self.config_path}")
            return None
        except KeyError:
            print("❌ Ошибка: В конфиге отсутствует RoleLogChannel")
            return None
        except json.JSONDecodeError:
            print("❌ Ошибка: Некорректный JSON в конфиге")
            return None

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        if before.roles == after.roles:
            return

        if not self.log_channel_id:
            return

        channel = self.bot.get_channel(self.log_channel_id)
        if not channel:
            return

        added = [r for r in after.roles if r not in before.roles]
        removed = [r for r in before.roles if r not in after.roles]

        if added:
            embed = disnake.Embed(
                title="Роль выдана участнику",
                description=(
                    f"**Участник:** {after.mention}\n"
                    f"**ID:** {after.id}\n"
                    f"**Выданные роли:** {', '.join([r.mention for r in added])}"
                ),
                color=disnake.Color.from_rgb(250, 77, 252),
                timestamp=datetime.now()
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353783682451902607/standard_21.gif")
            embed.set_thumbnail(url=after.display_avatar.url)
            await channel.send(embed=embed)

        if removed:
            embed = disnake.Embed(
                title="Роль удалена у участника",
                description=(
                    f"**Участник:** {after.mention}\n"
                    f"**ID:** {after.id}\n"
                    f"**Удаленные роли:** {', '.join([r.mention for r in removed])}"
                ),
                color=disnake.Color.from_rgb(250, 77, 252),
                timestamp=datetime.now()
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1353783988376047708/standard_22.gif")
            embed.set_thumbnail(url=after.display_avatar.url)
            await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(RoleTracker(bot))