import disnake
from disnake.ext import commands
import json
import os

class ScrimsEnd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_data_file = "data/trios_voice.json"

    @commands.slash_command(name="maker_del_trios", description="Удалить голосовые каналы скримов")
    @commands.has_permissions(administrator=True)
    async def scrims_end_trios(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        if not os.path.exists(self.voice_data_file):
            embed = disnake.Embed(
                title="Ошибка",
                description="Файл с данными о голосовых каналах не найден!",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        with open(self.voice_data_file, "r", encoding="utf-8") as f:
            voice_channel_ids = json.load(f)
        if not voice_channel_ids:
            embed = disnake.Embed(
                title="Ошибка",
                description="Нет голосовых каналов для удаления.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67dd84f3&is=67dc3373&hm=81cdd044adda52918b2c114aef585e65e5db0fa2c06590923aba500eee96aca7&=&width=1424&height=82")
            await inter.edit_original_response(embed=embed)
            return
        deleted_channels = []
        for channel_id in voice_channel_ids:
            channel = inter.guild.get_channel(channel_id)
            if channel and isinstance(channel, disnake.VoiceChannel):
                await channel.delete(reason="Завершение скримов")
                deleted_channels.append(f"<#{channel_id}>")
        with open(self.voice_data_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        embed = disnake.Embed(
            title="Скримы завершены",
            description="Все голосовые каналы успешно удалены.\n",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1352445993937014814/standard_15.gif?ex=67de0afc&is=67dcb97c&hm=4107c81680fbcfb45e95a4a646ad3851095ac749424595d4efd34daf78dbf055&=&width=1424&height=82")
        await inter.edit_original_response(embed=embed)

def setup(bot):
    bot.add_cog(ScrimsEnd(bot))