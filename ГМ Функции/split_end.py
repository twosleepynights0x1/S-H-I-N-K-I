import disnake
from disnake.ext import commands
from disnake.ui import Button, View
import asyncio
import os
import json

CONFIG_PATH = os.path.join('conf', 'config.json')

class SeasonSplitEnd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cancelled = False

        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")

        self.roles_to_remove = config["season"]["RankedRoles"]

        self.allowed_roles = config["roles"]["administration"]["AdminRoles"]

    async def send_error_embed(self, interaction, description):
        embed = disnake.Embed(
            title="Ошибка",
            description=description,
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=interaction.guild.me.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
        embed.set_footer(text=f"Администратор: {interaction.user.name}", icon_url=interaction.user.avatar.url)
        
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Ошибка при отправке сообщения об ошибке: {e}")
            try:
                await interaction.followup.send("Произошла ошибка: " + description, ephemeral=True)
            except:
                pass

    async def cancel_operation(self, interaction, embed):
        self.cancelled = True
        embed.title = "Операция SeasonSplit End отменена!"
        embed.description = "Процесс снятия сезонных ролей был отменен администраторами."
        embed.color = disnake.Color.from_rgb(250, 77, 252)
        embed.set_footer(text=f"Администратор: {interaction.user.name}", icon_url=interaction.user.avatar.url)
        
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=False)
            else:
                await interaction.followup.send(embed=embed, ephemeral=False)
        except Exception as e:
            print(f"Ошибка при отправке сообщения об отмене: {e}")
            await self.send_error_embed(interaction, "Не удалось отправить сообщение об отмене.")

    @commands.slash_command(name="seasonsplit_end", description="Снять все сезонные роли у участников сервера")
    async def seasonsplit_end(self, interaction: disnake.ApplicationCommandInteraction):
        if not (interaction.user.guild_permissions.administrator or 
                any(role.id in self.allowed_roles for role in interaction.user.roles)):
            await self.send_error_embed(
                interaction,
                "**У вас нет прав для использования этой команды ^^**"
            )
            return

        if not interaction.guild.me.guild_permissions.manage_roles:
            await self.send_error_embed(
                interaction,
                "У меня нет прав на управление ролями. Пожалуйста, выдайте мне соответствующие права."
            )
            return

        cancel_button = Button(label="Отменить", style=disnake.ButtonStyle.red)
        view = View(timeout=None)
        view.add_item(cancel_button)

        initial_embed = disnake.Embed(
            title="Начало SeasonSplit End",
            description="Начинается процесс снятия сезонных ролей у всех участников. Это может занять некоторое время.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        initial_embed.set_footer(text=f"Администратор: {interaction.user.name}", icon_url=interaction.user.avatar.url)

        try:
            await interaction.response.send_message(embed=initial_embed, view=view)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            await self.send_error_embed(interaction, "Не удалось начать процесс.")
            return

        async def cancel_button_callback(interaction):
            if not interaction.user.guild_permissions.administrator:
                await self.send_error_embed(
                    interaction,
                    "Только администраторы могут отменять операцию."
                )
                return
            await self.cancel_operation(interaction, initial_embed)

        cancel_button.callback = cancel_button_callback

        async def remove_season_roles():
            total_removed = 0
            guild = interaction.guild

            for role_id in self.roles_to_remove:
                if self.cancelled:
                    break

                role = guild.get_role(role_id)
                if not role:
                    print(f"Роль с ID {role_id} не найдена!")
                    continue

                if role.position >= guild.me.top_role.position:
                    print(f"Роль {role.name} выше моей, пропускаю...")
                    continue

                members_with_role = [member for member in guild.members if role in member.roles]
                if not members_with_role:
                    continue

                for member in members_with_role:
                    if self.cancelled:
                        break

                    try:
                        await member.remove_roles(role)
                        total_removed += 1
                        await asyncio.sleep(1) 
                    except disnake.Forbidden:
                        print(f"Нет прав для снятия роли {role.name} у {member.display_name}")
                    except Exception as e:
                        print(f"Ошибка при снятии роли {role.name} у {member.display_name}: {e}")

            if not self.cancelled:
                final_embed = disnake.Embed(
                    title="SeasonSplit End завершен!",
                    description=f"Все сезонные роли были успешно сняты у участников.\nВсего снятий: {total_removed}",
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                final_embed.set_footer(text=f"Администратор: {interaction.user.name}", icon_url=interaction.user.avatar.url)
                final_embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1357551316662091928/standard_1.gif?ex=67f09daf&is=67ef4c2f&hm=b8c415386529008795f4e69498180f03ef1a9ae04231660c059b297760ea2071&=")
                try:
                    await interaction.followup.send(embed=final_embed)
                except Exception as e:
                    print(f"Ошибка при отправке финального сообщения: {e}")

        self.cancelled = False
        await remove_season_roles()

    @commands.Cog.listener()
    async def on_ready(self):
        self.cancelled = False

def setup(bot):
    bot.add_cog(SeasonSplitEnd(bot))