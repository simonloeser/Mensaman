import os
import discord
import requests
from discord import app_commands
from datetime import date
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
GUILD = os.getenv('GUILD')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
URL = os.getenv('URL')

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def get_daily_menu(url, target_weekday=None):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    today = date.today()
    weekday = today.strftime('%A')
    if target_weekday is not None:
        weekday = target_weekday

    tab_id = f"tab_{weekday}"
    tab = soup.find('div', class_=tab_id)
    if not tab:
        return []

    menu_items = tab.find_all('li', class_=lambda value: value and value.startswith('tab_'))
    menu = []

    for item in menu_items:
        title_element = item.find('h5')
        title = title_element.text.strip()
        if title_element.find('span'):
            subtitle = title_element.find('span').text.strip()
            title = title.replace(subtitle, '')
            title = title.strip()

        menu.append(title)

    return menu


async def print_menu(url, target_weekday=None):
    menu = get_daily_menu(url, target_weekday)

    if target_weekday is None:
        target_weekday = "heute"

    if menu:
        message = f'# Essen für {target_weekday}:\n'
        for i, item in enumerate(menu, start=1):
            message += f'* Essen {i}: {item}\n'
    else:
        message = f'Kein Speiseplan für {target_weekday} verfügbar.'
    return '```md\n' + message + '```'


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD))
    print(f'{client.user} is ready to deliver some meals!')


@tree.command(name="meal", description="Gives you the meal of the day", guild=discord.Object(id=GUILD))
async def meal_command(interaction, day: str = None):
    if day is None:
        await interaction.response.send_message(await print_menu(URL))
    else:
        await interaction.response.send_message(await print_menu(URL, day.capitalize()))


client.run(TOKEN)
