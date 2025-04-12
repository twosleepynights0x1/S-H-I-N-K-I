import disnake
from disnake.ext import commands
import json
import os

class AutoDeleteMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = self._get_channel_id()

    def _get_channel_id(self):
        """Получает ID канала из config.json"""
        config_path = os.path.join('conf', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config["channels"]["logs"]["ScrimRegChannel"]

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.channel.id == self.target_channel_id:
            if not message.author.bot:
                await message.delete()

def setup(bot):
    bot.add_cog(AutoDeleteMessages(bot))