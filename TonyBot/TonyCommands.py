import asyncio
import datetime
import json
import logging
import random
import statistics
import time

import aiohttp
import bs4
import gspread
import requests
import wikipedia
from bs4 import BeautifulSoup

from .utils import botExceptionCatch
from TonyBot import db

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def ow_rank(id, playerBase):
    """OW rank checker"""
    if id in playerBase:
        blizzID = playerBase[id]
        link = 'https://playoverwatch.com/en-gb/career/pc/eu/' + blizzID
        async with aiohttp.get(link) as r:
            try:
                text = await r.text()
                soup = BeautifulSoup(text, 'html.parser')
                result = soup.find("div", {"class": "competitive-rank"}).text
            except:
                result = None
        return result
    else:
        result = "Can't find player in database"
    return result


# CRIT

# Redo for multi-server 

# def createNewEntry(users, name):
#     users[name] = {'crits': 0, 'dodges': 0, 'parries': 0}


# def getResult(victim, server, d):
#     users = d['users']
#     critChance = d['critChance']
#     dodgeChance = d['dodgeChance']
#     parryChance = d['parryChance']

#     if not victim in users:
#         createNewEntry(users, victim)
#     if random.randint(1, 100) <= dodgeChance:
#         users[victim]['dodges'] += 1
#         msg = '*{0} увернулся от крита [{1}]* <:PogChamp:230227769127075840>'.format(
#             victim, users[victim]['dodges'])

#     elif random.randint(1, 100) <= parryChance and server:
#         templist = []
#         for member in server.members:
#             if member.status.value == 'online':
#                 templist.append(member.name)
#         templist.remove(victim)
#         parryVictim = random.choice(templist)
#         users[victim]['parries'] += 1
#         if not parryVictim in users:
#             createNewEntry(users, parryVictim)
#             users[parryVictim]['crits'] += 1
#         else:
#             users[parryVictim]['crits'] += 1
#         msg = '*{0} спарировал крит в {1} [{2}]* <:PogChamp:230227769127075840>'.format(
#             victim, parryVictim, users[victim]['parries'])

#     else:
#         users[victim]['crits'] += 1
#         msg = '*Кританул по {0} [{1}]* <:4Head:230227653783846912>'.format(
#             victim, users[victim]['crits'])
#     return msg


# def readCritCount(d):
#     templist = []
#     for key in d:
#         templist.append('{0} - {1}'.format(key, d[key]['crits']))
#     msg = '`Положняк по критам ' + ', '.join(templist) + '`'
#     return msg


# WIKIPEDIA
wikipedia.set_lang('ru')

def wiki(article):
    try:
        wikiresult = wikipedia.summary(article).split('\n')[0]
        wikilink = wikipedia.page(article).url
    except wikipedia.exceptions.DisambiguationError as e:
        wikiresult = str(str(e).split(': \n')[1].split('\n')).strip('[]')
        if len(wikiresult) >= 250:
            wikiresult = 'Слишком много результатов, попробуй запрос поточнее'
        wikilink = 'Слишком много результатов чтобы выдать ссылку, попробуй поточнее'
    except Exception as ex:
        wikiresult = str(ex)
        wikilink = str(ex)
    return wikiresult, wikilink


def wikibotlang(language):
    wronglang = False
    tempdict = {}
    try:
        if language.lower() in ('english', 'en', 'eng', 'английский'):
            language = 'en'
            tempdict['en'] = 'Английский'
        elif language.lower() in ('russian', 'ru', 'rus', 'русский'):
            language = 'ru'
            tempdict['ru'] = 'Русский'
        elif language.lower() in ('ukraininan', 'ua', 'ukr', 'uk', 'украинский'):
            language = 'uk'
            tempdict['uk'] = 'Украинский'
        elif language.lower() in ('greek', 'gr', 'el', 'греческий'):
            language = 'el'
            tempdict['el'] = 'Греческий'
        else:
            wronglang = True
            language = 'ru'
            tempdict['ru'] = 'Русский'
        if wronglang:
            wikilangerror = '`Доступные варианты языков - Английский, Русский, Украинский и Греческий (en,ru,uk,el)`'
            return wikilangerror
        else:
            wikipedia.set_lang(language)
            wikilangerror = '`Язык изменен на {}`'.format(tempdict[language])
            return wikilangerror
    except Exception as e:
        logger.error(str(e))
        wikilangerror = '`Не могу изменить язык на {}`'.format(language)
        return wikilangerror


# def shuffleDict(dictionary):
#     zaloop = True
#     if len(dictionary) == 0:
#         zaloop = False
#         logger.warning(
#             'You are trying to do shuffleDict() with empty dictionary')
#     while zaloop:
#         if statistics.mean(list(dictionary.values())) == 1:
#             for item in dictionary.keys():
#                 dictionary[item] = 0
#         frandom = random.choice(list(dictionary.keys()))
#         values = list(dictionary.values())
#         fkey = dictionary[frandom]
#         if fkey > statistics.mean(values):
#             continue
#         elif fkey <= statistics.mean(values):
#             dictionary[frandom] = fkey + 1
#             return frandom
