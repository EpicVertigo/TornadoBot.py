"""Module for brawl command"""

import logging
from random import choice

import gspread
from apiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

from TonyBot.db import settings_table

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def authorize_google(settings):
    try:
        gscope = ['https://spreadsheets.google.com/feeds',
                  'https://www.googleapis.com/auth/drive.metadata.readonly']
        gcredentials = ServiceAccountCredentials.from_json_keyfile_name(
            settings['json'], gscope)
        service = discovery.build('drive', 'v3', credentials=gcredentials)
        response = service.changes().list(pageToken=settings['token']).execute()
        logger.debug(response)
        logger.info('[GSPREAD] Current state: {0}, New state: {1}'.format(
            settings['token'], response['newStartPageToken']))
        return gcredentials, response
    except Exception as e:
        logger.error('[{0}] {1}'.format(__name__, e))
        return None, None


def read_spreadsheet(gcredentials, spreadsheet, dbClient):
    try:
        gcs = gspread.authorize(gcredentials)
        brawl_sh = gcs.open(spreadsheet).sheet1
        # Get raw data from google sheet
        raw_data = [list(brawl_sh.col_values(i+1)) for i in range(brawl_sh.col_count)]
        # Filter lists for empty cells
        filtered_data = list(list(filter(None, column)) for column in raw_data)

        if 0 in list(map(len, filtered_data)):
            logger.error("[GSPREAD] Brawl lists can't be empty!")
            return None
        else:
            dbClient.update_brawl_table(raw_data)
            return filtered_data
    except Exception as e:
        logger.error('[{0}] {1}'.format(__name__, e))
        return None


def check_for_updates(dbClient):
    settings = dbClient.get_brawl_settings()
    gcredentials, response = authorize_google(settings)
    
    if response is not None and 'newStartPageToken' in response:

        # Use cached table if response token is the same as saved one
        if settings['token'] == response.get('newStartPageToken'):
            logger.info('[GSPREAD] Brawl lists are the same.')
            return dbClient.get_brawl_table()

        # Update token if token is different, but brawl spreadsheet is not in response
        elif settings['token'] != response.get('newStartPageToken') and settings['spreadsheet'] not in str(response):
            logger.info('[GSPREAD]: Brawl dictionary is not in response. New page token is {}'.format(
                response.get('newStartPageToken')))
            logger.info('[GSPREAD]: Brawl lists are the same.')
            dbClient.set_entry_by_key(settings_table, response.get('newStartPageToken'), 'token')
            return dbClient.get_brawl_table()

        # Try to get new brawl_list and update db table
        else:
            brawl_list = read_spreadsheet(gcredentials, settings['spreadsheet'], dbClient)
            if brawl_list is not None:
                dbClient.set_entry_by_key(settings_table, response.get('newStartPageToken'), 'token')
                logger.info('[GSPREAD] Brawl lists updated.')
            else:
                logger.error("[GSPREAD] Using cached brawl table")
                brawl_list = dbClient.get_brawl_table()
            return brawl_list
    else:
        logger.error("Can't connect to google drive. Please check logs for more info")
        brawl_list = dbClient.get_brawl_table()
        return brawl_list


def randomize_phrase(brawl_list):
    message = '{r[0]} {r[1]} {r[2]} {r[3]} и {r[4]} {r[5]}'
    if brawl_list:
        phrase_list = [choice(x) for x in brawl_list]
        return message.format(r=phrase_list)
    else:
        return ('`Something wrong with brawl lists. Please check logs for more info`')
