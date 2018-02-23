import logging
from datetime import datetime

from imgurpython import ImgurClient
from .utils import botExceptionCatch

logger = logging.getLogger(__name__)

def convert_time(unixtime):
    """Convert posix time to datetime for database record"""
    return datetime.fromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')

@botExceptionCatch
def get_album(credentials):
    client = ImgurClient(credentials['id'], credentials['secret'])
    data = client.get_album_images(credentials['album'])
    if len(data) == 0: 
        return None
    pictures = {x.link : x.datetime for x in data}
    logger.info ('[IMGURHB] List updated with {0} pictures'.format(len(pictures)))
    logger.info ('[IMGURHB] Client limits are 12500/{0}'.format(client.credits['ClientRemaining']))
    return pictures

def limits(credentials):
    client = ImgurClient(credentials['id'], credentials['secret'])
    limits = client.credits
    return limits