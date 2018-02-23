import logging
import time
from functools import wraps
from sqlite3 import IntegrityError, OperationalError

logger = logging.getLogger(__name__)

def botExceptionCatch(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as e:
            logger.error(func.__name__ +  str(e))
            return e.args
        except OperationalError as e:
            logger.error(func.__name__ +  str(e))
            return 'Database is locked'
        except IntegrityError as e:
            logger.error(func.__name__ +  str(e))
            return 'ERROR: {0}'.format(e.args)   
        except Exception as e:
            logger.error(func.__name__ +  str(e))
            return str(e)
    return wrapper

def admin_command(func):
    """Checks if command executed by admin or bot's owner"""
    @wraps(func)
    async def decorated(*args, **kwargs):
        try:
            if args[0].message.author.id == '121371550405361664':
                return await func(*args, **kwargs)
        except Exception as e:
            logger.error(e)
    return decorated

# monkaS
async def wisdom_info_formatter(wisdomHistory, bot, cache, lastWisdomAdded, wisdomCount):
    pyformat = '```py\n{}```'
    message = '{0:<4} : {1:^18} : {2:^35}\n'.format(
                'ID','Author','Wisdom Text')
    
    if len(wisdomHistory) != 0:
        message += '\nLast wisdoms (Max limit: {0})\n'.format(wisdomHistory.maxlen)
        for item in wisdomHistory:
            id = item[3]
            authorName = check_author_name(id, cache)
            wisdom = item[2].replace('\n', '')
            if len(wisdom) > 35:
                wisdom = '{0:.32}...'.format(wisdom)
            message += '{0[0]:<4} : {1:^18} : {2:35}\n'.format(item, authorName, wisdom)

    message += '\nLast added wisdom:\n{0[0]:<4} : {1:^18} : {0[2]:35}\n\nTotal wisdoms: {2}'.format(
                    lastWisdomAdded, check_author_name(lastWisdomAdded[3], cache), wisdomCount)
    return pyformat.format(message)

def check_author_name(id, cache):
    for item in cache:
        if id == item[0]:
            return item[1]
    else:
        return id


def compare_timestamps(timestamp):
    difference = time.time() - timestamp
    if difference > 16070400:
        return 3
    elif difference > 7776000:
        return 2
    else:
        return 1
