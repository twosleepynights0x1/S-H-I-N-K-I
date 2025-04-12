import disnake
from disnake.ext import commands, tasks
from disnake import Embed
import datetime
import json
import os

CONFIG_PATH = os.path.join('conf', 'config.json')

MUTE_LIST_FILE = os.path.join('data', 'user_mute_list.json')

class UnmuteChecker(commands.Cog):
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

        self.log_channel_id = config["channels"]["logs"]["MuteLogChannel"]

        self.unmute_checker.start()

    def cog_unload(self):
        self.unmute_checker.cancel()

    async def send_unmute_embeds(self, member, guild):
        user_embed = Embed(
            title="🔊 Ваш мьют снят",
            description="Все ограничения с вашего аккаунта сняты.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        user_embed.set_footer(text=f"Сервер: {guild.name}")

        log_embed = Embed(
            title="Пользователь размучен",
            description=f"С пользователя {member.mention} сняты все роли мьюта.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        log_embed.set_thumbnail(url=guild.me.avatar.url)  # Аватар бота справа сверху
        log_embed.set_footer(text=f"ID пользователя: {member.id}")
        log_embed.set_image(url="https://media.discordapp.net/attachments/1257698647064449144/1351236844662034574/standard_2.gif")

        try:
            await member.send(embed=user_embed)
        except disnake.HTTPException:
            pass

        log_channel = guild.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(embed=log_embed)

    @tasks.loop(minutes=1) 
    async def unmute_checker(self):
        if not os.path.exists(MUTE_LIST_FILE):
            return

        with open(MUTE_LIST_FILE, 'r', encoding='utf-8') as f:
            try:
                mute_list = json.load(f)
            except json.JSONDecodeError:
                mute_list = []

        current_time = datetime.datetime.utcnow()
        updated_mute_list = []

        for mute_data in mute_list:
            user_id = mute_data["user_id"]
            unmute_time = datetime.datetime.fromisoformat(mute_data["unmute_time"])

            if current_time < unmute_time:
                updated_mute_list.append(mute_data)
                continue

            for guild in self.bot.guilds:
                member = guild.get_member(user_id)
                if member:
                    removed_any = False
                    for role_id in self.mute_role_ids:
                        mute_role = guild.get_role(role_id)
                        if mute_role and mute_role in member.roles:
                            await member.remove_roles(mute_role)
                            removed_any = True
                            print(f"Автоматически снят мьют с пользователя {member.name} ({member.id}) на сервере {guild.name}.")

                    if removed_any:
                        await self.send_unmute_embeds(member, guild)

        with open(MUTE_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_mute_list, f, indent=4)

    @unmute_checker.before_loop
    async def before_unmute_checker(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(UnmuteChecker(bot))