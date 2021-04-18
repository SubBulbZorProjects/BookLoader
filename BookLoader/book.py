'''book'''
import ast  # Use to read list from config file.
import configparser  # Read config file.
import logging  # Logging errors.
import os  # Just os module?
import re  # Regex.
from pathlib import Path  # Create a directory if needed.
from threading import Thread  # Multi thread.

import requests as req  # Requests HTTP Library.
import requests_cache  # Cache API requests.
from fuzzywuzzy import fuzz  # String similarity.

from private.amazon_scrapper import main as amazon_scrapper  # Amazon scrapper.
from private.goodread_scrapper import \
    goodread_search as goodreads_scrapper  # goodreads scrapper.

current_dir = (os.path.dirname(os.path.realpath(__file__)))
logging_path = os.path.join(current_dir, "logs", "book.log")

logging.basicConfig(filename=logging_path, level=logging.WARNING,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

class Books: # pylint: disable=too-few-public-methods, too-many-instance-attributes
    '''Book class'''
    def __init__(self, isbn, gui):
        '''init Book class'''
        self.isbn = isbn
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config', 'conf.ini'))
        self.google_token = config.get("Google", "token")
        self.isbndb_token = config.get("ISBNdb", "token")
        self.google_url = config.get("Google", "url")
        self.isbndb_url = config.get("ISBNdb", "url")
        self.google_header = ('&key='+self.google_token)
        self.isbndb_header = {'Authorization': self.isbndb_token}
        ### GUI dictionary :
        self.gui = gui
        ### Class parameters :
        self.title_list = []
        self.authors_list = []
        self.publisher_list = []
        self.publish_date_list = []
        self.categories_list = []
        self.binding_list = []
        self.description_list = []
        self.image_list = []

    def __get_isbndb_request(self, isbn):
        '''Get ISBNdb api request'''

        Path(os.path.join(current_dir, "cache")).mkdir(parents=True, exist_ok=True)
        cache = os.path.join(current_dir, "cache", "scraper_cache")
        requests_cache.install_cache(cache, backend='sqlite', expire_after=300)

        try:
            response = req.get((self.isbndb_url+isbn), headers=self.isbndb_header)

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return response

    def __get_google_request(self, isbn):
        '''Get Google api request'''

        Path(os.path.join(current_dir, "cache")).mkdir(parents=True, exist_ok=True)
        cache = os.path.join(current_dir, "cache", "scraper_cache")
        requests_cache.install_cache(cache, backend='sqlite', expire_after=300)

        try:
            response = req.get(self.google_url+isbn+self.google_header)

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return response

    def __get_isbndb_book(self): # pylint: disable=too-many-branches
        '''Get Book from ISBNdb'''
        try:
            # Request book
            isbndb_book_get = self.__get_isbndb_request(str(self.isbn))

            # Title :
            if self.gui["title_box"]:
                try:
                    self.title_list.append({"isbn" : isbndb_book_get.json()["book"]["title"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Author :
            if self.gui["authors_box"]:
                try:
                    self.authors_list.append({"isbn" : list_expander(isbndb_book_get.json()["book"]["authors"])}) # pylint: disable=line-too-long
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Binding :
            if self.gui["binding_box"]:
                try:
                    self.binding_list.append({"isbn" : isbndb_book_get.json()["book"]["binding"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Publisher :
            if self.gui["publisher_box"]:
                try:
                    self.publisher_list.append({"isbn" : isbndb_book_get.json()["book"]["publisher"]}) # pylint: disable=line-too-long
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Publish Date :
            if self.gui["publish_date_box"]:
                try:
                    self.publish_date_list.append({"isbn" : isbndb_book_get.json()["book"]["date_published"][:4]}) # pylint: disable=line-too-long
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Categories :
            if self.gui["categories_box"]:
                try:
                    self.categories_list += isbndb_book_get.json()["book"]["subjects"]
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

        except Exception as error: # pylint: disable=broad-except
            logger.warning(error)

    def __get_amazon_book(self): # pylint: disable=too-many-branches
        '''Get Book from Amazon'''
        try:
            # Request book
            amazon_book_get = amazon_scrapper(str(self.isbn))

            # Title :
            if self.gui["title_box"]:
                try:
                    self.title_list.append({"amazon" : amazon_book_get["title"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Author :
            if self.gui["authors_box"]:
                try:
                    self.authors_list.append({"amazon" : amazon_book_get["author"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Description :
            if self.gui["description_box"]:
                try:
                    self.description_list.append({"amazon" : amazon_book_get["description"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Binding :
            if self.gui["binding_box"]:
                try:
                    self.binding_list.append({"amazon" : amazon_book_get["binding"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Publisher :
            if self.gui["publisher_box"]:
                try:
                    self.publisher_list.append({"amazon" : amazon_book_get["publisher"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Publish Date :
            if self.gui["publish_date_box"]:
                try:
                    self.publish_date_list.append({"amazon" : amazon_book_get["year"][:4]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Image :
            if self.gui["image_box"]:
                try:
                    self.image_list.append({"amazon" : amazon_book_get["image"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Categories :
            if self.gui["categories_box"]:
                try:
                    self.categories_list += amazon_book_get["categories"]
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

        except Exception as error: # pylint: disable=broad-except
            logger.warning(error)

    def __get_goodreads_book(self): # pylint: disable=too-many-branches
        '''Get Book from goodreads'''
        try:
            # Request book
            goodreads_book_get = goodreads_scrapper(str(self.isbn))

            # Title :
            if self.gui["title_box"]:
                try:
                    self.title_list.append({"goodreads" : goodreads_book_get["title"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Author :
            if self.gui["authors_box"]:
                try:
                    self.authors_list.append({"goodreads" : goodreads_book_get["author"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Description :
            if self.gui["description_box"]:
                try:
                    self.description_list.append({"goodreads" : goodreads_book_get["description"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Binding :
            if self.gui["binding_box"]:
                try:
                    self.binding_list.append({"goodreads" : goodreads_book_get["binding"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Publisher :
            if self.gui["publisher_box"]:
                try:
                    self.publisher_list.append({"goodreads" : goodreads_book_get["publisher"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Publish Date :
            if self.gui["publish_date_box"]:
                try:
                    self.publish_date_list.append({"goodreads" : goodreads_book_get["year"][:4]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Image :
            if self.gui["image_box"]:
                try:
                    self.image_list.append({"goodreads" : goodreads_book_get["image"]})
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Categories :
            if self.gui["categories_box"]:
                try:
                    self.categories_list += goodreads_book_get["categories"]
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

        except Exception as error: # pylint: disable=broad-except
            logger.warning(error)

    def __get_google_book(self): # pylint: disable=too-many-branches
        '''Get Book from Google'''
        try:
            # Request book
            google_book_get = self.__get_google_request(str(self.isbn))

            # Title :
            if self.gui["title_box"]:
                try:
                    self.title_list.append({"google" : google_book_get.json()["items"][0]["volumeInfo"]["title"]}) # pylint: disable=line-too-long
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Author :
            if self.gui["authors_box"]:
                try:
                    self.authors_list.append({"google" : list_expander(google_book_get.json()["items"][0]["volumeInfo"]["authors"])}) # pylint: disable=line-too-long
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Description :
            if self.gui["description_box"]:
                try:
                    self.description_list.append({"google" : google_book_get.json()["items"][0]["volumeInfo"]["description"]}) # pylint: disable=line-too-long
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Publisher :
            if self.gui["publisher_box"]:
                try:
                    self.publisher_list.append({"google" : google_book_get.json()["items"][0]["volumeInfo"]["publisher"]}) # pylint: disable=line-too-long
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Publish Date :
            if self.gui["publish_date_box"]:
                try:
                    self.publish_date_list.append({"google" : google_book_get.json()["items"][0]["volumeInfo"]["publishedDate"][:4]}) # pylint: disable=line-too-long
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

            # Categories :
            if self.gui["categories_box"]:
                try:
                    self.categories_list += google_book_get.json()["items"][0]["volumeInfo"]["categories"] # pylint: disable=line-too-long
                except Exception as error: # pylint: disable=broad-except
                    logger.info(error)

        except Exception as error: # pylint: disable=broad-except
            logger.warning(error)

    def get_book(self): # pylint: disable=too-many-locals
        # Use threat :
        '''Get books properties'''
        try:
            if self.gui["amazon"]:
                data_thread_1 = Thread(target=self.__get_amazon_book)
                data_thread_1.start()

            if self.gui["goodreads"]:
                data_thread_2 = Thread(target=self.__get_goodreads_book)
                data_thread_2.start()

            if self.gui["isbndb"]:
                data_thread_3 = Thread(target=self.__get_isbndb_book)
                data_thread_3.start()

            if self.gui["google"]:
                data_thread_4 = Thread(target=self.__get_google_book)
                data_thread_4.start()

            if self.gui["amazon"]:
                data_thread_1.join()

            if self.gui["goodreads"]:
                data_thread_2.join()

            if self.gui["isbndb"]:
                data_thread_3.join()

            if self.gui["google"]:
                data_thread_4.join()

            title = validator(self.title_list) # pylint: disable=unused-variable
            authors = validator(self.authors_list) # pylint: disable=unused-variable
            binding = validator(self.binding_list) # pylint: disable=unused-variable
            publisher = validator(self.publisher_list) # pylint: disable=unused-variable
            description = validator(self.description_list) # pylint: disable=unused-variable
            publish_date = validator(self.publish_date_list) # pylint: disable=unused-variable

            # Variables without validation :
            isbn = self.isbn # pylint: disable=unused-variable

            # Allow to choose from list in GUI :
            image = self.image_list # pylint: disable=unused-variable
            description = self.description_list # pylint: disable=unused-variable

            # Categories :
            fuzzy = Fuzzer(similarity_list=self.categories_list)
            categories = list(set(fuzzy.fuzz())) # pylint: disable=unused-variable

            dictionary = {}
            for key in self.gui:
                if "_box" in key and self.gui[key]:
                    dictionary[key.split('_box')[0]] = eval(key.split('_box')[0]) # pylint: disable=eval-used

        except Exception as error: # pylint: disable=broad-except
            logger.warning(error)

        return dictionary

class Fuzzer:
    '''Fuzzer class'''
    def __init__(self, similarity_list):
        self.similarity_list = similarity_list
        self.category_dict = {}

        # Load ini variables.
        try:
            self.config = configparser.ConfigParser()
            self.config.read(os.path.join(os.path.dirname(__file__), 'config', 'conf.ini'))
            self.main_list = ast.literal_eval(self.config.get("Category", "categories"))
            self.discard_list = ast.literal_eval(self.config.get("Validator", "discard"))
            self.threshold = self.config.get("Category", "threshold")

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

    def __mapper(self):
        '''Map category'''
        self.config.read(os.path.join(os.path.dirname(__file__), 'config', 'category.ini'))

        for category in self.main_list:
            try:
                mapper_list = ast.literal_eval(self.config.get("Mapper", category))
                if isinstance(mapper_list, str):
                    raise TypeError('Type error, rise exception')

                # Find mapping.
                mapper_list = [mapping.lower() for mapping in mapper_list]
                mapper_list.append(category.lower())
                self.category_dict[category] = mapper_list

            # Add category as value and key if no mapping found.
            except configparser.NoOptionError as error: # pylint: disable=unused-variable
                self.category_dict[category] = [category.lower()]
            # Add category as value and key if error raised.
            except TypeError as error: # pylint: disable=unused-variable
                self.category_dict[category] = [category.lower()]

        return self.category_dict

    def fuzz(self):
        '''Find on lists similar objects'''

        def add_word(loop_word):
            '''Concatenate category'''
            return word.lower() + ' ' + loop_word.lower() # pylint: disable=undefined-loop-variable

        def add_sign(loop_word):
            '''Concatenate category'''
            return word.lower() + ' & ' + loop_word.lower() # pylint: disable=undefined-loop-variable

        try:
            # Invoke mapper function.
            main_dict = self.__mapper()
            separate_1 = []
            separate_2 = []
            separate_3 = []

            # Remove double-dash.
            for category in self.similarity_list:
                separate_1 += category.split('--')

            # Make it lower.
            separate_1 = [separate_1_category.lower() for separate_1_category in separate_1]

            # Remove single whitespace.
            for separated_category in separate_1:
                separate_2 += (separated_category.replace(",", "")).split(' ')

            # Make it lower.
            separate_2 = [separate_2_category.lower() for separate_2_category in separate_2]

            # Remove empty entry from list.
            for discard in self.discard_list:
                while discard in separate_2: separate_2.remove(discard) # pylint: disable=multiple-statements

            # Make some alternatives.
            for word in separate_2:
                separate_3 += map(add_word, separate_2)
                separate_3 += map(add_sign, separate_2)

            # Concatenate splitted lists with category.
            to_fuzz = [*self.similarity_list, *separate_2, *separate_3]

            return [key for key, value in main_dict.items()
                    for x in value for y in to_fuzz if fuzz.ratio(x,y) > int(self.threshold)]

        except Exception as error: # pylint: disable=broad-except
            print(error)
            logger.info(error)

def validator(validation_list): # pylint: disable=too-many-branches, too-many-return-statements
    '''Clear lists of unwanted objects and choose the right one'''
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config', 'conf.ini'))
    discard_list = ast.literal_eval(config.get("Validator", "discard"))
    priority = config.get("Validator", "priority")
    source_list = [list(source.values())[0] for source in validation_list]

    try:
        # Remove empty entry from main dictionary
        loop = validation_list.copy()
        for source in loop:
            for discard in discard_list:
                if list(source.values())[0] is discard:
                    validation_list.remove(source)

    except Exception as error: # pylint: disable=broad-except
        logger.info(error)

    try:
         # Remove empty entry from list
        for discard in discard_list:
            while discard in source_list: source_list.remove(discard) # pylint: disable=multiple-statements
        if len(source_list) > 1:
            # Testing equality of values
            if all(source == source_list[0] for source in source_list):
                # Choose amazon if available
                main_source = [source[priority] for source in validation_list if priority in source]
                if main_source:
                    return main_source[0]

                # Take the first element if amazon not available
                return source_list[0]

            # Find html tags in string
            html = [source for source in validation_list if find_html(list(source.values())[0])]

            if html:
                if type(html) is list and len(html) > 1: # pylint: disable=unidiomatic-typecheck
                    # Get greater string from html
                    main_source = [list(source.values())[0] for source in html]
                    return get_greater_string(main_source)

                # Get nested value
                return list(html[0].values())[0]

            # If string is clear, take amazon if available
            main_source = [source[priority] for source in validation_list if priority in source] # pylint: disable=line-too-long
            if main_source:
                return main_source[0]

            # At the very end take the first element
            return source_list[0]

        elif len(source_list) == 1:
            return source_list[0]
        else:
            return None

    except Exception as error: # pylint: disable=broad-except
        logger.info(error)

def list_expander(expander_list):
    '''Expand list elements to string'''
    try:
        if len(expander_list) > 1:
            return ', '.join(expander_list)
        if len(expander_list) == 1:
            return expander_list[0]
        return None

    except Exception as error: # pylint: disable=broad-except
        logger.info(error)

def get_greater_string(validation_list):
    '''Get greater string'''
    validation_dictionary = {}
    for index, string in enumerate(validation_list):
        string_len = len(string.split())
        validation_dictionary[index] = string_len

    greater_string = max(validation_dictionary, key=validation_dictionary.get)
    return validation_list[greater_string]

def find_html(string):
    '''Find HTML tags'''
    pattern = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    result = re.search(pattern, string)
    return result

def main(isbn, gui):
    '''Main function'''
    # Send dictionary with boxes from gui to class ->

    book = Books(isbn=isbn, gui = gui)
    request = book.get_book()

    return request
