import datetime
import inspect
import json
import logging
import os
import random
import subprocess
import time
from datetime import datetime, timedelta
from TonyBot.utils import admin_command, wisdom_info_formatter
from TonyBot import imgur_hb, playfab, TonyCommands, bot_init, db, google_brawl
import asyncio

import discord
from discord.ext import commands

# Setup logging
# Add version here
discordLogger = logging.getLogger('discord')
discordLogger.setLevel(logging.INFO)

discordHandler = logging.FileHandler(
    filename='logs/discord.log', encoding='utf-8', mode='w')
discordHandler.setFormatter(logging.Formatter(
    fmt='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%I:%M:%S'))
discordLogger.addHandler(discordHandler)

logger = logging.getLogger('TonyBot')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='logs/TonyBot.log', encoding='utf-8', mode='w')

console = logging.StreamHandler()
console.setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%I:%M:%S')
handler.setFormatter(formatter)
console.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(console)


bot = commands.Bot(command_prefix='!',
                   description='Super duper halal bot for clowans. List of commands below')

@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name=dbClient.get_game()))
    logger.info('Logged in as {0}:{1}'.format(bot.user.name, bot.user.id))


@bot.command(pass_context=True, hidden=True)
@admin_command
async def debug(ctx, *, code: str):
    """Evaluates code."""
    code = code.strip('` `')
    python = '```py\n{}\n```'
    try:
        result = eval(code)
        if inspect.isawaitable(result):
            result = await result
    except Exception as e:
        await bot.say(python.format(type(e).__name__ + ': ' + str(e)))
        result = None
        return
    await bot.say(python.format(result))


@bot.command()
async def cytube():
    """Для тех кто не умеет добавлять сайты в закладки"""
    cytube_url = dbClient.get_link('cytube')
    movies_url = dbClient.get_link('movies1')
    await bot.say('`Смотреть` <:bearrion:230370930600312832> {0}\n'
                  '`Брать кинцо` <:cruzhulk:230370931065749514> {1}'.format(cytube_url, movies_url))


@bot.command(hidden=True)
async def shles():
    """SHLES"""
    await bot.say(dbClient.get_link('shles'))


@bot.command(hidden=True)
async def asteroids():
    """Показывает топ игрока epicvertigo.xyz/asteroids.html"""
    topPlayer = PlayFab.GetLeaderboard(credentials['PlayFabTitleID'])
    if topPlayer is not None:
        await bot.say("Top Asteroids player: {} with {} points".format(topPlayer['DisplayName'], topPlayer['StatValue']))


@bot.command(pass_context=True)
async def avatar(ctx, mention=None):
    """Показывает аватарку юзера"""
    if mention == None:
        await bot.say(ctx.message.author.avatar_url)
        return
    if len(mention) is not 21 and len(mention) is not 22:
        await bot.say('`Как юзать - !avatar @User`')
        return
    if mention[2] == '!':
        mention = mention.replace('!', '')
    user = None
    for member in ctx.message.server.members:
        if member.id == mention[2:20]:
            user = member
    if user == None:
        await bot.say('`Нет такого юзера на сервере`')
    else:
        if user.avatar_url == '':
            await bot.say('`У юзера нет аватарки`')
        else:
            await bot.say(user.avatar_url)


@bot.command()
async def ip():
    """Напомните ип плс"""
    await bot.say(dbClient.get_entry_by_key(db.settings_table, 'ip') + ' <:OSsloth:230773934197440522>')


@bot.group(pass_context=True)
async def mix(ctx):
    """Mixes !hb and !wisdom commands"""
    if not ctx.invoked_subcommand:
        await bot.say('{0}\n{1}'.format(dbClient.get_random_row(db.wisdom_table),
                                        dbClient.get_random_picture()))


@bot.command(pass_context=True, hidden=True)
async def low(ctx):
    if ctx.message.author.id == '127135903125733376':
        await bot.say('https://i.imgur.com/Ym97yDB.png')
    else:
        await bot.say('<:bearrion:230370930600312832>')


@bot.group(pass_context=True)
async def ow(ctx):
    """Overwatch Rank"""
    if ctx.invoked_subcommand is None:
        playerBase = dbClient.get_game_profiles('blizzard_id')
        if ctx.message.content == '!ow':
            if ctx.message.author.id in playerBase:
                message = await TonyCommands.ow_rank(ctx.message.author.id, playerBase)
                await bot.say('`{0}, Current rank {1}`'.format(ctx.message.author.name, message))
            return
        else:
            content = ctx.message.content
            mention = content.split('!ow ')[1][2:20]
            if mention == '!22383766718644224':
                await bot.say('Я не играю в это говно <:ded:237151960359370753>')
                return
            if len(mention) is not 18 or not mention.isdigit():
                await bot.say('`How to use - !ow @User`')
                return
            if mention in playerBase:
                message = await TonyCommands.ow_rank(mention, playerBase)
                await bot.say('`{0}, Current rank {1}`'.format(playerBase[mention].split('-')[0], message))
            else:
                await bot.say("Can't find player in database")


@ow.command(pass_context=True)
async def ladder():
    global ow_lock
    if not ow_lock:
        playerBase = dbClient.get_game_profiles('blizzard_id')
        ow_lock = True
        tmp = await bot.say('`Loading player list 0/{}`'.format(len(playerBase)))
        playerNum = 0
        lad = {}
        for id in playerBase:
            lad[playerBase[id].split('-')[0]] = await TonyCommands.ow_rank(id, playerBase)
            playerNum += 1
            await bot.edit_message(tmp, '`Loading player list {0}/{1}`'.format(str(playerNum), len(playerBase)))
        lad = {k: v for k, v in lad.items() if v is not None}
        sortedLadder = sorted(lad.items(), key=lambda x: x[1], reverse=True)
        average = 0
        messageText = str()
        for x in sortedLadder:
            messageText += '    {0} - {1}\n'.format(x[1], x[0])
            average += int(x[1])
        average = round(average / len(sortedLadder))

        await bot.edit_message(tmp, '<:OSsloth:230773934197440522> \n```xl\nOverwatch rankings\n\n{0}\nСредняя температура по больнице - {1}```'.format(messageText, average))
        ow_lock = False


@bot.group(pass_context=True)
async def gachi(ctx):
    """Take it boy"""
    if not ctx.invoked_subcommand:
        await bot.say(dbClient.get_random_row(db.gachi_table))


@gachi.command(pass_context=True)
@admin_command
async def add(ctx, url: str):
    # Add regex for links
    await bot.say(dbClient.add_value_to_table(db.gachi_table, url))


@bot.command(hidden=True)
async def firstrule():
    await bot.say('Never hook first <:smart:282452131552690176>')


@bot.command(hidden=True)
async def secondrule():
    await bot.say("You can't counter Pharah <:Kappa:230228691945390080>")


@bot.command(hidden=True)
async def thirdrule():
    await bot.say("Ко мне говно <:4Head:230227653783846912>")


@bot.group(pass_context=True)
async def wiki(ctx):
    """Википедия в Дискорде, не отходя от кассы"""
    article = str(ctx.message.content).replace('!wiki ', '')
    if not ctx.invoked_subcommand:
        if article == '!wiki':
            await bot.say('`Пример использования "!wiki Дупель"`')
        else:
            try:
                await bot.say('`{}`'.format(TonyCommands.wiki(article)[0]))
            except Exception as e:
                logger.error(e)
                await bot.say(str(e))


@wiki.command()
async def lang(string: str):
    """Сменить язык Вики (Доступные языки - en, ru, uk, el)"""
    await bot.say(TonyCommands.wikibotlang(string))


@wiki.command(pass_context=True)
async def link(ctx):
    """Выдать ссылку на статью (если она существует)"""
    wikireq = str(ctx.message.content).replace('!wiki link ', '')
    await bot.say(TonyCommands.wiki(wikireq)[1])


@bot.group(pass_context=True)
async def hb(ctx):
    """Нет слов"""
    if not ctx.invoked_subcommand:
        await bot.say(dbClient.get_random_picture())


@hb.command()
async def update():
    """Обновить список картинок из альбома ХБ"""
    piclist = imgur_hb.get_album(credentials['imgur'])
    if not piclist or not isinstance(piclist, dict):
        update_error = "Can't update piclist.{}".format(piclist)
        logger.error(update_error)
        await bot.say(update_error)
    else:
        dbClient.update_imgur(piclist)
        await bot.say('`Лист обновлен. {} картинок в альбоме`'.format(len(piclist)))


@bot.group(pass_context=True)
async def wisdom(ctx):
    """Спиздануть мудрость клоунов"""
    if not ctx.invoked_subcommand:
        await bot.say(dbClient.get_random_row(db.wisdom_table))


@wisdom.command(pass_context=True)
async def add(ctx):
    """Добавить новую мудрость клоунов"""
    wisdomLine = ctx.message.content.split(
        ctx.command.qualified_name)[1].strip()
    await bot.say(dbClient.add_new_entry(db.wisdom_table, wisdomLine, ctx.message.author.id))


@wisdom.command(pass_context=True, hidden=True)
@admin_command
async def remove(ctx):
    """Removes wisdom by given id in ctx"""
    idToRemove = ctx.message.content.split(
        ctx.command.qualified_name)[1].strip()
    if idToRemove.isdigit():
        await bot.say(dbClient.remove_entry(db.wisdom_table, idToRemove))


@wisdom.command(hidden=True, pass_context=True)
@admin_command
async def info(ctx):
    """Shows 5 last wisdoms with id and author's name and some info"""
    cachedNicknames = dbClient.get_cached_nicknames(db.nicknames_table)
    lastAddedWisdom = dbClient.get_last_row(db.wisdom_table)
    wisdomCount = dbClient.get_row_count(db.wisdom_table)

    if not cachedNicknames or datetime.now() - datetime.strptime(cachedNicknames[0][2], '%Y-%m-%d %H:%M:%S') > timedelta(1):
        dbClient.update_cached_nicknames(bot.servers)
        cachedNicknames = dbClient.get_cached_nicknames(db.nicknames_table)
        dbClient.refresh_wisdom_history()
    await bot.say(await wisdom_info_formatter(dbClient.lastwisdoms, bot, cachedNicknames, lastAddedWisdom, wisdomCount))


@wisdom.command(hidden=True, pass_context=True)
@admin_command
async def update(ctx):
    dbClient.update_cached_nicknames(bot.servers)
    await bot.say(dbClient.refresh_wisdom_history())


@bot.group(pass_context=True)
async def brawl(ctx):  # Randomly generated brawl
    """Kill me pls"""
    if not ctx.invoked_subcommand:
        await bot.say(google_brawl.randomize_phrase(brawl_list))


@brawl.command()
async def update():
    global brawl_list
    """Обновить текущий словарь"""
    brawl_list = google_brawl.check_for_updates(dbClient)
    if brawl_list:
        await bot.say('`Lists are successfully updated`')
    else:
        await bot.say("`Something wrong with brawl lists. Please check logs for more info`")


@brawl.command()
async def info():
    """Ссылка на файл со словарем"""
    await bot.say(dbClient.get_link('brawl_sheet'))


@bot.command()
async def roll():  # Roll int() from 1 to 100
    """Ролит число от 1 до 100"""
    rollresult = random.randint(1, 100)
    await bot.say(rollresult)


@bot.command()
async def friday():
    """Время в задницу"""
    await bot.say(dbClient.get_link('friday'))


@bot.command()
async def choose(*choices: str):
    """Выбор между стульями"""
    await bot.say(random.choice(choices))


@bot.command()
async def free():
    """Святые писания"""
    await bot.say('`Живи молодым и умри молодым` {}'.format(dbClient.get_link('free')))


@bot.group(pass_context=True)
async def kf(ctx):
    """Ссылка на файл статистики по КФ2"""
    if not ctx.invoked_subcommand:
        await bot.say(dbClient.get_link('kf2'))


@kf.command()
async def update():  # Update kf2 gdrive file
    """Обновить файл статистики по КФ2"""
    global extScriptLock
    if extScriptLock == True:
        await bot.say("`Скрипт еще работает, не задрачивай меня`")
    if extScriptLock == False:
        # extScriptLock = await SteamStats.BotUpdate({"GAMEID":"252950","WSNAME":"Rocket League",'GSNAME':'Steam Achievements', 'fix_icons':False, 'firstTime':False, 'decorate':False, 'nodesc':False})
        p = subprocess.Popen(["python3", "SteamStats.py",
                              "-g", "232090",
                              "-ws", "KF2"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        await bot.say("`Скрипт запущен, помолимся.`")
        logger.info('[KFGOOGLE]: Script started')
        extScriptLock = True
        sleeptime = 5
        while p.poll() == None:
            await asyncio.sleep(sleeptime)
        else:
            await bot.say("`Таблицы ачивок обновлены`")
            extScriptLock = False
            logger.info('[KFGOOGLE]: Script finished')


@bot.command(pass_context=True)
@admin_command
async def game(ctx, *args):  # Change game in status
    """Сменить боту игру"""
    name = ' '.join(args)
    if not args:
        await bot.say('`How to use: "!game Game Name"`')
    else:
        await bot.say(dbClient.set_game(name))
        await bot.change_presence(game=discord.Game(name=name))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

if __name__ == '__main__':
    logger.info('Script started')

    dbClient = db.Client()
    brawl_list = google_brawl.check_for_updates(dbClient)

    credentials = bot_init.get_credentials()
    dbClient.update_imgur(imgur_hb.get_album(credentials['imgur']))

    extScriptLock = False
    ow_lock = False

    bot.run(credentials['token'])

