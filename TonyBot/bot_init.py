import logging
import json
logger = logging.getLogger('TonyBot')
logger.setLevel(logging.DEBUG)


def get_credentials():
    """Get credentials from file"""
    try:
        with open('credentials.json', 'r', encoding='utf-8') as jsonPrivate:
            credentials = json.load(jsonPrivate)
            return credentials
            logger.debug('Credentials loaded')
    except Exception as e:
        logger.error(e)


def get_data():
    """Get data"""
    try:
        with open('TonyBot/data.json', 'r', encoding='utf-8') as jsonFile:
            data = json.load(jsonFile)
            logger.debug('Data loaded')
            return data
    except Exception as e:
        logger.error(e)


def save_data(data):
    """Save data"""
    try:
        with open('TonyBot/data.json', 'w+', encoding='utf-8') as jsonFile:
            jsonFile.write(json.dumps(data, sort_keys=True,
                                      indent=4, ensure_ascii=False))
            logger.debug('Data saved')
    except Exception as e:
        logger.error(e)
