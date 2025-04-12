import disnake
from disnake.ext import commands
from pathlib import Path
import os

class DevCogManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _handle_cog(self, inter: disnake.ApplicationCommandInteraction, action: str, cog: str):
        directories = ["MODULES"]

        cog_path = None
        for directory in directories:
            potential_path = f"{directory}.{cog}"
            if action != "load" and potential_path in self.bot.extensions:
                cog_path = potential_path
                break
            elif action == "load" and Path(os.path.join(directory, f"{cog}.py")).exists():
                cog_path = potential_path
                break

        if cog_path is None:
            await inter.response.send_message(
                embed=disnake.Embed(
                    title="❌ Ког не найден",
                    description=f"Ког **{cog}** не найден в директории `{directory}`.",
                    color=disnake.Color.from_rgb(250, 77, 252),
                )
            )
            return
        try:
            if action == "load":
                self.bot.load_extension(cog_path)
                result = f"Ког **`{cog_path}`** успешно загружен."
                color = disnake.Color.from_rgb(250, 77, 252)
                icon = "✅"
            elif action == "unload":
                self.bot.unload_extension(cog_path)
                result = f"Ког **`{cog_path}`** успешно выгружен."
                color = disnake.Color.from_rgb(250, 77, 252)
                icon = "🟧"
            elif action == "reload":
                self.bot.reload_extension(cog_path)
                result = f"Ког **`{cog_path}`** успешно перезагружен."
                color = disnake.Color.from_rgb(250, 77, 252)
                icon = "🔄"
        except Exception as e:
            result = f"Произошла ошибка при выполнении операции с когом **`{cog_path}`**:\n```{e}```"
            color = disnake.Color.from_rgb(250, 77, 252)
            icon = "❌"

        embed = disnake.Embed(
            title=f"{icon} Результат команды: {action.capitalize()} Cog",
            description=result,
            color=color,
        )
        embed.add_field(name="Действие", value=f"`{action.capitalize()}`", inline=True)
        embed.add_field(name="Название кoга", value=f"`{cog}`", inline=True)
        if action == "load":
            embed.add_field(name="Статус", value="Ког успешно загружен в систему.", inline=False)
        elif action == "unload":
            embed.add_field(name="Статус", value="Ког был успешно выгружен из системы.", inline=False)
        elif action == "reload":
            embed.add_field(name="Статус", value="Ког был успешно перезагружен.", inline=False)
        else:
            embed.add_field(name="Статус", value="Операция завершена.", inline=False)

        embed.set_footer(text=f"Выполнено: {inter.author}", icon_url=inter.author.display_avatar.url)

        await inter.response.send_message(embed=embed)

    @commands.slash_command()
    async def core(
        self,
        inter: disnake.ApplicationCommandInteraction,
        action: str = commands.Param(choices=["load", "unload", "reload"]),
        cog: str = commands.Param(description="Название ког файла (без .py)"),
    ):

        if not inter.user.guild_permissions.administrator and inter.user.id != self.bot.owner_id:
            error_embed = disnake.Embed(
                title="Недостаточно прав",
                description="У вас нет прав администратора для выполнения этой команды.",
                color=disnake.Color.from_rgb(255, 0, 0) 
            )
            error_embed.set_thumbnail(url=self.bot.user.display_avatar.url) 
            await inter.response.send_message(embed=error_embed, ephemeral=True)
            return
        await self._handle_cog(inter, action, cog)

def setup(bot):
    bot.add_cog(DevCogManager(bot))
