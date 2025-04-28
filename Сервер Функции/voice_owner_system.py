import disnake
from disnake.ext import commands
import json
import os
import stat
import traceback
import asyncio

class VoiceManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        module_dir = os.path.abspath(os.path.dirname(__file__))
        project_root = os.path.dirname(module_dir)
        self.voice_owners_file = os.path.join(project_root, "data", "voice_owners.json")
        self.log_channel_id = 1366185256075530291 
        self.kick_log_channel_id = 1366418566630346813  # Новый канал для логов кика
        self.excluded_channels = {
            597379133852352513,
            1364302960166961194,
            768380694057451540,
            1312137151139418143
        }

        data_dir = os.path.dirname(self.voice_owners_file)
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except Exception as e:
                print(f"[VoiceManager __init__] Ошибка при создании директории {data_dir}: {e}", flush=True)
                traceback.print_exc()
                raise
        try:
            dir_stat = os.stat(data_dir)
            if not os.access(data_dir, os.W_OK):
                print(f"[VoiceManager __init__] Нет прав на запись в директорию {data_dir}. Попробуйте исправить права доступа.", flush=True)
                raise PermissionError(f"Нет прав на запись в директорию {data_dir}")
        except Exception as e:
            print(f"[VoiceManager __init__] Ошибка при проверке прав доступа к директории {data_dir}: {e}", flush=True)
            traceback.print_exc()
            raise

        self.voice_owners = self.load_voice_owners()

    def cog_unload(self):
        self.save_voice_owners(self.voice_owners)

    def load_voice_owners(self):
        try:
            with open(self.voice_owners_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            voice_owners = {}
            self.save_voice_owners(voice_owners)
            return voice_owners
        except Exception as e:
            print(f"[VoiceManager load_voice_owners] Ошибка при загрузке владельцев голосовых каналов из {self.voice_owners_file}: {e}", flush=True)
            traceback.print_exc()
            raise

    def save_voice_owners(self, voice_owners):
        try:
            os.makedirs(os.path.dirname(self.voice_owners_file), exist_ok=True)
            with open(self.voice_owners_file, "w", encoding="utf-8") as f:
                json.dump(voice_owners, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[VoiceManager save_voice_owners] Ошибка при сохранении владельцев голосовых каналов в {self.voice_owners_file}: {e}", flush=True)
            traceback.print_exc()
            raise

    async def restrict_channel_access(self, member: disnake.Member, voice_channel: disnake.VoiceChannel):
        try:
            await voice_channel.set_permissions(member, connect=False)
            await asyncio.sleep(600)  # 10 минут
            await voice_channel.set_permissions(member, connect=None)
        except disnake.Forbidden:
            print(f"[VoiceManager restrict_channel_access] Нет прав для изменения разрешений канала {voice_channel.name} для {member.display_name}", flush=True)
        except Exception as e:
            print(f"[VoiceManager restrict_channel_access] Ошибка при ограничении доступа к каналу: {e}", flush=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.bot:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if not log_channel:
            print(f"[VoiceManager on_voice_state_update] Лог-канал с ID {self.log_channel_id} не найден.", flush=True)
            return

        if before.channel is None and after.channel is not None:
            channel_id = str(after.channel.id)

            if after.channel.id in self.excluded_channels:
                return
            if channel_id not in self.voice_owners:
                members_in_channel = after.channel.members  
                if len(members_in_channel) == 1:
                    self.voice_owners[channel_id] = str(member.id)
                    self.save_voice_owners(self.voice_owners)
                    embed = disnake.Embed(
                        title="Новый владелец канала",
                        description=f"{member.mention} стал владельцем голосового канала **{after.channel.name}**!",
                        color=disnake.Color.from_rgb(250, 77, 252)
                    )
                    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                    embed.set_footer(
                        text=f"Пользователь: {member.display_name}",
                        icon_url=member.avatar.url if member.avatar else member.default_avatar.url
                    )
                    try:
                        await log_channel.send(embed=embed)
                    except Exception as e:
                        print(f"[VoiceManager on_voice_state_update] Ошибка при отправке сообщения о новом владельце: {e}", flush=True)

        elif before.channel is not None and after.channel is not None:
            if before.channel == after.channel:
                return

            old_channel_id = str(before.channel.id)
            if before.channel.id in self.excluded_channels:
                pass
            elif old_channel_id in self.voice_owners:
                was_owner = self.voice_owners[old_channel_id] == str(member.id)
                if was_owner:
                    members_in_channel = before.channel.members
                    if members_in_channel:
                        new_owner = members_in_channel[0]
                        self.voice_owners[old_channel_id] = str(new_owner.id)
                        self.save_voice_owners(self.voice_owners)
                        embed = disnake.Embed(
                            title="Новый владелец канала",
                            description=f"{new_owner.mention} стал новым владельцем канала **{before.channel.name}** после ухода {member.mention}!",
                            color=disnake.Color.from_rgb(250, 77, 252)
                        )
                        embed.set_thumbnail(url=new_owner.avatar.url if new_owner.avatar else new_owner.default_avatar.url)
                        embed.set_footer(
                            text=f"Пользователь: {new_owner.display_name}",
                            icon_url=new_owner.avatar.url if new_owner.avatar else new_owner.default_avatar.url
                        )
                        try:
                            await log_channel.send(embed=embed)
                        except Exception as e:
                            print(f"[VoiceManager on_voice_state_update] Ошибка при отправке сообщения о новом владельце: {e}", flush=True)
                    else:
                        del self.voice_owners[old_channel_id]
                        self.save_voice_owners(self.voice_owners)
                        embed = disnake.Embed(
                            title="Владелец покинул канал",
                            description=f"{member.mention} покинул канал **{before.channel.name}** и больше не является владельцем.",
                            color=disnake.Color.from_rgb(250, 77, 252)
                        )
                        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                        embed.set_footer(
                            text=f"Пользователь: {member.display_name}",
                            icon_url=member.avatar.url if member.avatar else member.default_avatar.url
                        )
                        try:
                            await log_channel.send(embed=embed)
                        except Exception as e:
                            print(f"[VoiceManager on_voice_state_update] Ошибка при отправке сообщения о сбросе владельца: {e}", flush=True)

            new_channel_id = str(after.channel.id)
            if after.channel.id in self.excluded_channels:
                return
            if new_channel_id not in self.voice_owners:
                members_in_channel = after.channel.members 
                if len(members_in_channel) == 1:
                    self.voice_owners[new_channel_id] = str(member.id)
                    self.save_voice_owners(self.voice_owners)
                    embed = disnake.Embed(
                        title="Новый владелец канала",
                        description=f"{member.mention} стал владельцем голосового канала **{after.channel.name}**!",
                        color=disnake.Color.from_rgb(250, 77, 252)
                    )
                    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                    embed.set_footer(
                        text=f"Пользователь: {member.display_name}",
                        icon_url=member.avatar.url if member.avatar else member.default_avatar.url
                    )
                    try:
                        await log_channel.send(embed=embed)
                    except Exception as e:
                        print(f"[VoiceManager on_voice_state_update] Ошибка при отправке сообщения о новом владельце: {e}", flush=True)

        elif before.channel is not None and after.channel is None:
            channel_id = str(before.channel.id)
            if before.channel.id in self.excluded_channels:
                return
            if channel_id in self.voice_owners:
                was_owner = self.voice_owners[channel_id] == str(member.id)
                if was_owner:
                    members_in_channel = before.channel.members 
                    if members_in_channel:
                        new_owner = members_in_channel[0]
                        self.voice_owners[channel_id] = str(new_owner.id)
                        self.save_voice_owners(self.voice_owners)
                        embed = disnake.Embed(
                            title="Новый владелец канала",
                            description=f"{new_owner.mention} стал новым владельцем канала **{before.channel.name}** после ухода {member.mention}!",
                            color=disnake.Color.from_rgb(250, 77, 252)
                        )
                        embed.set_thumbnail(url=new_owner.avatar.url if new_owner.avatar else new_owner.default_avatar.url)
                        embed.set_footer(
                            text=f"Пользователь: {new_owner.display_name}",
                            icon_url=new_owner.avatar.url if new_owner.avatar else new_owner.default_avatar.url
                        )
                        try:
                            await log_channel.send(embed=embed)
                        except Exception as e:
                            print(f"[VoiceManager on_voice_state_update] Ошибка при отправке сообщения о новом владельце: {e}", flush=True)
                    else:
                        del self.voice_owners[channel_id]
                        self.save_voice_owners(self.voice_owners)
                        embed = disnake.Embed(
                            title="Владелец покинул канал",
                            description=f"{member.mention} покинул канал **{before.channel.name}** и больше не является владельцем.",
                            color=disnake.Color.from_rgb(250, 77, 252)
                        )
                        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                        embed.set_footer(
                            text=f"Пользователь: {member.display_name}",
                            icon_url=member.avatar.url if member.avatar else member.default_avatar.url
                        )
                        try:
                            await log_channel.send(embed=embed)
                        except Exception as e:
                            print(f"[VoiceManager on_voice_state_update] Ошибка при отправке сообщения о сбросе владельца: {e}", flush=True)

    @commands.slash_command(description="Кикнуть участника из голосового канала (только для владельца канала)")
    async def voice_kick(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member):
        await inter.response.defer(ephemeral=True)

        if member.bot:
            embed = disnake.Embed(
                title="Ошибка",
                description="**Нельзя кикнуть бота из голосового канала!**\n\nКоманда `/voice_kick` работает только для участников, а не для ботов. Если вам нужно удалить бота, обратитесь к администратору сервера.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        if member == inter.author:
            embed = disnake.Embed(
                title="Ошибка",
                description="**Вы не можете кикнуть самого себя!**\n\nКоманда `/voice_kick` предназначена для исключения других участников из голосового канала. Если вы хотите покинуть канал, просто выйдите из него вручную.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        author_voice = inter.author.voice
        if not author_voice or not author_voice.channel:
            embed = disnake.Embed(
                title="Ошибка",
                description="**Вы должны находиться в голосовом канале, чтобы использовать эту команду!**\n\nПожалуйста, подключитесь к любому голосовому каналу на сервере и попробуйте снова.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        channel_id = str(author_voice.channel.id)
        if author_voice.channel.id in self.excluded_channels:
            embed = disnake.Embed(
                title="Ошибка",
                description="**Эта команда недоступна в данном канале!**\n\nСистема управления голосовыми каналами отключена для этого канала.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        if channel_id not in self.voice_owners or self.voice_owners[channel_id] != str(inter.author.id):
            embed = disnake.Embed(
                title="Ошибка",
                description="**Вы не являетесь владельцем этого голосового канала!**\n\nКоманда `/voice_kick` доступна только владельцу канала. Подождите, пока вы не станете владельцем, или обратитесь к текущему владельцу канала.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        member_voice = member.voice
        if not member_voice or not member_voice.channel:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"**{member.display_name} не находится в голосовом канале!**\n\nУчастник, которого вы пытаетесь кикнуть, сейчас не подключён ни к одному голосовому каналу. Убедитесь, что он находится в канале, и попробуйте снова.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        if member_voice.channel.id != author_voice.channel.id:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"**{member.display_name} находится в другом голосовом канале!**\n\nВы можете кикнуть только тех участников, которые находятся в том же голосовом канале, что и вы. Подключитесь к каналу {member_voice.channel.name} или попросите участника перейти в ваш канал.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        try:
            await member.edit(voice_channel=None)
            embed = disnake.Embed(
                title="Участник кикнут",
                description=f"{member.display_name} был кикнут из голосового канала!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            await inter.edit_original_response(embed=embed)

            # Отправка сообщения кикнутому участнику в DM
            dm_embed = disnake.Embed(
                title="Вы были кикнуты",
                description=f"Вы были кикнуты из канала **{author_voice.channel.name}** владельцем {inter.author.display_name}!\nДоступ к каналу закрыт на 10 минут.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            dm_embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            try:
                await member.send(embed=dm_embed)
            except disnake.Forbidden:
                print(f"[VoiceManager voice_kick] Не удалось отправить сообщение {member.display_name} в DM: доступ закрыт", flush=True)

            # Ограничение доступа к каналу
            self.bot.loop.create_task(self.restrict_channel_access(member, author_voice.channel))

            # Отправка лога в канал 1366418566630346813
            kick_log_channel = self.bot.get_channel(self.kick_log_channel_id)
            if kick_log_channel:
                current_members = author_voice.channel.members
                members_list = "\n".join([f"{m.mention}" for m in current_members]) if current_members else "Нет участников."
                log_embed = disnake.Embed(
                    title="Участник кикнут из голосового канала",
                    description=(
                        f"Владелец канала: {inter.author.mention}\n"
                        f"Кикнутый участник: {member.mention}\n"
                        f"Доступ к каналу {author_voice.channel.mention} заблокирован для участника на 10 минут.\n\n"
                        f"**Текущие участники канала:**\n{members_list}"
                    ),
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                log_embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)
                try:
                    await kick_log_channel.send(embed=log_embed)
                except Exception as e:
                    print(f"[VoiceManager voice_kick] Ошибка при отправке лога кика в канал {self.kick_log_channel_id}: {e}", flush=True)

        except disnake.Forbidden:
            embed = disnake.Embed(
                title="Ошибка",
                description="**У бота нет прав для кика этого участника из голосового канала!**\n\nПожалуйста, убедитесь, что у бота есть необходимые разрешения (например, права на управление участниками в голосовых каналах). Обратитесь к администратору сервера, если проблема сохраняется.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
        except Exception as e:
            embed = disnake.Embed(
                title="Ошибка",
                description=f"**Произошла ошибка при выполнении команды!**\n\nДетали ошибки: {e}\nПожалуйста, попробуйте снова позже или обратитесь к администратору сервера, если проблема сохраняется.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            print(f"[VoiceManager voice_kick] Ошибка при выполнении команды voice_kick: {e}", flush=True)

    @commands.slash_command(description="Показать панель управления голосовым каналом (только для владельца канала)")
    async def voice_panel(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        author_voice = inter.author.voice
        if not author_voice or not author_voice.channel:
            embed = disnake.Embed(
                title="Ошибка",
                description="**Вы должны находиться в голосовом канале, чтобы использовать эту команду!**\n\nПожалуйста, подключитесь к любому голосовому каналу на сервере и попробуйте снова.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        channel_id = str(author_voice.channel.id)
        if author_voice.channel.id in self.excluded_channels:
            embed = disnake.Embed(
                title="Ошибка",
                description="**Эта команда недоступна в данном канале!**\n\nСистема управления голосовыми каналами отключена для этого канала.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        if channel_id not in self.voice_owners or self.voice_owners[channel_id] != str(inter.author.id):
            embed = disnake.Embed(
                title="Ошибка",
                description="**Вы не являетесь владельцем этого голосового канала!**\n\nКоманда `/voice_panel` доступна только владельцу канала. Подождите, пока вы не станете владельцем, или обратитесь к текущему владельцу канала.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif")
            await inter.edit_original_response(embed=embed)
            return

        voice_channel = author_voice.channel
        members = voice_channel.members
        owner = inter.author 
        members_list = "\n".join([f"- {m.display_name}" for m in members]) if members else "Нет участников."

        embed = disnake.Embed(
            title=f"Панель управления каналом: {voice_channel.name}",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.add_field(name="Владелец", value=owner.mention, inline=False)
        embed.add_field(name="Участники", value=members_list, inline=False)
        embed.set_thumbnail(url=inter.guild.me.avatar.url)

        options = [
            disnake.SelectOption(label=member.display_name, value=str(member.id))
            for member in members if member != owner and not member.bot
        ]

        if not options:
            embed.add_field(name="Кик участников", value="Нет участников для кика.", inline=False)
            await inter.edit_original_response(embed=embed)
            return

        select_menu = disnake.ui.Select(
            placeholder="Выберите участника для кика...",
            options=options,
            custom_id=f"kick_select_{channel_id}_{inter.author.id}"
        )

        async def select_callback(interaction: disnake.MessageInteraction):
            if interaction.user != inter.author:
                await interaction.response.send_message(
                    "Вы не можете использовать это меню, так как вы не вызвали команду `/voice_panel`!",
                    ephemeral=True
                )
                return

            selected_member_id = int(interaction.data.values[0])
            member_to_kick = voice_channel.guild.get_member(selected_member_id)

            if not member_to_kick:
                await interaction.response.send_message(
                    "Участник не найден. Возможно, он покинул сервер.",
                    ephemeral=True
                )
                return

            if member_to_kick.voice is None or member_to_kick.voice.channel != voice_channel:
                await interaction.response.send_message(
                    f"{member_to_kick.display_name} уже покинул голосовой канал.",
                    ephemeral=True
                )
                updated_members = voice_channel.members
                updated_members_list = "\n".join([f"- {m.display_name}" for m in updated_members]) if updated_members else "Нет участников."
                embed.set_field_at(1, name="Участники", value=updated_members_list, inline=False)
                updated_options = [
                    disnake.SelectOption(label=m.display_name, value=str(m.id))
                    for m in updated_members if m != owner and not m.bot
                ]
                if updated_options:
                    select_menu.options = updated_options
                    await interaction.message.edit(embed=embed, view=view)
                else:
                    embed.add_field(name="Кик участников", value="Нет участников для кика.", inline=False)
                    await interaction.message.edit(embed=embed, view=None)
                return

            try:
                await member_to_kick.edit(voice_channel=None)

                # Отправка сообщения кикнутому участнику в DM
                dm_embed = disnake.Embed(
                    title="Вы были кикнуты",
                    description=f"Вы были кикнуты из канала **{voice_channel.name}** владельцем {inter.author.display_name}!\nДоступ к каналу закрыт на 10 минут.",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                dm_embed.set_thumbnail(url=member_to_kick.avatar.url if member_to_kick.avatar else member_to_kick.default_avatar.url)
                try:
                    await member_to_kick.send(embed=dm_embed)
                except disnake.Forbidden:
                    print(f"[VoiceManager voice_panel] Не удалось отправить сообщение {member_to_kick.display_name} в DM: доступ закрыт", flush=True)

                # Ограничение доступа к каналу
                self.bot.loop.create_task(self.restrict_channel_access(member_to_kick, voice_channel))

                # Отправка лога в канал 1366418566630346813
                kick_log_channel = self.bot.get_channel(self.kick_log_channel_id)
                if kick_log_channel:
                    current_members = voice_channel.members
                    members_list = "\n".join([f"{m.mention}" for m in current_members]) if current_members else "Нет участников."
                    log_embed = disnake.Embed(
                        title="Участник кикнут из голосового канала",
                        description=(
                            f"Владелец канала: {inter.author.mention}\n"
                            f"Кикнутый участник: {member_to_kick.mention}\n"
                            f"Доступ к каналу {voice_channel.mention} заблокирован для участника на 10 минут.\n\n"
                            f"**Текущие участники канала:**\n{members_list}"
                        ),
                        color=disnake.Color.from_rgb(250, 77, 252)
                    )
                    log_embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)
                    try:
                        await kick_log_channel.send(embed=log_embed)
                    except Exception as e:
                        print(f"[VoiceManager voice_panel] Ошибка при отправке лога кика в канал {self.kick_log_channel_id}: {e}", flush=True)

                updated_members = voice_channel.members
                updated_members_list = "\n".join([f"- {m.display_name}" for m in updated_members]) if updated_members else "Нет участников."
                embed.set_field_at(1, name="Участники", value=updated_members_list, inline=False)
                updated_options = [
                    disnake.SelectOption(label=m.display_name, value=str(m.id))
                    for m in updated_members if m != owner and not m.bot
                ]
                if updated_options:
                    select_menu.options = updated_options
                    await interaction.response.edit_message(embed=embed, view=view)
                else:
                    embed.add_field(name="Кик участников", value="Нет участников для кика.", inline=False)
                    await interaction.response.edit_message(embed=embed, view=None)

            except disnake.Forbidden:
                await interaction.response.send_message(
                    "У бота нет прав для кика этого участника из голосового канала!",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"Произошла ошибка при кике: {e}",
                    ephemeral=True
                )

        view = disnake.ui.View()
        select_menu.callback = select_callback
        view.add_item(select_menu)

        await inter.edit_original_response(embed=embed, view=view)

def setup(bot: commands.Bot):
    bot.add_cog(VoiceManager(bot))