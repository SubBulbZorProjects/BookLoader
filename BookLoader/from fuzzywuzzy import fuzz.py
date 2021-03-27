import configparser
import os
import ast

from fuzzywuzzy import fuzz

category_dict = {}

config = configparser.ConfigParser()
config.read(os.path.dirname(__file__) + '/conf.ini')
category_list = ast.literal_eval(config.get("Category", 'categories'))

config.read(os.path.dirname(__file__) + '/category.ini')

for cat in category_list:
    try:
        map_list = ast.literal_eval(config.get("Mapper", cat))
        if type(map_list) is str:
            raise TypeError('Wrong type')
        map_list = [x.lower() for x in map_list]
        map_list.append(cat.lower())
        category_dict[cat] = map_list
    except configparser.NoOptionError as e:
        category_dict[cat] = [cat.lower()]
    except TypeError as e:
        category_dict[cat] = [cat.lower()]

    
    


lista1 = ['travel','coocking','tools']
# category_dict = {'Food & drink' : ['Food & drink', 'coocking'],
#                 'History' : ['History', 'Historical']}

print(category_dict)

def fuzzer():

    return [key for key, value in category_dict.items() for x in value for y in lista1 if fuzz.ratio(x,y) > 99]
p = fuzzer()
print(p)
