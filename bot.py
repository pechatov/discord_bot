import os
import discord
import random
from requests import get
from bs4 import BeautifulSoup
import re
from discord.ext import commands
from emoji import emoji
from dotenv import load_dotenv
import json
import pickle
from classes import classes, specs, class_dict, class_color
from character import Character
from dungeons import dungeons, dungeons_dict, dungeons_str_1, dungeons_str_2
from wa import weak_auras
import time


load_dotenv()
token = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!')
top_k = 5
raider_io = 'https://raider.io'
base_url = 'https://raider.io/mythic-plus-spec-rankings/season-bfa-4/world/'
api = '/api/v1/characters/profile?'
postfix = 'region={}&realm={}&name={}&fields=gear'


def make_url(postfix):
    return raider_io + postfix


def get_data_from_api(region, realm, name):
    rio_api_url = raider_io + api + postfix.format(region, realm, name)
    return json.loads(get(rio_api_url).text)


def build_inversed_dict(d):
    return {v: k for k, list_v in d.items() for v in list_v}


def refresh_spec(c, spec):
    print('{} {} is started'.format(spec, c))
    global all_specs
    rio_url = base_url + c + '/' + spec
    page = get(base_url + c + '/' + spec)
    soup = BeautifulSoup(page.text, 'lxml')
    header = soup.find_all('h3')[:top_k]
    urls = [header[i].find('a')['href'] for i in range(top_k)]
    curr_spec = []
    for i in range(top_k):
        region = urls[i].split('/')[2]
        realm = urls[i].split('/')[3]
        name = header[i].text
        rio_data = get_data_from_api(region, realm, name)
        thumbnail_url = rio_data['thumbnail_url']
        url = rio_data['profile_url']
        item_level = rio_data['gear']['item_level_equipped']
        corruption = rio_data['gear']['corruption']
        faction = rio_data['faction']
        neck_level = round(rio_data['gear']['artifact_traits'], 2)

        character = Character(name=name, url=url, rio=soup.find_all('td')[3 + i * 5].text,
                              region=region, realm=realm,
                              neck_level=neck_level, item_level=item_level, corruption=corruption,
                              c=c, spec=spec, faction=faction)

        for x in soup.find_all('a')[(i + 2) * 15: (i + 2) * 15 + 12]:
            dungeon = '_'.join(x['href'].split('/')[3].split('-')[2:])
            character.links[dungeon] = raider_io + x['href']
            character.level[dungeon] = x['href'].split('/')[-1].split('-')[1]
        curr_spec.append(character)
    print('{} {} is done'.format(spec, c))
    all_specs[c + '_' + spec] = curr_spec
    with open('rio', 'wb') as file:
        pickle.dump(all_specs, file)


def refresh_data():
    all_specs = dict()
    for c in classes:
        for spec in specs[c]:
            refresh_spec(c, spec)


def create_embed(character, top_i, print_corruptions=True):
    title = '{}. {}'.format(top_i + 1, character.name)
    title += ' ' * (105 - int(2.5 * len(title))) + str(character.rio)
    embed = discord.Embed(colour=class_color[character.c])
    embed.set_author(
        name=title, url=character.url, icon_url=character.spec_logo)
    embed.set_thumbnail(url=character.faction_logo_url)
    embed.add_field(name='item level', value=character.item_level, inline=True)
    embed.add_field(name='neck level', value=character.neck_level, inline=True)
    embed.add_field(name='corruption', value=character.corruption_total -
                    character.corruption_resistance, inline=True)

    dungeon_timers_1 = '⠀'.join(['[+{}]({})'.format(character.level[dungeon], character.links[dungeon])
                                 for dungeon in dungeons[:6]])
    dungeon_timers_2 = '⠀'.join(['[+{}]({})'.format(character.level[dungeon], character.links[dungeon])
                                 for dungeon in dungeons[6:]])

    result_1 = dungeons_str_1 + '\n' + dungeon_timers_1
    result_2 = dungeons_str_2 + '\n' + dungeon_timers_2

    embed.add_field(name=dungeons_str_1, value=dungeon_timers_1, inline=True)
    embed.add_field(name=dungeons_str_2, value=dungeon_timers_2, inline=True)

    if print_corruptions:
        embed.add_field(name='corruptions', value=' '.join([emoji[corrupt]
                                                            for corrupt in character.corruptions]), inline=False)
    return embed


@bot.event
async def on_ready():
    refresh_on_start = False
    print(f'{bot.user} has connected to Discord!')
    if refresh_on_start:
        refresh_data()
    with open('rio', 'rb') as file:
        global all_specs
        all_specs = pickle.load(file)
    print('data loaded')


@bot.command(name='roll', help='Simulates rolling dice.')
async def roll(ctx, arg=None):
    if not arg:
        n_min = 1
        n_max = 100
    else:
        try:
            n_min, n_max = map(int, arg.split('-'))
        except(Exception):
            await ctx.send('Wrong input. Try !roll 1-100')
            return
    dice = str(random.choice(range(n_min, n_max + 1)))
    await ctx.send('{} rolled {} ({} - {})'.format(ctx.author, dice, n_min, n_max))


@bot.command(name='refresh', help='refresh rio')
@commands.has_role('admin')
async def refresh(ctx, c=None, spec=None):
    await ctx.send('refreshing, wait few minutes...')
    if c:
        c = build_inversed_dict(class_dict)[c]
        if spec:
            refresh_spec(c, spec)
        else:
            for spec in specs[c]:
                refresh_spec(c, spec)
    else:
        refresh_data()
    await ctx.send('refreshing is finished!')


@bot.command(name='top', help='find top player on raider.io')
async def find_top(ctx, arg1=None, arg2=None):
    global emojis
    d = build_inversed_dict(class_dict)
    if arg1:
        arg1 = d[arg1]
    if time.time() - all_specs[arg1 + '_' + arg2][0]._timestamp > 36000:
        refresh_spec(arg1, arg2)
    for i in range(top_k):
        embed = create_embed(all_specs[arg1 + '_' + arg2][i], i)
        await ctx.send(embed=embed)


@bot.command(name='wa', help='post cool weak auras')
async def wa(ctx, action=None, name=None, url=None):
    with open('weak_auras.json', 'r') as fp:
        weak_auras = json.load(fp)
    embed = discord.Embed(title='useful weak auras',
                          colour=10141308, url='https://wago.io')
    lines = ''
    for name, url in weak_auras.items():
        lines += '[{}]({})\n'.format(name, url)
    embed.add_field(name="wa", value=lines, inline=True)

    await ctx.send(embed=embed)


@bot.command(name='wa_add')
@commands.has_role('admin')
async def wa_add(ctx, name, url):
    with open('weak_auras.json', 'r') as fp:
        weak_auras = json.load(fp)
    weak_auras[name] = url
    with open('weak_auras.json', 'w') as fp:
        json.dump(weak_auras, fp)
    await ctx.send('aura is added')


@bot.command(name='wa_delete')
@commands.has_role('admin')
async def wa_delete(ctx, name):
    with open('weak_auras.json', 'r') as fp:
        weak_auras = json.load(fp)
    if name in weak_auras.keys():
        weak_auras.pop(name)
        with open('weak_auras.json', 'w') as fp:
            json.dump(weak_auras, fp)
        await ctx.send('aura is deleted')
        return
    await ctx.send('wrong name')


@bot.command(name='create-channel')
@commands.has_role('admin')
async def create_channel(ctx, channel_name='real-python'):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        print(f'Creating a new channel: {channel_name}')
        await guild.create_text_channel(channel_name)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


bot.run(token)
