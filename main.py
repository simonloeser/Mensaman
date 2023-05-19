import asyncio
import locale
import os
import random
import discord
import requests
from discord import app_commands
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
GUILD = os.getenv('GUILD')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
URL = os.getenv('URL_HOPLA')

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


async def print_menu(url, target_weekday=None, mensa=None):
    menu = get_daily_menu(url, target_weekday)
    if target_weekday is None:
        target_weekday = "heute"

    if mensa is None:
        mensa = 'Willi'

    if menu:
        color = random.randint(0, 0xFFFFFF)
        embed = discord.Embed(title=f'Essen für {target_weekday} ({mensa.capitalize()})', color=color)
        for i, item in enumerate(menu, start=1):
            embed.add_field(name=f'Essen {i}', value=item, inline=False)
        embed.url = URL
    else:
        color = random.randint(0, 0xFFFFFF)
        embed = discord.Embed(title=f'Kein Speiseplan für {target_weekday} verfügbar ({mensa.capitalize()})', color=color)
    return embed


@tree.command(name="meal", description="Gives you the meal of the day", guild=discord.Object(id=GUILD))
async def meal_command(interaction, day: str = None, mensa: str = None):
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    if day is None:
        target_weekday = date.today().strftime('%A').capitalize()
    else:
        target_weekday = day.capitalize()

    change_mensa(mensa)

    embed = await print_menu(URL, target_weekday, mensa)
    await interaction.response.send_message(embed=embed)


@tree.command(name="allmeals", description="Gives you all remaining meals of the week", guild=discord.Object(id=GUILD))
async def allmeals_command(interaction, mensa: str = None):
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    today = date.today()
    weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag']
    current_weekday = today.weekday()

    change_mensa(mensa)
    if mensa is None:
        mensa = 'Willi'

    color = random.randint(0, 0xFFFFFF)
    embed = discord.Embed(title=f'Speiseplan für die Restwoche ({mensa.capitalize()})', color=color)
    embed.url = URL

    for i in range(current_weekday, len(weekdays)):
        target_weekday = weekdays[i]
        menu_embed = await print_menu(URL, target_weekday, mensa)

        if menu_embed and any(field.name.startswith('Essen ') for field in menu_embed.fields):
            fields = menu_embed.fields
            meal_fields_added = False

            for field in fields:
                if field.name.startswith('Essen '):
                    if not meal_fields_added:
                        embed.add_field(name=target_weekday, value='', inline=False)
                        meal_fields_added = True
                    embed.add_field(name=field.name, value=field.value, inline=False)
    await interaction.response.send_message(embed=embed)


def change_mensa(mensa: str = None):
    global URL
    mensa_mapping = {
        'Willi': 'URL_WILLI',
        'Hopla': 'URL_HOPLA',
        'Kunst': 'URL_KUNST',
        'Avz': 'URL_AVZ',
        'Witz': 'URL_WITZ'
    }
    mensa = mensa.capitalize() if mensa else None
    URL = os.getenv(mensa_mapping.get(mensa, 'URL_WILLI'))


async def send_daily_menu():
    global URL
    while True:
        URL = os.getenv('URL_WILLI')
        now = datetime.now()
        target_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if now >= target_time:
            today = date.today()
            current_weekday = today.strftime('%A').capitalize()
            channel = client.get_channel(CHANNEL_ID)
            embed = await print_menu(URL, current_weekday)
            await channel.send(embed=embed)
            target_time = target_time + timedelta(days=1)

        time_difference = target_time - now
        await asyncio.sleep(time_difference.total_seconds())


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD))
    print(f'{client.user} is ready to deliver some meals!')
    client.loop.create_task(send_daily_menu())


async def main():
    try:
        locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
        await client.start(TOKEN)
        await send_daily_menu()
    finally:
        await client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
