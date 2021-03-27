'''Dummy file'''
from book import main as single_mode
from woo import main as woo
from woo import get_product as woo_get
from image_downloader import get_image as image

# Dictionary of gui features
gui = {
    'google'            :True,
    'isbndb'            :True,
    'amazon'            :True,
    'goodreads'         :True,
#    'name_box'          :True,
    'title_box'         :True,
    'authors_box'       :True,
    'description_box'   :True,
    'binding_box'       :True,
    'publisher_box'     :True,
    'publish_date_box'  :True,
    'categories_box'    :True,
    'image_box'         :True
}

def get_book(item):
    '''Dummy file'''
    product = single_mode(item, gui)
    try:
        product["image"] = image(product["image"], item)
    except Exception: # pylint: disable=broad-except
        product["image"] = None
    return product

def send_woocommerce(dictionary): # pylint: disable=redefined-outer-name
    '''Dummy file'''
    product = woo(dictionary)
    return product

def get_woocommerce(item):
    '''Dummy file'''
    product = woo_get(item, gui)
    return product


# entry = 9781473231122 # pylint: disable=invalid-name
# entry = 9781609808389
entry = 9780008296490

dictionary = get_book(entry)
# get_woo = get_woocommerce(entry)
print(dictionary)

# dictionary = get_woocommerce(entry)
dictionary["isbn"] = str(entry)
dictionary["amount"] = 10
dictionary["price"] = "5"
dictionary["sale_price"] = "3"
dictionary["tags"] = ["Sale", "New Release"]
dictionary["categories"] = ["Food & Drink", "Audio CD"]
dictionary["source"] = False
dictionary["name"] = "Dev"
# dictionary["image"] = image(dictionary["image"], entry)
# get_woo = send_woocommerce(dictionary)
# print(get_woo)
