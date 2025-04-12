import disnake
from disnake.ext import commands
import json
import os


CONFIG_PATH = os.path.join('conf', 'config.json')

class Slowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")

        self.admin_roles = config["roles"]["administration"]["AdminRoles"]

        self.log_channel_id = config["channels"]["logs"]["CommandsLogChannel"]

    @commands.slash_command(name="slowmode", description="Установить задержку между сообщениями в канале")
    async def slowmode(
        self, 
        interaction: disnake.ApplicationCommandInteraction, 
        channel: disnake.TextChannel, 
        time: int
    ):
        """Устанавливает задержку между сообщениями в указанном канале."""

        if not any(role.id in self.admin_roles for role in interaction.author.roles) and not interaction.author.guild_permissions.administrator:
            embed = disnake.Embed(
                title="Ошибка",
                description="**У вас нет прав для использования этой команды.**",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if time == 0:
            await channel.edit(slowmode_delay=0)
            embed = disnake.Embed(
                title="Режим замедления отключен!",
                description=f"В канале {channel.mention} была отключена задержка между сообщениями.",
                color=disnake.Color.from_rgb(250, 77, 252)
                )
            action_text = "Режим замедления отключен"
            embed.set_image(url="https://media.discordapp.net/attachments/1257698647064449144/1351221153838137466/standard_1.gif?ex=67d99643&is=67d844c3&hm=60ff29f11d4d6978dde7ccd8e88cc14e6dfbd03e5427f55d7958b0b6ca28e6b1&=")
        else:
            await channel.edit(slowmode_delay=time)
            embed = disnake.Embed(
                title="Режим замедления установлен!",
                description=f"В канале {channel.mention} была установлена задержка между сообщениями: {time} секунд.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1257698647064449144/1351221153838137466/standard_1.gif?ex=67d99643&is=67d844c3&hm=60ff29f11d4d6978dde7ccd8e88cc14e6dfbd03e5427f55d7958b0b6ca28e6b1&=")
            action_text = f"Режим замедления активирован на {time} секунд"

        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(
            text=f"Администратор: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        await interaction.response.send_message(embed=embed)

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            log_embed = disnake.Embed(
                title="Log",
                color=disnake.Color.blue()
            )
            log_embed.add_field(name="Команда:", value="slowmode", inline=False)
            log_embed.add_field(name="Канал:", value=channel.mention, inline=False)
            log_embed.add_field(name="Задержка:", value=f"{time} секунд" if time > 0 else "Отключена", inline=False)
            log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
            log_embed.set_footer(
                text=f"Администратор: {interaction.user.display_name}", 
                icon_url=interaction.user.display_avatar.url
            )
            log_embed.timestamp = interaction.created_at
            
            await log_channel.send(embed=log_embed)
        else:
            print(f"Канал для логирования с ID {self.log_channel_id} не найден.")

def setup(bot):
    bot.add_cog(Slowmode(bot))