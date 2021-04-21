'''MySQL connector'''
import configparser  # Read config file.
import logging  # Logging errors.
import os  # Just os module?
from pathlib import Path  # Create a directory if needed.

import mysql.connector
from mysql.connector import errorcode

current_dir = (os.path.dirname(os.path.realpath(__file__)))

# Start logging.
Path(os.path.join(current_dir, "logs")).mkdir(parents=True, exist_ok=True)
logging_path = os.path.join(current_dir, "logs", "sql.log")
logging.basicConfig(filename=logging_path, level=logging.WARNING,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

class MySQL: # pylint: disable=too-few-public-methods
    '''Woo class'''

    def __init__(self, isbn):
        '''init MySQL class'''
        # Import configuration.
        config = configparser.ConfigParser()
        config.read(os.path.join(current_dir, 'config', 'conf.ini'))
        self.host = config.get("MySQL", "host")
        self.user = config.get("MySQL", "user")
        self.password = config.get("MySQL", "password")
        self.database = config.get("MySQL", "database")
        self.isbn = isbn

    def db_mysql(self):
        '''MySQL function'''

        query  = ("SELECT * FROM `wp_postmeta` WHERE meta_key = '_sku' AND meta_value = {}").format(self.isbn) # pylint: disable=line-too-long

        try:
            cnx = mysql.connector.connect(
                host = self.host,
                user = self.user,
                password = self.password,
                database = self.database)

            cursor = cnx.cursor()

        except mysql.connector.Error as error:
            if error.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
                logger.info(error)

            elif error.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
                logger.info(error)

            else:
                logger.info(error)
                print(error)

        try:
            cursor.execute(query)
            result = cursor.fetchall()
            if not result:
                return None

            return result[0][1]

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        finally:
            cursor.close()
            cnx.close()
