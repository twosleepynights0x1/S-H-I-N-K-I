import disnake
from disnake.ext import commands
from disnake import Embed, ButtonStyle, TextInputStyle
import os
import json

if not os.path.exists('data'):
    os.makedirs('data')

INVITES_FILE = os.path.join('data', 'event_maker_invites.json')

CONFIG_FILE = os.path.join('conf', 'config.json')

if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Конфигурационный файл {CONFIG_FILE} не найден.")

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json.load(f)

ADMIN_ROLES = config["roles"]["administration"]["AdminRoles"]

class RecruitmentModal(disnake.ui.Modal):
    def __init__(self, bot, role):
        self.bot = bot
        self.role = role 
        components = [
            disnake.ui.TextInput(
                label="Ваше имя",
                custom_id="name_input",
                style=TextInputStyle.short,
                placeholder="Введите ваше имя...",
                min_length=2,
                max_length=50
            ),
            disnake.ui.TextInput(
                label="Ваш возраст",
                custom_id="age_input",
                style=TextInputStyle.short,
                placeholder="Введите ваш возраст...",
                min_length=1,
                max_length=3
            ),
            disnake.ui.TextInput(
                label="Сколько времени вы готовы уделять серверу?",
                custom_id="time_input",
                style=TextInputStyle.paragraph,
                placeholder="Например, 2-3 часа в день...",
                min_length=5,
                max_length=200
            ),
            disnake.ui.TextInput(
                label="Почему вы решили присоединиться к нам?",
                custom_id="reason_input",
                style=TextInputStyle.paragraph,
                placeholder="Расскажите, почему хотите стать ивент-мейкером...",
                min_length=10,
                max_length=500
            )
        ]
        super().__init__(title=f"Заявка на роль {self.role}", components=components)

    def load_invites(self):
        if os.path.exists(INVITES_FILE):
            with open(INVITES_FILE, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def save_invites(self, invites):
        with open(INVITES_FILE, 'w', encoding='utf-8') as f:
            json.dump(invites, f, indent=4, ensure_ascii=False)

    async def callback(self, inter: disnake.ModalInteraction):

        invites = self.load_invites()

        user_id = str(inter.user.id)
        if user_id in invites and self.role in invites[user_id]:
            error_embed = Embed(
                title="Ошибка",
                description=f"**Вы уже подали заявку на роль {self.role}!** Ожидайте её рассмотрения.",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            error_embed.set_thumbnail(url=inter.guild.me.avatar.url)
            error_embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1322586271809409166/error.gif?ex=67d8e7b3&is=67d79633&hm=d288f557b4ebf2f47899e12e683a4ba810126b68261e161b17b1df1b7a43f422&=")
            await inter.response.send_message(embed=error_embed, ephemeral=True)
            return

        name = inter.text_values["name_input"]
        age = inter.text_values["age_input"]
        time = inter.text_values["time_input"]
        reason = inter.text_values["reason_input"]

        application_channel = self.bot.get_channel(1361777217842970905)
        if not application_channel:
            print(f"Канал с ID 1361777217842970905 не найден.")
            await inter.response.send_message("Произошла ошибка: канал для заявок не найден.", ephemeral=True)
            return

        application_embed = Embed(
            title=f"Новая заявка на роль {self.role}",
            description=f"Заявка от участника: **{inter.user.mention}** (`{inter.user}`)",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        application_embed.set_thumbnail(url=inter.guild.me.avatar.url)
        application_embed.add_field(name="Имя:", value=name, inline=False)
        application_embed.add_field(name="Возраст:", value=age, inline=False)
        application_embed.add_field(name="Сколько времени готов уделять серверу:", value=time, inline=False)
        application_embed.add_field(name="Почему решил присоединиться:", value=reason, inline=False)
        application_embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1361770330590417196/standard.gif?ex=67fff6f3&is=67fea573&hm=91bdf32a8a8309de2172d2585d48e342f71e6bcc7a43aba6acab5604efba718c&=")
        application_embed.set_footer(
            text=f"Пользователь: {inter.user.display_name}",
            icon_url=inter.user.display_avatar.url
        )

        role_mentions = " ".join([f"<@&{role_id}>" for role_id in [471833867007819786, 821839784607612949]])
        await application_channel.send(content=role_mentions, embed=application_embed)

        # Сохраняем заявку в файл
        if user_id not in invites:
            invites[user_id] = {}
        invites[user_id][self.role] = {
            "name": name,
            "age": age,
            "time": time,
            "reason": reason,
            "username": str(inter.user)
        }
        self.save_invites(invites)

        response_embed = Embed(
            title="Заявка отправлена",
            description=f"Ваша заявка на роль {self.role} успешно отправлена! Ожидайте рассмотрения.",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        response_embed.set_thumbnail(url=inter.guild.me.avatar.url)
        response_embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1361770330590417196/standard.gif?ex=67fff6f3&is=67fea573&hm=91bdf32a8a8309de2172d2585d48e342f71e6bcc7a43aba6acab5604efba718c&=")

        await inter.response.send_message(embed=response_embed, ephemeral=True)

class RecruitmentButton(disnake.ui.View):
    def __init__(self, bot, role):
        super().__init__(timeout=None)  
        self.bot = bot
        self.role = role

    @disnake.ui.button(label="Подать заявку", style=ButtonStyle.primary, custom_id="recruitment_button")
    async def recruitment_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        modal = RecruitmentModal(self.bot, self.role)
        await inter.response.send_modal(modal)

class Recruitment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="send_recruitment",
        description="Отправить объявление о наборе на роль в указанный канал.",
        options=[
            disnake.Option(
                name="role",
                description="Выберите роль для набора",
                type=disnake.OptionType.string,
                required=True,
                choices=[
                    disnake.OptionChoice(name="Ивент-Мейкер", value="Ивент-Мейкер")
                ]
            ),
            disnake.Option(
                name="channel",
                description="Выберите канал для отправки объявления",
                type=disnake.OptionType.channel,
                required=True
            )
        ]
    )
    async def send_recruitment(self, inter: disnake.ApplicationCommandInteraction, role: str, channel: disnake.TextChannel):
        """Команда для отправки объявления о наборе на роль."""
        # Проверяем права пользователя (администратор или роль из AdminRoles)
        user_roles = [role.id for role in inter.user.roles]
        has_admin_role = any(role_id in ADMIN_ROLES for role_id in user_roles)
        if not (inter.user.guild_permissions.administrator or has_admin_role):
            embed = Embed(
                title="Ошибка",
                description="**У вас нет прав для использования этой команды ^^**",
                color=disnake.Color.from_rgb(250, 77, 252)
            )
            embed.set_thumbnail(url=inter.guild.me.avatar.url)
            embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1361770330590417196/standard.gif?ex=67fff6f3&is=67fea573&hm=91bdf32a8a8309de2172d2585d48e342f71e6bcc7a43aba6acab5604efba718c&=")
            await inter.response.send_message(embed=embed, ephemeral=True)
            return


        embed = Embed(
            title=f"Набор на роль {role}!",
            description=(
                "**Приветствую уважаемые участники сервера!**\n\n"
                "**Хотите стать частью нашей команды? Получить незабываемый опыт?**\n"
                "Мы открываем заявки на - <@&652889442524069898>\n"
                "*  <@&652889442524069898> - Люди ответственные за мероприятия на сервере\n\n"
                "**Что требуется от тебя?**\n"
                "* Желание и мотивация проводить мероприятия на сервере\n"
                "* Идеи в развитии сервера\n"
                "* Адекватность и возраст (от 17 лет)\n\n"
                "**Что ты получишь от нас?**\n"
                "* Атмосферный и добрый коллектив!\n"
                "* Возможность получить <@&990322144976191558> за хорошую работу!\n"
                "* Карьерный рост и многое другое!\n\n"
                "**Оставляй свою заявку и ожидай результатов! Помни, чем грамотнее оформлена заявка, тем больше у тебя шансов!**"
            ),
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        embed.set_thumbnail(url=inter.guild.me.avatar.url)
        embed.set_image(url="https://media.discordapp.net/attachments/1305280051989708820/1361770330590417196/standard.gif?ex=67fff6f3&is=67fea573&hm=91bdf32a8a8309de2172d2585d48e342f71e6bcc7a43aba6acab5604efba718c&=")
        embed.set_footer(
            text=f"Объявление от: {inter.user.display_name}",
            icon_url=inter.user.display_avatar.url
        )


        await channel.send(content="@everyone", embed=embed, view=RecruitmentButton(self.bot, role))

        response_embed = Embed(
            title="Объявление отправлено",
            description=f"Объявление о наборе на роль {role} успешно отправлено в {channel.mention}!",
            color=disnake.Color.from_rgb(250, 77, 252)
        )
        response_embed.set_thumbnail(url=inter.guild.me.avatar.url)

        await inter.response.send_message(embed=response_embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Recruitment(bot))