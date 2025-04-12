import disnake
from disnake.ext import commands
from disnake import Embed
import os
import json

CONFIG_PATH = os.path.join('conf', 'config.json')

class ClearMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")

        self.allowed_roles = config["roles"]["administration"]["AdminRoles"]

        self.log_channel_id = config["channels"]["logs"]["CommandsLogChannel"]

    async def log_action(self, interaction, channel, action):
        log_channel = self.bot.get_channel(self.log_channel_id)

        if log_channel:
            try:
                log_embed = disnake.Embed(
                    title="Log",
                    color=disnake.Color.blue()
                )
                log_embed.add_field(name="Команда:", value=action["command"], inline=False)
                log_embed.add_field(name="Канал:", value=channel.mention, inline=False)
                log_embed.add_field(name="Удалено сообщений:", value=str(action["deleted_count"]), inline=False)
                log_embed.set_thumbnail(url=interaction.user.display_avatar.url)
                log_embed.set_footer(
                    text=f"Администратор: {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url
                )
                log_embed.timestamp = interaction.created_at

                await log_channel.send(embed=log_embed)
                print(f"Лог отправлен: {action['command']} для канала {channel.name}")
            except Exception as e:
                print(f"Ошибка при отправке лога: {e}")
                await interaction.followup.send("Не удалось отправить лог в канал.", ephemeral=True)
        else:
            print(f"Канал для логирования с ID {self.log_channel_id} не найден.")
            await interaction.followup.send("Канал для логирования не найден.", ephemeral=True)

    @commands.slash_command(name="clear", description="Удалить указанное количество сообщений в текущем канале")
    async def clear(
        self, 
        interaction: disnake.ApplicationCommandInteraction, 
        amount: int
    ):
        
        await interaction.response.defer()

        if not any(role.id in self.allowed_roles for role in interaction.user.roles) and not interaction.user.guild_permissions.administrator:
            embed = Embed(
                title="Ошибка",
                description=f"**У вас нет прав для использования этой команды ^^**",
                color=disnake.Color.from_rgb(250, 77, 252))
            embed.set_thumbnail(url=interaction.guild.me.avatar.url)  # Аватар бота справа сверху
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if amount < 1 or amount > 100:
            embed = Embed(
                title="Ошибка",
                description=f"**Количество сообщений должно быть от 1 до 100.**",
                color=disnake.Color.from_rgb(250, 77, 252))
            embed.set_thumbnail(url=interaction.guild.me.avatar.url)  # Аватар бота справа сверху
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        deleted = await interaction.channel.purge(limit=amount)

        embed = disnake.Embed(
            title="Канал очищен!",
            description=f"В канале {interaction.channel.mention} было удалено {len(deleted)} сообщений.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1257698647064449144/1351215051410767995/standard.gif?ex=67d99094&is=67d83f14&hm=70459af376e908cfea056e5d55542b8142ef95115e910626a1f2335b95162bbf&=")
        embed.set_footer(
            text=f"Администратор: {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        await interaction.followup.send(embed=embed)
        action = {
            "command": "clear",         
            "deleted_count": len(deleted) 
        }
        await self.log_action(interaction, interaction.channel, action)  
        
def setup(bot):
    bot.add_cog(ClearMessages(bot))