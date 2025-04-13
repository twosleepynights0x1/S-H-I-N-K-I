import disnake
from disnake.ext import commands
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

class RoleTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.roles_file = Path("data/user_roles.json")
        self.mute_list_file = Path("data/user_mute_list.json")
        CONFIG_PATH = os.path.join('conf', 'config.json')
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")
        self.role_log_channel_id = config["channels"]["logs"]["RecoveryLogChannel"]
        self.admin_roles = config["roles"]["administration"]["AdminRoles"]
        self.mute_roles = [
            config["roles"]["moderation"]["MuteChatRole"],
            config["roles"]["moderation"]["MuteGlobalRole"],
            config["roles"]["moderation"]["MuteVoiceRole"]
        ]
        self.roles_file.parent.mkdir(exist_ok=True, parents=True)
        if not self.roles_file.exists():
            with open(self.roles_file, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False)
        self.load_roles()

    def load_roles(self):
        try:
            with open(self.roles_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке ролей: {e}")
            return {}

    def save_roles(self, roles_data):
        try:
            with open(self.roles_file, "w", encoding="utf-8") as f:
                json.dump(roles_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении ролей: {e}")

    def load_mute_list(self):
        try:
            with open(self.mute_list_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке списка мутов: {e}")
            return []

    async def update_roles(self, member: disnake.Member):
        if member.bot:
            return
        roles_data = self.load_roles()
        role_ids = [role.id for role in member.roles if role.id != member.guild.id and role.id not in self.admin_roles]
        roles_data[str(member.id)] = role_ids
        self.save_roles(roles_data)

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                await self.update_roles(member)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        if member.bot:
            return
        roles_data = self.load_roles()
        user_id = str(member.id)
        if user_id in roles_data:
            role_ids = roles_data[user_id]
            roles_to_assign = [member.guild.get_role(role_id) for role_id in role_ids if member.guild.get_role(role_id)]
            mute_list = self.load_mute_list()
            mute_entry = next((entry for entry in mute_list if entry["user_id"] == member.id), None)
            mute_roles_to_assign = []
            if mute_entry:
                unmute_time = datetime.fromisoformat(mute_entry["unmute_time"])
                if unmute_time > datetime.now():
                    remaining_time = (unmute_time - datetime.now()).total_seconds()
                    mute_roles_to_assign = [member.guild.get_role(role_id) for role_id in self.mute_roles if member.guild.get_role(role_id)]
                    roles_to_assign = [role for role in roles_to_assign if role.id not in self.mute_roles]
            try:
                if roles_to_assign:
                    await member.add_roles(*roles_to_assign, reason="Восстановление ролей после возвращения на сервер")
                if mute_roles_to_assign:
                    await member.add_roles(*mute_roles_to_assign, reason=f"Восстановление мута на оставшееся время: {int(remaining_time)} секунд")
                    self.bot.loop.create_task(self.schedule_unmute(member, remaining_time, mute_roles_to_assign))
                log_channel = member.guild.get_channel(self.role_log_channel_id)
                if log_channel:
                    description = f"Пользователь {member.mention} вернулся на сервер.\n"
                    description += f"Восстановлены роли: {', '.join(f'<@&{role.id}>' for role in roles_to_assign) or 'Нет ролей'}\n"
                    if mute_roles_to_assign:
                        description += f"Восстановлены мут-роли: {', '.join(f'<@&{role.id}>' for role in mute_roles_to_assign)} на {int(remaining_time)} секунд"
                    embed = disnake.Embed(
                        title="Роли восстановлены",
                        description=description,
                        color=disnake.Color.from_rgb(250, 77, 252)
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text=f"ID: {member.id}")
                    await log_channel.send(embed=embed)
            except Exception as e:
                print(f"Ошибка при восстановлении ролей для {member.id}: {e}")
                log_channel = member.guild.get_channel(self.role_log_channel_id)
                if log_channel:
                    embed = disnake.Embed(
                        title="Ошибка восстановления ролей",
                        description=f"Не удалось восстановить роли для {member.mention}: {e}",
                        color=disnake.Color.from_rgb(250, 77, 252)
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text=f"ID: {member.id}")
                    await log_channel.send(embed=embed)
        await self.update_roles(member)

    async def schedule_unmute(self, member: disnake.Member, duration: float, mute_roles: list):
        await disnake.utils.sleep_until(datetime.now() + timedelta(seconds=duration))
        try:
            await member.remove_roles(*mute_roles, reason="Истёк срок мута")
            log_channel = member.guild.get_channel(self.role_log_channel_id)
            if log_channel:
                embed = disnake.Embed(
                    title="Мут снят",
                    description=f"С пользователя {member.mention} автоматически снят мут.",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"ID: {member.id}")
                await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Ошибка при снятии мута с {member.id}: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        if member.bot:
            return
        roles_data = self.load_roles()
        if str(member.id) in roles_data:
            log_channel = member.guild.get_channel(self.role_log_channel_id)
            if log_channel:
                role_ids = roles_data[str(member.id)]
                embed = disnake.Embed(
                    title="Роли сохранены",
                    description=f"Пользователь {member.mention} покинул сервер. Сохранены роли: {', '.join(f'<@&{role_id}>' for role_id in role_ids) or 'Нет ролей'}",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"ID: {member.id}")
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        if before.bot:
            return
        if before.roles != after.roles:
            await self.update_roles(after)

def setup(bot: commands.Bot):
    bot.add_cog(RoleTracker(bot))