import disnake
from disnake.ext import commands
from disnake import Embed
import json
import os

CONFIG_PATH = os.path.join('conf', 'config.json')
MUTE_LIST_FILE = os.path.join('data', 'user_mute_list.json')

class UnmuteCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")
        
        self.mute_role_ids = [
            config["roles"]["moderation"]["MuteGlobalRole"],  # Global Mute
            config["roles"]["moderation"]["MuteVoiceRole"],   # Voice Mute
            config["roles"]["moderation"]["MuteChatRole"]     # Chat Mute
        ]

        self.allowed_roles = config["roles"]["administration"]["AdminRoles"]

        self.log_channel_id = config["channels"]["logs"]["CommandsLogChannel"]
        self.notification_channel_id = config["channels"]["logs"]["MuteLogChannel"]

    async def log_action(self, interaction, member, action):
        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            try:
                log_embed = Embed(
                    title="Log",
                    color=disnake.Color.blue()
                )
                log_embed.add_field(name="Команда:", value=action["command"], inline=False)
                log_embed.add_field(name="Пользователь:", value=member.mention, inline=False)

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
            await interaction.followup.send("Канал для логирования не найден.", ephemeral=True)

    async def send_unmute_embed(self, interaction, member):
        embed = Embed(
            title="Пользователь размучен",
            description=f"С пользователя {member.mention} сняты все роли мьюта.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=interaction.guild.me.avatar.url) 
        embed.set_footer(text=f"Администратор: {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1257698647064449144/1351236844662034574/standard_2.gif?ex=67d9a4e0&is=67d85360&hm=5f338b6aaca2631d11c82009702a1ff6b0c7b18163c4af7cd3869c1d3af29c01&=")

        notification_channel = self.bot.get_channel(self.notification_channel_id)
        if notification_channel:
            await notification_channel.send(embed=embed)
        else:
            print(f"Канал для уведомлений с ID {self.notification_channel_id} не найден.")
        try:
            await member.send(embed=embed)
        except disnake.Forbidden:
            print(f"Не удалось отправить сообщение в ЛС пользователю {member.name}.")
            await interaction.followup.send(f"Не удалось отправить сообщение в ЛС пользователю {member.mention}.", ephemeral=True)

    @commands.slash_command(
        name="unmute",
        description="Размьют участника",
        options=[
            disnake.Option(
                name="member",
                description="Укажите пользователя, которого нужно размьютить.",
                type=disnake.OptionType.user,
                required=True
            )
        ]
    )
    async def unmute(self, inter, member: disnake.Member):
        if not any(role.id in self.allowed_roles for role in inter.user.roles) and not inter.user.guild_permissions.administrator:
            embed = Embed(
                title="Ошибка",
                description=f"**У вас нет прав для использования этой команды ^^**",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url) 
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await inter.send(embed=embed, ephemeral=True)
            return

        roles_to_remove = []
        for role_id in self.mute_role_ids:
            role = inter.guild.get_role(role_id)
            if role and role in member.roles:
                roles_to_remove.append(role)

        if not roles_to_remove:
            await inter.send(f"{member.mention} не имеет ролей мьюта.", ephemeral=True)
            return

        await member.remove_roles(*roles_to_remove)

        if os.path.exists(MUTE_LIST_FILE):
            with open(MUTE_LIST_FILE, 'r', encoding='utf-8') as f:
                try:
                    mute_list = json.load(f)
                except json.JSONDecodeError:
                    mute_list = []
        else:
            mute_list = []

        updated_mute_list = [mute_data for mute_data in mute_list if mute_data["user_id"] != member.id]

        with open(MUTE_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_mute_list, f, indent=4)

        embed = Embed(
            title="Пользователь размучен",
            description=f"С пользователя {member.mention} сняты все роли мьюта.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=inter.guild.me.avatar.url)
        embed.set_footer(text=f"Администратор: {inter.user.name}", icon_url=inter.user.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1257698647064449144/1351236844662034574/standard_2.gif?ex=67d9a4e0&is=67d85360&hm=5f338b6aaca2631d11c82009702a1ff6b0c7b18163c4af7cd3869c1d3af29c01&=")
        await inter.send(embed=embed, ephemeral=True)

        action = {
            "command": "Unmute", 
        }
        await self.log_action(inter, member, action)

        await self.send_unmute_embed(inter, member)

def setup(bot):
    bot.add_cog(UnmuteCommand(bot))