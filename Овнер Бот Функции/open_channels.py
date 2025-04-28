import disnake
from disnake.ext import commands
import json
import os
import asyncio

CONFIG_PATH = os.path.join('conf', 'config.json')

class OpenVoiceChannels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1359907627882119459  
        self.category_ids = {
            "Паблик трио": 597292342185033730,
            "Паблик дуо": 686482164275216394,
            "Сильвер/Бронза": 825719235577643038,
            "Голд": 825727668023721984,
            "Платина": 825738424153407509,
            "Даймонд": 825741661644128306,
            "Мастер": 825745899782799375,
            "Предатор": 884091982903910410
        }

        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise Exception(f"Не удалось загрузить конфигурацию из {CONFIG_PATH}: {e}")

        self.allowed_roles = config["roles"]["administration"]["AdminRoles"]

    async def create_error_embed(self, description: str) -> disnake.Embed:
        embed = disnake.Embed(
            title="Ошибка",
            description=f"**{description} ^^**",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
        return embed

    async def create_progress_embed(self, processed: int, total: int) -> disnake.Embed:
        embed = disnake.Embed(
            title="⏳ Обработка голосовых каналов",
            description=f"Обработано: {processed}/{total} каналов.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed

    @commands.slash_command(name="open_voice_channels", description="Открыть права на просмотр для всех голосовых каналов в категориях")
    async def open_voice_channels(self, inter: disnake.ApplicationCommandInteraction):
        """Открывает права на просмотр для всех голосовых каналов в заданных категориях."""
        await inter.response.defer(ephemeral=True)

        if not any(role.id in self.allowed_roles for role in inter.user.roles) and not inter.user.guild_permissions.administrator:
            embed = await self.create_error_embed("У вас нет прав для использования этой команды")
            await inter.edit_original_response(embed=embed)
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if not log_channel:
            embed = await self.create_error_embed(f"Канал для логов с ID {self.log_channel_id} не найден")
            await inter.edit_original_response(embed=embed)
            return

        all_voice_channels = []
        for category_name, category_id in self.category_ids.items():
            category = inter.guild.get_channel(category_id)
            if not category or not isinstance(category, disnake.CategoryChannel):
                print(f"[OpenVoiceChannels] Категория с ID {category_id} не найдена или не является категорией")
                continue

            voice_channels = category.voice_channels
            if not voice_channels:
                print(f"[OpenVoiceChannels] В категории {category_name} (ID: {category_id}) нет голосовых каналов")
                continue

            for channel in voice_channels:
                all_voice_channels.append((channel, category_name))

        if not all_voice_channels:
            embed = await self.create_error_embed("Не найдено ни одного голосового канала в указанных категориях")
            await inter.edit_original_response(embed=embed)
            return

        total_channels = len(all_voice_channels)
        opened_channels_count = 0
        processed_channels = 0

        for channel, category_name in all_voice_channels:
            try:
                # Устанавливаем права только на просмотр канала для @everyone
                await channel.set_permissions(
                    inter.guild.default_role,  # @everyone
                    view_channel=True
                )
                opened_channels_count += 1
                print(f"[OpenVoiceChannels] Открыт доступ к каналу {channel.name} (ID: {channel.id})")

                log_embed = disnake.Embed(
                    title="Голосовой канал открыт",
                    description=(
                        f"Инициализировал: {inter.user.mention} ({inter.user})\n"
                        f"Канал: {channel.mention} (в категории {category_name})"
                    ),
                    color=disnake.Color.from_rgb(250, 77, 252)
                )
                log_embed.set_thumbnail(url=inter.user.avatar.url if inter.user.avatar else inter.user.default_avatar.url)
                try:
                    await log_channel.send(embed=log_embed)
                except Exception as e:
                    print(f"[OpenVoiceChannels] Ошибка при отправке лога в канал {self.log_channel_id}: {e}")

            except disnake.Forbidden:
                print(f"[OpenVoiceChannels] Нет прав для изменения разрешений канала {channel.name} (ID: {channel.id})")
            except Exception as e:
                print(f"[OpenVoiceChannels] Ошибка при изменении прав для канала {channel.name} (ID: {channel.id}): {e}")

            processed_channels += 1

            if processed_channels % 10 == 0 or processed_channels == total_channels:
                embed = await self.create_progress_embed(processed_channels, total_channels)
                await inter.edit_original_response(embed=embed)

            await asyncio.sleep(1)

        embed = disnake.Embed(
            title="✅ Успех",
            description=f"Права на просмотр открыты для {opened_channels_count} голосовых каналов.\nПодробности в канале логов.",
            color=disnake.Color.from_rgb(250, 77, 252)
        ) if opened_channels_count > 0 else disnake.Embed(
            title="ℹ️ Ничего не изменено",
            description="Не удалось открыть ни один голосовой канал. Проверьте логи бота.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )

        embed.set_thumbnail(url=self.bot.user.avatar.url)
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(OpenVoiceChannels(bot))