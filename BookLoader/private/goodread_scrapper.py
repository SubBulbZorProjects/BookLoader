''' Goodread Scrapper '''
import requests
from bs4 import BeautifulSoup
from googlesearch import search


def goodread_search(item):
    ''' Goodread scrapper function '''

    goodread_dict = {}
    title = ''
    author = ''
    image = ''
    category_list = []
    description = ''
    binding = ''
    publisher = ''
    publish_date = ''

    # Goodread search link
    goodread_url = 'https://www.goodreads.com/search?q=' + item
    
    # Parse url to Bs4 object
    def parse_url(goodread_url):
        ''' Parse url to Soup '''
        headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36",
        "action": "sign-in"
        }
        page = requests.get(goodread_url, headers=headers)
        soup = BeautifulSoup(page.content, 'lxml', from_encoding=page.encoding)
        return soup
        
    # Find Title
    def find_title(soup):
        ''' Find title on page '''
        try:
            title = soup.find("h1", attrs={"id":'bookTitle'})
        except:
            title = None
        return title

    # Find title as method
    try:
        soup = parse_url(goodread_url)
        title = find_title(soup)
    except:
        title = None
    try:
        if title != None:
            title = title.get_text()
            title = title.split()
            title = ' '.join(title)
    except:
        title = None

    # Find author
    try:
        author = soup.find("span",attrs={'itemprop':"name"})
        author = author.get_text()
    except:
        pass

    # Find image source
    try:
        image = soup.find("img",attrs={'id':"coverImage"}).attrs['src']
    except:
        image = None

    # Find category list
    try:
        category = soup.find_all("a",attrs={"class":"actionLinkLite bookPageGenreLink"})
        for index, i in enumerate(category,start=1):
            if index > 3:
                break
            category_list.append(i.get_text())
    except:
        pass
    
    # Find description
    try:
        description = soup.find('div',attrs={"id":"description"})
        description = description.findAll('span')
    except:
        description = None

    if description != None:
        if len(description) > 1:
            description = description[1]
        else:
            description = description[0]
    try:
        description = str(description)
        s = description.find('>')
        description = description[s+1:-7]
    except:
        pass
    
    # Find binding
    try:
        binding = soup.find('span',attrs={"itemprop":"bookFormat"}).get_text()
    except:
        binding = None

    # Find details
    try:
        details = soup.find('div',attrs={"id":"details"})
        details = details.findAll("div",attrs={'class':'row'})[1].get_text()
    except:
        details = None

    # Split publisher
    try:
        publisher = details.split("by ")[1]
        publisher = publisher.split('\n')[0]
    except:
        publisher = None
    
    # Split publish year
    try:
        publish_date = details.split("by")[0]
        publish_date = publish_date.split()[-1]
    except:
        publish_date = None

    # Create dictionary
    goodread_dict = {
        "title" : title,
        'author' : author,
        'image' : [image],
        'categories' : category_list,
        'description' : description,
        'binding' : binding,
        'publisher' : publisher,
        'year' : publish_date

    }

    return goodread_dict
