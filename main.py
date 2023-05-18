import locale
import os
import random
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
        title_element = item.find('strong')
        if title_element:
            title = title_element.text.strip()
            menu.append(title)
    return menu


async def print_menu(url, target_weekday=None):
    menu = get_daily_menu(url, target_weekday)
    if target_weekday is None:
        target_weekday = "heute"

    if menu:
        color = random.randint(0, 0xFFFFFF)
        embed = discord.Embed(title=f'Essen für {target_weekday}', color=color)
        for i, item in enumerate(menu, start=1):
            embed.add_field(name=f'Essen {i}', value=item, inline=False)
        embed.url = URL
    else:
        embed = discord.Embed(title=f'Kein Speiseplan für {target_weekday} verfügbar', color=0xff0000)
    return embed


@tree.command(name="meal", description="Gives you the meal of the day", guild=discord.Object(id=GUILD))
async def meal_command(interaction, day: str = None):
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    if day is None:
        target_weekday = date.today().strftime('%A').capitalize()
    else:
        target_weekday = day.capitalize()

    embed = await print_menu(URL, target_weekday)
    await interaction.response.send_message(embed=embed)


@tree.command(name="allmeals", description="Gives you all remaining meals of the week", guild=discord.Object(id=GUILD))
async def allmeals_command(interaction):
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    today = date.today()
    weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag']
    current_weekday = today.weekday()

    color = random.randint(0, 0xFFFFFF)
    embed = discord.Embed(title='Speiseplan für die Restwoche', color=color)
    embed.url = URL

    for i in range(current_weekday, len(weekdays)):
        target_weekday = weekdays[i]
        menu_embed = await print_menu(URL, target_weekday)

        if menu_embed:
            embed.add_field(name=f'{target_weekday}', value='\u200B', inline=False)
            fields = menu_embed.fields
            for field in fields:
                embed.add_field(name=field.name, value=field.value, inline=False)
        else:
            continue
    await interaction.response.send_message(embed=embed)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD))
    print(f'{client.user} is ready to deliver some meals!')


client.run(TOKEN)