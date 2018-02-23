import json
import requests
import gspread
import oauth2client
from oauth2client.service_account import ServiceAccountCredentials
import time
import argparse
import logging
start_time = time.time()

logger = logging.getLogger('stats')
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(filename='logs/steamstats.log', encoding='utf-8', mode='w')
handler.setLevel(logging.DEBUG)

console = logging.StreamHandler()
console.setLevel(logging.INFO)

formatter = logging.Formatter(fmt = '[%(asctime)s] [%(levelname)s] %(message)s', datefmt = '%I:%M:%S')
handler.setFormatter(formatter)
console.setFormatter(formatter)

logger.addHandler(handler)
logger.addHandler(console)

logger.info ('Script started')

parser = argparse.ArgumentParser()
parser.add_argument('-i','--fix-icons', help='only fixing icons', action='store_true')
parser.add_argument('-d','--decorate', help='decorate google spreadsheet for first use', action='store_true')
parser.add_argument('-n','--nodesc', help='only fixing icons', action='store_true') #Some games doesn't actually have descriptions
parser.add_argument('-g','--game', help='other game id', action='store', dest='GAMEID', required=False, default='232090')
parser.add_argument('-gs','--spreadsheet', help='use another spreadsheet', dest='GSNAME', default='Steam Achievements')
parser.add_argument('-ws','--worksheet', help='use another worksheet', dest='WSNAME', required=False, default='KF2')
parser.add_argument('-v','--version', action='version', version='1.3')
args = vars(parser.parse_args())
logger.debug(args)

with open('credentials.json','r', encoding='utf-8') as jsonFile:
            credentials = json.load(jsonFile)
with open('StatsFiles/data.json','r', encoding='utf-8') as jsonFile:
            settings = json.load(jsonFile)
master = {}
gameSettings = {}
gameName = None
ws = None
STEAM_API_KEY = credentials['steamAPI']
PLAYER_ACHIEVMENTS_URL = 'http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/'
ALLPLAYERS = settings['steam']['users']

def openGameSettingsFile():
    """Open GameSettings file for given GAMEID"""
    global gameSettings
    try:
        with open('StatsFiles/'+args['GAMEID']+'.json','r',encoding='utf-8') as f:
            gameSettings = json.load(f)
        if not 'selfCreated' in gameSettings or not gameSettings['selfCreated']:
            logger.warning('Settings file is wrong or corrupted')
            createGameSettingsFile()
        else:
            logger.info('Game Settings file loaded')
    except OSError:
        createGameSettingsFile()

def saveGameSettingsFile(gameSettings):
    with open('StatsFiles/'+args['GAMEID']+'.json','w+',encoding='utf-8') as jsonFile:
            jsonFile.write(json.dumps(gameSettings,sort_keys=True, indent=4,ensure_ascii=False))
    logger.info('Game Settings saved')

def createGameSettingsFile():
    """Create Settings file for given GAMEID"""
    global gameSettings
    logger.info('Creating new Game Settings file for current game')
    convertDict = settings['steam']['convert']
    gameSettings = {}
    statsBlock = {}
    users = {}
    index = 4
    stats_index = 1
    for player in ALLPLAYERS:
        current = ALLPLAYERS[player]
        payload = {'key':STEAM_API_KEY,'appid':args['GAMEID'],'steamid':current['SteamID']}
        r = requests.get(PLAYER_ACHIEVMENTS_URL,params=payload)
        data = json.loads(r.text)
        if data['playerstats']['success']:
            print(player)
            users[player] = {}
            users[player]['index'] = index
            users[player]['letter'] = convertDict[str(index)]
            index += 1
            users[player]['statsIndex'] = stats_index
            stats_index += 1
            users[player]['SteamID'] = current['SteamID']
    statsBlock['Name'] = convertDict[str(index)]
    statsBlock['Done'] = convertDict[str(index+1)]
    statsBlock['Undone'] = convertDict[str(index+2)]
    statsBlock['Percent'] = convertDict[str(index+3)]
    statsBlock['Total'] =convertDict[str(index+4)]
    gameSettings['stats'] = statsBlock
    gameSettings['users'] = users
    gameSettings['firstRow'] = len(gameSettings['users']) + 1
    gameSettings['achOffset'] = len(gameSettings['users'])
    gameSettings['selfCreated'] = True
    gameSettings['firstTime'] = True
    saveGameSettingsFile(gameSettings)

def authorizeGoogle():
    """Authorize into Google Drive"""
    global ws
    logger.info ('Logging into Google Drive...')
    scope = ['https://spreadsheets.google.com/feeds']
    try:
        gcredentials = ServiceAccountCredentials.from_json_keyfile_name('google-drive.json', scope)
        gs = gspread.authorize(gcredentials)
        ws = gs.open(args['GSNAME']).worksheet(args['WSNAME'])
    except gspread.SpreadsheetNotFound:
        logger.error ("Can't open a file with given name")
        quit()
    if ws:
        logger.info ('Google Spreadsheet opened')
        
def getMasterDict():
    """Get dictionary of global achievements"""
    global master, gameName
    logger.info ('Fetching master list of achievements...')
    r = requests.get('http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v0002/?key={0}&appid={1}&l=english&format=json'.format(STEAM_API_KEY,args['GAMEID']))
    data = json.loads(r.text, encoding='utf-8')
    master = data['game']['availableGameStats']['achievements']
    gameName = data['game']['gameName']
    logger.info('Game {d[game][gameName]}, version {d[game][gameVersion]}, total {len} achievements'.format(d=data,len=len(master))) #Some games may fail cause of 'tm' shit

def checkABC():
    """Checking gspread file columns A, B and C"""
    logger.info ('Checking gspread file columns A, B and C...')
    listA = list(filter(None,ws.col_values(1)))
    del listA [:2]
    listB = list(filter(None,ws.col_values(2)))
    del listB [:1]

    if len(listA) < len(master):
        fixABC('A', master, 'displayName')
    else:
        fastCheckABC(listA, 'A', master, 'displayName')
    if not args['nodesc']:
        if len(listB) < len(master):
            fixABC('B', master, 'descriptionv')
        else:
            fastCheckABC(listB, 'B', master, 'description')
    if len(listA) < len(master) or len(listB) < len(master) and not args['nodesc']:
        fixABC('C', master, 'icon')

    logger.info('ABC checked')

def fixABC(letter,data,content):
    """Update full column or cell_range for given letter"""
    count = 0
    cell_range = ws.range('{0}{2}:{0}{1}'.format(letter,str(len(data)+gameSettings['achOffset']),gameSettings['firstRow']))
    if letter == 'C':
        for cell in cell_range:
            cell.value = '=IMAGE("{}",2)'.format(data[count][content])
            count +=1
    else:
        for cell in cell_range:
            try:
                cell.value = data[count][content]
            except KeyError:
                cell.value = "Hidden achievment"
            count +=1
    ws.update_cells(cell_range)
    logger.info ('Full column {} updated'.format(letter))

def fastCheckABC(compareList,letter,data,content):
    """Fast compare with master dictionary"""
    changes = 0
    for i in range(len(compareList)):
        try:
            if compareList[i] != data[i][content]:
                ws.update_acell('{0}{1}'.format(letter,str(i+gameSettings['firstRow'])),data[i][content])
                logger.info('{0} {1} changed'.format(content.capitalize(),data[i][content]))
                changes +=1
                if changes >=5:
                    fixABC(letter,data,content)
                    break
        except KeyError:
            pass

def playerCheck():
    """Check each player's achievements in gameSettings['users']"""
    logger.info('Checking each player in gameSettings["users"]...')
    for player in gameSettings['users']:
        logger.info('Checking {}...'.format(player))
        current = gameSettings['users'][player]
        payload = {'key':STEAM_API_KEY,'appid':args['GAMEID'],'steamid':current['SteamID']}
        r = requests.get(PLAYER_ACHIEVMENTS_URL,params=payload)
        data = json.loads(r.text)
        achievements = data['playerstats']['achievements']

        listPlayer = list(filter(None,ws.col_values(current['index'])))
        del listPlayer [:1]

        if len(listPlayer) < len(master):
            playerFullColumn(current,achievements,player)
            logger.info('Fixing statistics block for {}'.format(player))
            stats = gameSettings['stats']
            ws.update_acell('{0}{1}'.format(stats['Done'],current['statsIndex']),'=COUNTIF({0}{1}:{0}{2}, "1")'.format(current['letter'],gameSettings['firstRow'],len(master)+gameSettings['achOffset']))
            ws.update_acell('{0}{1}'.format(stats['Undone'],current['statsIndex']),'=COUNTIF({0}{1}:{0}{2}, "0")'.format(current['letter'],gameSettings['firstRow'],len(master)+gameSettings['achOffset']))
            ws.update_acell('{0}{1}'.format(stats['Percent'],current['statsIndex']),'={2}{0}/{1}'.format(current['statsIndex'],len(master),stats['Done']))
            ws.update_acell('{0}1'.format(stats['Total']),'=SUM({2}1:{2}{0})/({1}*{0})'.format(len(gameSettings['users']),len(master),stats['Done']))
        else:
            changes = 0
            for i in range(len(listPlayer)):
                if int(listPlayer[i]) != achievements[i]['achieved']:
                    ws.update_acell('{0}{1}'.format(current['letter'],str(i+gameSettings['firstRow'])),achievements[i]['achieved'])
                    logger.info('{0} achieved {1}'.format(player,master[i]['displayName']))
                    changes +=1
                    if changes >= 5:
                        playerFullColumn(current,achievements,player)
                        break
    logger.info('Players checked')

def playerFullColumn(current,achievements,player):
    """Update full column or cell_range for player"""
    count = 0
    cell_range = ws.range('{0}{2}:{0}{1}'.format(current['letter'],str(len(achievements)+gameSettings['achOffset']),gameSettings['firstRow']))
    for cell in cell_range:
        cell.value = achievements[count]['achieved']
        count +=1
    ws.update_cells(cell_range)
    logger.info('Column {0} for player {1} changed'.format(current['letter'],player))

def decorate():
    """Prepare document for first use"""
    logger.info('Decorating file for the first use...')
    ws.update_acell('A1',gameName)
    ws.update_acell('A{}'.format(gameSettings['achOffset']),'Achievement')
    ws.update_acell('B{}'.format(gameSettings['achOffset']),'Description')
    ws.update_acell('{0}1'.format(gameSettings['stats']['Total']),'=SUM({2}1:{2}{0})/({1}*{0})'.format(len(gameSettings['users']),len(master),gameSettings['stats']['Done']))
    for player in gameSettings['users']:
        current = gameSettings['users'][player]
        ws.update_acell('{0}{1}'.format(current['letter'],gameSettings['achOffset']), player)
        ws.update_acell('{0}{1}'.format(gameSettings['stats']['Name'],current['statsIndex']), player)
    gameSettings['firstTime'] = False
    saveGameSettingsFile(gameSettings)
        
def fixIcons():
    """Fix column C"""
    openGameSettingsFile()
    getMasterDict()
    fixABC('C', master, 'icon')

if __name__ == '__main__':
    if args['fix_icons']:
        logger.warning('This script will only fix icons in gspread file')
        authorizeGoogle()
        fixIcons()
        logger.info('Icons fixed')
    else:        
        openGameSettingsFile()
        authorizeGoogle()
        getMasterDict()
        if gameSettings['firstTime'] or args['decorate']:
            decorate()
        checkABC()
        playerCheck()
        logger.debug ('Done in {0}'.format(round(time.time() - start_time, 2)))
    quit()
