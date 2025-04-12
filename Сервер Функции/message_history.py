import disnake
import json
import os
from disnake.ext import commands

MESSAGE_HISTORY_PATH = "data/message_history.json"

class MessageHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs(os.path.dirname(MESSAGE_HISTORY_PATH), exist_ok=True)
        if not os.path.exists(MESSAGE_HISTORY_PATH):
            with open(MESSAGE_HISTORY_PATH, "w", encoding="utf-8") as file:
                json.dump({}, file)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return

        try:
            with open(MESSAGE_HISTORY_PATH, "r", encoding="utf-8") as file:
                message_history = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            message_history = {}

        user_id = str(message.author.id)

        if user_id not in message_history:
            message_history[user_id] = {
                "username": str(message.author),
                "messages": []
            }

        message_history[user_id]["messages"].append({
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
            "channel_id": message.channel.id,
            "channel_name": str(message.channel)
        })

        with open(MESSAGE_HISTORY_PATH, "w", encoding="utf-8") as file:
            json.dump(message_history, file, indent=4, ensure_ascii=False)

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        if message.author.bot:
            return

        try:
            with open(MESSAGE_HISTORY_PATH, "r", encoding="utf-8") as file:
                message_history = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        user_id = str(message.author.id)

        if user_id in message_history:
            for msg in message_history[user_id]["messages"]:
                if msg["content"] == message.content and msg["timestamp"] == message.created_at.isoformat():
                    msg["deleted"] = True
                    break

            with open(MESSAGE_HISTORY_PATH, "w", encoding="utf-8") as file:
                json.dump(message_history, file, indent=4, ensure_ascii=False)

def setup(bot):
    bot.add_cog(MessageHistory(bot))