'''amazon'''
import re
from threading import Thread
import requests
from bs4 import BeautifulSoup
from googlesearch import search


class AmazonScrapper:
    ''' Improved amazon scrapper'''
    def __init__(self,item):
        self.item = item
        self.title_list = []
        self.authors_list = []
        self.publisher_list = []
        self.category_list = []
        self.pub_data_list = []
        self.bind_list = []
        self.year_list = []
        self.description_list = []
        self.image_list = []
        self.url_list = []
        self.amazon_dict = {}
        self.get_url_list()
        self.unpack_url_list()

    def get_url_list(self):
        ''' Find urls from google '''
        link = self.item + ' site:www.amazon.com OR site:www.amazon.co.uk'
        for url in search(link,tld='com',start=0,stop=4, pause=0.1):
            self.url_list.append(url)
        print(self.url_list)

    def get_product(self,amazon_url):
        ''' Parse and scrapp page '''
        headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64)",
        "action": "sign-in"
        }
        requests_session = requests.Session()
        page = requests_session.get(amazon_url, headers=headers)
        soup = BeautifulSoup(page.content, 'lxml',from_encoding=page.encoding)

        # Book details
        try:
            details = soup.find("div",attrs={"id":"detailBullets_feature_div"})
            details = details.findAll("span",attrs={"class":"a-list-item"})
        except Exception: # pylint: disable=broad-except
            pass

        # Unpacking details
        try:
            for i in details:
                if "Publisher" in i.get_text():
                    pub_info = i.get_text()
                if "Hardcover" in i.get_text() or "Paperback" in i.get_text():
                    bind = i.get_text()
                if "ISBN-13" in i.get_text():
                    isbn = i.get_text()
        except Exception: # pylint: disable=broad-except
            pass

        # Find isbn
        try:
            isbn = isbn.replace('\n','').replace("-",'')
            isbn = isbn.split(':')[1]
        except Exception: # pylint: disable=broad-except
            pass

        try:
            if isbn != self.item:
                return self.amazon_dict
        except Exception: # pylint: disable=broad-except
            isbn = None

        # Find Title
        try:
            title = soup.find("span", attrs={"id":'productTitle'}).get_text()
        except Exception: # pylint: disable=broad-except
            title = None

        if title:
            title = title.replace('\n','')
            self.title_list.append(title)

        # Find image
        try:
            image = soup.find("img",attrs={'id':"imgBlkFront"}).attrs['data-a-dynamic-image']
        except Exception: # pylint: disable=broad-except
            image = None
        try:
            image = image.split('"')
        except Exception: # pylint: disable=broad-except
            pass
        if image:
            if len(image) > 2:
                first = re.findall(r'\d+',image[2])
                second = re.findall(r'\d+',image[4])
                if first[0] > second[0] and first[1] > second[1]:
                    self.image_list.append(image[1])
                else:
                    self.image_list.append(image[3])
            else:
                self.image_list.append(image[1])

        # Find author
        try:
            author = soup.find("span",attrs={'class':"author notFaded"}).get_text()
        except Exception: # pylint: disable=broad-except
            try:
                author = soup.find("a",attrs={"class":"a-size-small a-link-normal authorNameLink a-text-normal"}).get_text() # pylint: disable=line-too-long
                author = author.replace("\n","")
            except Exception: # pylint: disable=broad-except
                author = None
        if author is not None:
            try:
                author = author.split('(')[0]
            except Exception: # pylint: disable=broad-except
                pass
            try:
                author = author.replace('\n','')
            except Exception: # pylint: disable=broad-except
                pass
            try:
                self.authors_list.append(author)
            except Exception: # pylint: disable=broad-except
                pass

        # Find category
        try:
            category = soup.find("ul",attrs={"class":"a-unordered-list a-nostyle a-vertical zg_hrsr"}) # pylint: disable=line-too-long
            category = category.findAll("span",attrs={"class":"a-list-item"})

            for i in category:
                cat = i.get_text()
                cat = cat.split('in', 1)[1].split("(")[0]
                self.category_list.append(cat)
        except Exception: # pylint: disable=broad-except
            pass

        # Find Description
        try:
            description = soup.find("div",attrs={"id":"bookDescription_feature_div"})
            description = description.findAll('div')
        except Exception: # pylint: disable=broad-except
            pass
        if description:
            if len(description) > 0:
                try:
                    description = str(description[0])
                    self.description_list.append(description)
                except Exception: # pylint: disable=broad-except
                    pass
        else:
            return None

        try:
            publisher = pub_info.split(":")[1]
            publisher = publisher.split(";")[0].replace("\n","").split("(")[0]
            self.publisher_list.append(publisher)
        except Exception: # pylint: disable=broad-except
            publisher = None

        try:
            year = pub_info.replace(")","").replace('\n','')
            year = year[-4:]
            self.year_list.append(year)
        except Exception: # pylint: disable=broad-except
            year = None

        try:
            binding = bind.split(":")[0].replace("\n","")
            self.bind_list.append(binding)
        except Exception: # pylint: disable=broad-except
            binding = None

    def unpack_url_list(self):
        ''' Thread for url list '''
        thread_list = []
        for url in self.url_list:
            worker = Thread(target=self.get_product,args=(url,))
            thread_list.append(worker)
        for thread in thread_list:
            thread.start()
        for thread in thread_list:
            thread.join()


    def get_dictionary(self):
        ''' Create dictionary from output list '''
        if self.title_list:
            self.amazon_dict['title'] = min(self.title_list, key=len)
        if self.authors_list:
            self.amazon_dict['author'] = self.authors_list[0]
        if self.image_list:
            self.amazon_dict['image'] = self.image_list
        if self.publisher_list:
            self.amazon_dict['publisher'] = self.publisher_list[0]
        if self.year_list:
            self.amazon_dict['year'] = self.year_list[0]
        if self.category_list:
            self.amazon_dict['categories'] = self.category_list
        if self.bind_list:
            self.amazon_dict['binding'] = self.bind_list[0]
        if self.description_list:
            self.amazon_dict['description'] = max(self.description_list, key=len)

        return self.amazon_dict


def main(isbn):
    ''' Main function Amazon Scrapper '''
    amazon = AmazonScrapper(isbn)
    amazon_dictionary = amazon.get_dictionary()

    return amazon_dictionary
