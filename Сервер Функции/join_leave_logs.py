import disnake
from disnake.ext import commands
import json
import os

class MemberLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = self._get_channel_id()

    def _get_channel_id(self):
        try:
            config_path = os.path.join('conf', 'config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config["channels"]["logs"]["JoinLeaveLogChannel"]
        except:
            return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.log_channel_id)
        if channel:
            embed = disnake.Embed(
                title="Участник присоединился",
                description=(
                    f"**Тэг:** {member} ({member.mention})\n"
                    f"**Никнейм:** {member.display_name}\n"
                    f"**UUID:** {member.id}"
                ),
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            else:
                embed.set_thumbnail(url=member.default_avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352293701589799054/standard_8.gif?ex=67dd7d26&is=67dc2ba6&hm=bd734191642fcd63515b3d8a8a3a6b22c85ecf3a259330eb07e8b82fc04103d7&=&width=1424&height=82")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = self.bot.get_channel(self.log_channel_id)
        if channel:
            embed = disnake.Embed(
                title="Участник покинул сервер",
                description=(
                    f"**Тэг:** {member} ({member.mention})\n"
                    f"**Никнейм:** {member.display_name}\n"
                    f"**UUID:** {member.id}"
                ),
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            else:
                embed.set_thumbnail(url=member.default_avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352294092641533962/standard_9.gif?ex=67dd7d84&is=67dc2c04&hm=801372e8f7f3fc7b24d7569a64a34b73a62afab651d0923bcca38ff1d52f6ff5&=&width=1424&height=82")
            await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(MemberLogs(bot))