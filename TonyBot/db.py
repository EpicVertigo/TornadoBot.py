import sqlite3
import string
from collections import namedtuple, deque
from .utils import botExceptionCatch, compare_timestamps
import logging
logger = logging.getLogger(__name__)

TABLE = namedtuple('Table', 'name key value author timestamp')
wisdom_table = TABLE(name='wisdom', key=None, value='text', author='author', timestamp='date')
imgur_table = TABLE(name='imgur', key=None, value='url', author=None, timestamp='date')
gachi_table = TABLE(name='gachi', key=None, value='url', author=None, timestamp=None)
nicknames_table = TABLE(name='cached_nicknames', key=None, value='id', author='display_name', timestamp='date')
settings_table = TABLE(name='settings', key='key', value='value', author=None, timestamp=None)
links_table = TABLE(name='links', key='key', value='url', author=None, timestamp=None)
brawl_table = TABLE(name='brawl', key=None, value=None, author=None, timestamp=None)


class Client(object):
    """ A class for TonyBot sqlite3 client"""

    def __init__(self, database='data.db'):
        self.database = database
        self.connection = sqlite3.connect(self.database)
        self.cursor = self.connection.cursor()
        self.lastwisdoms = deque([], maxlen=5)
        #self.connection.set_trace_callback(print)
        logger.info('Connected to DB')

    # Client commands for sqlite3 botDB
    @property
    def cmd_get_random_row(self):
        """Gets random row from a table with 'pID' column"""
        return 'SELECT rowid, * FROM {0.name} WHERE pID = 0 ORDER BY random() LIMIT 1'

    @property
    def cmd_get_table(self):
        """Gets whole table"""
        return 'SELECT * FROM {0.name}'

    @property
    def cmd_get_by_ID(self):
        """Gets DB entry by given ID"""
        return 'SELECT * FROM {0.name} WHERE rowid=?'

    @property
    def cmd_get_last_wisdom(self):
        """Gets DB entry by given ID (with rowid)"""
        return 'SELECT rowid, * FROM {0.name} WHERE rowid=?'

    @property
    def cmd_reset_PIDs(self):
        """Updates PID column with zeroes"""
        return 'UPDATE {0.name} SET pID = 0'

    @property
    def cmd_update_PID(self):
        """Updates entry's PID"""
        return 'UPDATE {0.name} SET pID=? WHERE rowid=?'

    @property
    def cmd_add_new_wisdom(self):
        """Adds new entry to given table with TABLE format"""
        return 'INSERT INTO {0.name}({0.value}, {0.author}, {0.timestamp}) VALUES(?, ?, current_timestamp)'

    @property
    def cmd_remove_row(self):
        """Removes entry by given rowid"""
        return 'DELETE FROM {0.name} WHERE rowid=?'

    @property
    def cmd_delete_table(self):
        """Removes sqlite3 database"""
        return 'DELETE FROM {0.name}'

    @property
    def cmd_add_new_row(self):
        """Adds new row list to table"""
        return 'INSERT INTO {0.name}({0.value}) VALUES (?)'

    @property
    def cmd_get_last_row(self):
        """Returns last row in table"""
        return 'SELECT rowid,* FROM {0.name} WHERE rowid = (SELECT MAX(rowid) FROM {0.name})'

    @property
    def cmd_get_row_count(self):
        """Gets row count"""
        return 'SELECT (SELECT COUNT() FROM {0.name}) as count'

    @property
    def cmd_get_by_key(self):
        """Gets value from table by key"""
        return 'SELECT {0.value} FROM {0.name} WHERE {0.key}=?'

    @property
    def cmd_set_by_key(self):
        """Sets value in table by given key"""
        return 'UPDATE {0.name} SET {0.value}=? WHERE {0.key}=?'

    # Client methods
    @botExceptionCatch
    def get_last_row(self, table):
        """Gets last row in table"""
        return self.cursor.execute(self.cmd_get_last_row.format(table)).fetchall()[0]

    @botExceptionCatch
    def get_row_count(self, table):
        """Gets row count from table"""
        return self.cursor.execute(self.cmd_get_row_count.format(table)).fetchall()[0][0]

    @botExceptionCatch
    def refresh_wisdom_history(self):
        """Updates current lastwisdom deque if wisdom table changes"""
        tempIDs = [x[0] for x in self.lastwisdoms]
        self.lastwisdoms.clear()
        for id in tempIDs:
            self.cursor.execute(
                self.cmd_get_last_wisdom.format(wisdom_table), (id,))
            self.lastwisdoms.append(self.cursor.fetchall()[0])
        return "Wisdom queue updated"

    @botExceptionCatch
    def get_random_row(self, table):
        """Gets random row with PID 0"""
        randomRow = self.cursor.execute(
            self.cmd_get_random_row.format(table)).fetchall()
        if randomRow:
            result = randomRow[0]
            if table.name is 'wisdom':
                self.lastwisdoms.append(result)
            self.cursor.execute(self.cmd_update_PID.format(table), (1, result[0],))
            self.connection.commit()
            return result[2]
        else:
            self.cursor.execute(self.cmd_reset_PIDs.format(table))
            self.connection.commit()
            return self.get_random_row(table)

    @botExceptionCatch
    def get_entry_by_ID(self, table, id):
        """Returns row from table by rowid"""
        self.cursor.execute(self.cmd_get_by_ID.format(table), (id,))
        return self.cursor.fetchall()

    @botExceptionCatch
    def get_entry_by_key(self, table, key):
        """Returns value from table by key"""
        return self.cursor.execute(self.cmd_get_by_key.format(table), (key,)).fetchall()[0][0]

    @botExceptionCatch
    def set_entry_by_key(self, table, value, key):
        """Sets value in table by key"""
        self.cursor.execute(self.cmd_set_by_key.format(table), (value, key,))
        self.connection.commit()

    @botExceptionCatch
    def add_new_entry(self, table, newEntry, author='Default'):
        """! Only works for wisdoms table !"""
        if table.name is not 'wisdom':
            return "You can't add new entries to this table"
        newEntry = newEntry.strip()
        if not newEntry:
            return "Can't add empty entry"
        self.cursor.execute(self.cmd_add_new_wisdom.format(
            table), (newEntry, author,))
        self.connection.commit()
        logger.info('{} added'.format(newEntry))
        return '{} added'.format(newEntry)

    @botExceptionCatch
    def remove_entry(self, table, id):
        """Removes row by rowid (Wisdoms table)"""
        if self.get_entry_by_ID(table, id) == []:
            return 'Nothing to remove'
        else:
            self.cursor.execute(self.cmd_remove_row.format(table), (id,))
            self.connection.commit()
            logger.info('Wisdom {} removed'.format(id))
            return 'Wisdom {} removed'.format(id)

    @botExceptionCatch
    def update_imgur(self, pictures):
        """Updates imgur table"""

        if pictures is None or not isinstance(pictures, dict):
            return 'List of pictures is empty!'

        command = 'INSERT INTO {0.name}({0.value}, {0.timestamp}) VALUES (?,?)'
        self.cursor.execute(self.cmd_delete_table.format(imgur_table))
        self.cursor.executemany(command.format(imgur_table), [[key, value] for key, value in pictures.items()])
        self.connection.commit()


    @botExceptionCatch
    def get_random_picture(self):
        """Gets random picture from imgur table and sets new index based on picture's age"""
        command = 'SELECT rowid, * FROM {0.name} WHERE pID <= 2 ORDER BY random() LIMIT 1'
        random_row = self.cursor.execute(command.format(imgur_table)).fetchall()
        if random_row:
            result = random_row[0]
            current_pid = result[1]
            new_pid = current_pid + compare_timestamps(result[3])
            self.cursor.execute(self.cmd_update_PID.format(imgur_table), (new_pid, result[0],))
            self.connection.commit()
            return result[2]
        else:
            self.cursor.execute(self.cmd_reset_PIDs.format(imgur_table))
            self.connection.commit()
            return self.get_random_picure(imgur_table)


    @botExceptionCatch
    def add_value_to_table(self, table, value):
        """Adds new value to table"""
        self.cursor.execute(self.cmd_add_new_row.format(table), (value,))
        self.connection.commit()
        return '`{0} added to {1}`'.format(value, table.name)

    @botExceptionCatch
    def get_cached_nicknames(self, table):
        """Returns tuple list in format ('ID', 'DisplayName', 'Date')"""
        self.cursor.execute(self.cmd_get_table.format(table))
        return self.cursor.fetchall()

    @botExceptionCatch
    def update_cached_nicknames(self, servers):
        """Updates nickname cache for every server in bot.servers"""
        users = {}
        for server in servers:
            for member in server.members:
                users[member.id] = member.display_name
        self.cursor.execute(self.cmd_delete_table.format(nicknames_table))
        self.cursor.executemany(self.cmd_add_new_wisdom.format(nicknames_table), [
                                [key, value] for key, value in users.items()])
        self.connection.commit()

    @botExceptionCatch
    def close(self):
        """Closes db connection"""
        self.connection.close()
        logger.info("Connection closed")

    # Extension shortcuts
    @botExceptionCatch
    def get_game(self):
        """Returns saved 'game' from settings table"""
        return self.get_entry_by_key(settings_table, 'game')

    @botExceptionCatch
    def set_game(self, name):
        """Saves 'game' to settings table"""
        key = 'game'
        self.set_entry_by_key(settings_table, name, key)
        return 'Status changed to {}'.format(name)

    @botExceptionCatch
    def get_link(self, key):
        """Returns link by key from 'links' table"""
        return self.get_entry_by_key(links_table, key)

    @botExceptionCatch
    def get_game_profiles(self, key):
        """Returns player dictionary in format discordID:platformID"""
        command = 'SELECT id, {0} FROM users WHERE {0} is not NULL'
        raw_data = self.cursor.execute(command.format(key)).fetchall()
        profiles = {x[0]: x[1] for x in raw_data}
        return profiles

    @botExceptionCatch
    def get_brawl_settings(self):
        """Returns list of settings for brawl command"""
        command = 'SELECT {0.key},{0.value} FROM {0.name} WHERE key in (?, ?, ?)'
        raw_data = self.cursor.execute(command.format(
            settings_table), ('spreadsheet', 'json', 'token',)).fetchall()
        settings = {x[0]: x[1] for x in raw_data}
        return settings

    def get_brawl_table(self):
        try:
            command = 'SELECT * FROM brawl'
            raw_data = self.cursor.execute(command).fetchall()
            column_lists = list(map(list, zip(*raw_data)))
            filtered_lists = list(list(filter(None, column)) for column in column_lists)
            return filtered_lists
        except Exception as e:
            logger.error('[{0}] {1}'.format(__name__, e))
            return None

    @botExceptionCatch
    def update_brawl_table(self, brawl_list):
        self.cursor.execute(self.cmd_delete_table.format(brawl_table))
        command = 'INSERT INTO brawl(names, actions, victims, tools, actions2, places) VALUES (?,?,?,?,?,?)'
        zipped_data = list(zip(*brawl_list))
        self.cursor.executemany(command, [(x) for x in zipped_data])
        self.connection.commit()
