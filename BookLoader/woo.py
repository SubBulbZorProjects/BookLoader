'''WooCommerce API integrator'''
import configparser  # Read config file.
import inspect  # Get function name.
import logging  # Logging errors.
import os  # Just os module?
from pathlib import Path  # Create a directory if needed.

from woocommerce import API as woo  # woocommerce API

from database import MySQL # MySQL Query.
from wp import main as wp  # WordPress API

current_dir = (os.path.dirname(os.path.realpath(__file__)))
Path(os.path.join(current_dir, "logs")).mkdir(parents=True, exist_ok=True)
logging_path = os.path.join(current_dir, "logs", "Woo.log")
logging.basicConfig(filename=logging_path, level=logging.WARNING,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)

class WooCommerce: # pylint: disable=too-few-public-methods
    '''Woo class'''
    def __init__(self, book):
        '''init Woo class'''
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'config', 'conf.ini'))
        self.woo_url = config.get("WooCommerce", "url")
        self.woo_key = config.get("WooCommerce", "key")
        self.woo_secret = config.get("WooCommerce", "secret")
        self.book = book
        self.error_codes = [401, 404, 500]
        self.error_catch = []

    def get_woo_request(self):
        '''Get WooCommerce api request'''
        try:
            response = woo(
                url=self.woo_url,
                consumer_key=self.woo_key,
                consumer_secret=self.woo_secret,
                wp_api=True,
                version="wc/v2",
                query_string_auth=True,
                verify_ssl = True,
                timeout=10
            )
        except Exception as error: # pylint: disable=broad-except
            logger.info(error)
        return response

    def get_woo_product(self, post_id):
        '''Get WooCommerce product'''
        try:
            auth = self.get_woo_request()
            # response = auth.get("products").json()
            response = auth.get("products/" + str(post_id)).json()

            # Send none if status code found in error codes
            if "data" in response:
                if response.get("data", {}).get("status") in self.error_codes:
                    self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                    return None

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return response

    def get_woo_products(self, page):
        '''Get WooCommerce products'''
        try:
            auth = self.get_woo_request()
            response = auth.get("products", params={"per_page":100, "page":page}).json()

            # Send none if status code found in error codes
            if "data" in response:
                if response.get("data", {}).get("status") in self.error_codes:
                    self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                    return None

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return response

    def get_woo_categories(self):
        '''Get WooCommerce category'''
        dictionary = {}
        try:
            auth = self.get_woo_request()
            response = auth.get("products/categories", params={"per_page":100}).json()

            # Send none if status code found in error codes
            if "data" in response:
                if response.get("data", {}).get("status") in self.error_codes:
                    self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                    return None

            for category in response:
                if "amp;" in category["name"]:
                    category["name"] = category["name"].replace("amp;","")
                dictionary[category["id"]] = category["name"]

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return dictionary

    def get_woo_tags(self):
        '''Get WooCommerce tags'''
        dictionary = {}
        try:
            auth = self.get_woo_request()
            response = auth.get("products/tags", params={"per_page":100}).json()

            # Send none if status code found in error codes
            if "data" in response:
                if response.get("data", {}).get("status") in self.error_codes:
                    self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                    return None

            for tag in response:
                if "amp;" in tag["name"]:
                    tag["name"] = tag["name"].replace("amp;","")
                dictionary[tag["id"]] = tag["name"]

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return dictionary

    def prepare_update_woo_products(self):
        '''Prepare WooCommerce product update'''
        try:
            # Auth
            auth = self.get_woo_request()
            response = auth.get("products/" + str(self.book["id"])).json()
            if response:
                # Upload image
                image = wp(self.book["image"])
                data = {
                    "name": self.book["name"],
                    "description": self.book["description"],
                    "sku": self.book["isbn"],
                    "categories": [],
                    "tags": [],
                    "attributes": [
                        {
                        "id": 1,
                        "name": "Tytuł",  # cspell: disable-line
                        "position": 1,
                        "visible": True,
                        "variation": True,
                        "options": [self.book["title"]]
                        },
                        {
                        "id": 2,
                        "name": "Autor",  # cspell: disable-line
                        "position": 2,
                        "visible": True,
                        "variation": True,
                        "options": [self.book["authors"]]
                        },
                        {
                        "id": 3,
                        "name": "Wydawnictwo",  # cspell: disable-line
                        "position": 3,
                        "visible": True,
                        "variation": True,
                        "options": [self.book["publisher"]]
                        },
                        {
                        "id": 4,
                        "name": "Rok wydania",  # cspell: disable-line
                        "position": 4,
                        "visible": True,
                        "variation": True,
                        "options": [self.book["publish_date"]]
                        },
                        {
                        "id": 5,
                        "name": "Okładka",  # cspell: disable-line
                        "position": 5,
                        "visible": True,
                        "variation": True,
                        "options": [self.book["binding"]]
                        },
                        {
                        "id": 6,
                        "name": "ISBN",
                        "position": 6,
                        "visible": True,
                        "variation": True,
                        "options": [self.book["isbn"]]
                        }
                    ]
                }

                # Tags
                try:
                    if self.book["tags"]:
                        tags = self.validate_tags()
                        for tag in tags:
                            data["tags"].append({'id':tag})
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                # Image
                try:
                    if image:
                        data["images"] = [{"src": image}]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                # Price
                try:
                    if self.book["price"]:
                        data["regular_price"] = self.book["price"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                # Sale Price
                try:
                    if self.book["sale_price"]:
                        data["sale_price"] = self.book["sale_price"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                # Amount
                try:
                    if self.book["amount"]:
                        data["manage_stock"] = True
                        data["stock_quantity"] = self.book["amount"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                # Get category ID
                try:
                    categories = self.validate_category()
                    for category in categories:
                        data["categories"].append({'id':category})
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                # Send request
                response = self.update_woo_products(self.book["id"], data)

                # Send none if status code found in error codes
                if "data" in response:
                    if response.get("data", {}).get("status") in self.error_codes:
                        self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                        return None

                # Format output
                try:
                    output = {
                        'id'            :response["id"],
                        'name'          :response["name"],
                        'link'          :response["permalink"],
                        'source'        :True
                    }

                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

            # Send none if status code found in error codes
            if "data" in response:
                if response.get("data", {}).get("status") in self.error_codes:
                    self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                    return None

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return output

    def update_woo_products(self, product_id, data):
        '''Post WooCommerce product'''
        try:
            # Auth
            auth = self.get_woo_request()
            response = auth.put("products/" + str(product_id), data).json()

            # Send none if status code found in error codes
            if "data" in response:
                if response.get("data", {}).get("status") in self.error_codes:
                    self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                    return None

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return response

    def post_woo_category(self, category):
        '''Create WooCommerce category'''
        try:
            auth = self.get_woo_request()
            data = {
                "name": category
            }

            response = auth.post("products/categories", data).json()

            # Send none if status code found in error codes
            if "data" in response:
                if response.get("data", {}).get("status") in self.error_codes:
                    self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                    return None

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return response

    def post_woo_products(self):
        '''Post WooCommerce product'''
        try:
            # Auth
            auth = self.get_woo_request()
            # Upload image to media
            image = wp(self.book["image"])

            data = {
                "name": self.book["name"],
                "description": self.book["description"],
                "sku": self.book["isbn"],
                "categories": [],
                "tags": [],
                "attributes": [
                    {
                    "id": 1,
                    "name": "Tytuł",  # cspell: disable-line
                    "position": 1,
                    "visible": True,
                    "variation": True,
                    "options": [self.book["title"]]
                    },
                    {
                    "id": 2,
                    "name": "Autor",  # cspell: disable-line
                    "position": 2,
                    "visible": True,
                    "variation": True,
                    "options": [self.book["authors"]]
                    },
                    {
                    "id": 3,
                    "name": "Wydawnictwo",  # cspell: disable-line
                    "position": 3,
                    "visible": True,
                    "variation": True,
                    "options": [self.book["publisher"]]
                    },
                    {
                    "id": 4,
                    "name": "Rok wydania",  # cspell: disable-line
                    "position": 4,
                    "visible": True,
                    "variation": True,
                    "options": [self.book["publish_date"]]
                    },
                    {
                    "id": 5,
                    "name": "Okładka",  # cspell: disable-line
                    "position": 5,
                    "visible": True,
                    "variation": True,
                    "options": [self.book["binding"]]
                    },
                    {
                    "id": 6,
                    "name": "ISBN",
                    "position": 6,
                    "visible": True,
                    "variation": True,
                    "options": [self.book["isbn"]]
                    }
                ]
            }

            # Tags
            try:
                if self.book["tags"]:
                    tags = self.validate_tags()
                    for tag in tags:
                        data["tags"].append({'id':tag})
            except Exception as error:  # pylint: disable=broad-except
                logger.info(error)

            # Image
            try:
                if image:
                    data["images"] = [{"src": image}]
            except Exception as error:  # pylint: disable=broad-except
                logger.info(error)

            # Price
            try:
                if self.book["price"]:
                    data["regular_price"] = self.book["price"]
            except Exception as error:  # pylint: disable=broad-except
                logger.info(error)

            # Sale Price
            try:
                if self.book["sale_price"]:
                    data["sale_price"] = self.book["sale_price"]
            except Exception as error:  # pylint: disable=broad-except
                logger.info(error)

            # Amount
            try:
                if self.book["amount"]:
                    data["manage_stock"] = True
                    data["stock_quantity"] = self.book["amount"]
            except Exception as error:  # pylint: disable=broad-except
                logger.info(error)

            # Get category ID
            try:
                categories = self.validate_category()
                for category in categories:
                    data["categories"].append({'id':category})
            except Exception as error:  # pylint: disable=broad-except
                logger.info(error)

            # Send request
            response = auth.post("products", data).json()

            # Send none if status code found in error codes
            if "data" in response:
                if response.get("data", {}).get("status") in self.error_codes:
                    self.error_catch.append(inspect.getouterframes(inspect.currentframe())[0].function) # pylint: disable=line-too-long
                    return None

            # Format output
            try:
                output = {
                    'id'            :response["id"],
                    'name'          :response["name"],
                    'link'          :response["permalink"],
                    'source'        :False
                }

            except Exception as error:  # pylint: disable=broad-except
                logger.info(error)

            if response["data"]["status"] == 400:

                try:
                    mysql_request = MySQL(isbn=self.book["isbn"])
                    request = mysql_request.db_mysql()

                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                if request:
                    product = self.get_woo_product(request)
                    if product["stock_quantity"]:
                        data["stock_quantity"] = int(data["stock_quantity"]) + product["stock_quantity"]  # pylint: disable=line-too-long

                    try:
                        response = self.update_woo_products(product["id"], data)
                        output = {
                            'id'            :response["id"],
                            'name'          :response["name"],
                            'link'          :response["permalink"],
                            'source'        :True
                        }

                        return output

                    except Exception as error:  # pylint: disable=broad-except
                        logger.info(error)
                else:
                    return None

        except Exception as error:  # pylint: disable=broad-except
            logger.info(error)
        return output

    def validate_category(self):
        '''Try to get WooCommerce category before upload product'''
        try:
            categories_woo = self.get_woo_categories()
            categories_book = list(self.book["categories"])
            result = {k for k, v in categories_woo.items() if v in categories_book}

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return result

    def validate_tags(self):
        '''Try to get WooCommerce category before upload product'''
        try:
            tags_woo = self.get_woo_tags()
            tags_book = list(self.book["tags"])
            result = {k for k, v in tags_woo.items() if v in tags_book}

        except Exception as error: # pylint: disable=broad-except
            logger.info(error)

        return result

    def search_for_product(self):
        '''Find product in Woo'''
        try:
            page_number = 0
            while True:
                page_number += 1
                try:
                    products = self.get_woo_products(page_number)
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                if products:
                    for product in products:
                        if product["sku"] == str(self.book):
                            return product
                else:
                    return None

        except Exception as error:  # pylint: disable=broad-except
            logger.info(error)

    @staticmethod
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

    @staticmethod
    def get_translation(word, mode):
        '''Translate attributes'''
        translation = {
                "title"         :"Tytuł",  # cspell: disable-line
                "authors"       :"Autor",  # cspell: disable-line
                "publisher"     :"Wydawnictwo",  # cspell: disable-line
                "publish_date"  :"Rok wydania",  # cspell: disable-line
                "binding"       :"Okładka",  # cspell: disable-line
            }
        if mode == "en":
            return list(translation.keys())[list(translation.values()).index(word)]
        if mode == "pl":
            return translation[word]

def get_product(book, gui):
    '''Get product form Woo'''

    dictionary = {}

    try:
        # Get product ID from DB.
        mysql_request = MySQL(isbn=book)
        mysql_response = mysql_request.db_mysql()

        if mysql_response:
            product = WooCommerce(book=book)
            request = product.get_woo_product(mysql_response)

            if request:
                try:
                    dictionary["id"] = request["id"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                try:
                    for attribute in request["attributes"]:
                        dictionary[product.get_translation(attribute["name"],
                                "en")] = product.list_expander(attribute["options"]).replace("amp;","") # pylint: disable=line-too-long
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                try:
                    dictionary["name"] = request["name"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                try:
                    dictionary["description"] = request["description"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                try:
                    categories_list = []
                    categories = request["categories"]
                    for category in categories:
                        categories_list.append(category["name"].replace("amp;",""))

                    dictionary["categories"] = categories_list
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                try:
                    tags_list = []
                    tags = request["tags"]
                    for tag in tags:
                        tags_list.append(tag["name"].replace("amp;",""))

                    dictionary["tags"] = tags_list
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                try:
                    dictionary["image"] = request["images"][0]["src"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                try:
                    dictionary["price"] = request["regular_price"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                try:
                    dictionary["sale_price"] = request["sale_price"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                try:
                    dictionary["amount"] = request["stock_quantity"]
                except Exception as error:  # pylint: disable=broad-except
                    logger.info(error)

                for key in gui:
                    if "_box" in key and gui[key]:
                        if key.split('_box')[0] not in dictionary:
                            dictionary[key.split('_box')[0]] = None

                        if dictionary[key.split('_box')[0]] == "":
                            dictionary[key.split('_box')[0]] = None

    except Exception as error:  # pylint: disable=broad-except
        logger.info(error)

    return dictionary

def main(book):
    '''Send product to'''
    shop = WooCommerce(book=book)
    # Make update
    if book["source"]:
        request = shop.prepare_update_woo_products()
        print(request)
        if shop.error_catch:
            request = shop.error_catch

    else:
        request = shop.post_woo_products()
        print(request)
        if shop.error_catch:
            request = shop.error_catch

    return request
