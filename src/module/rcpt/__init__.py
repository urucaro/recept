#!/usr/bin/python
#-*- coding:  utf8 -*-

import os
import urllib
import urllib2
import json
from bs4 import BeautifulSoup
import re
import argparse
import collections
import csv



class Environment (object):
    def __init__ (self,  p):
        """Create an environment based on the prefix 'p'"""
        assert os.path.isdir (p)
        self.prefix = p
        self.data_path = os.path.join (self.prefix, 'data')
        self.xap_db_path = os.path.join (self.data_path,  'xap-db')


class Database (object):
    """Database holding information from 'Livsmedelsdatabasen' """
    def __init__(self, x):
        """initialize the database placed in 'x' """
        assert os.path.isdir (x)
        self.env = Environment (x)
        self.basepath = self.env.prefix
        self.data_path = self.env.data_path
        self.xap_db_path =self.env.xap_db_path
        self.data_fn = os.path.join (self.data_path,  'LivsmedelsDatabas.csv')
        self.simple_words_fn = os.path.join (self.data_path,  'enklaord.txt')
        self.units_fn = os.path.join (self.data_path,  'units.txt')
        self.load_csv_data ()
        self.load_simplewords_list ()

    def load_csv_data (self):
        """reads database and returns a csv reader"""
        assert os.path.isfile (self.data_fn)
        with open (self.data_fn,  'rb') as f:
            csv_reader =  csv.reader (f, dialect= 'excel' , delimiter= ';')
            self.csv_header = csv_reader.next ()
            self.csv_col_titles = csv_reader.next ()
            self.foods_list = []
            for row in csv_reader:
                self.foods_list.append (row[0].decode('windows-1252'))

    def load_simplewords_list (self):
        with open(self.simple_words_fn,  'r') as f:
            word_list = f.readlines()
            word_list = word_list [0].decode('utf-8').split(',')
        return word_list

    def load_unit_list (self):
        with open (self.units_fn,  'r') as f:
            units_list = f.readlines ()
            units_list = units_list [0].decode('utf-8').split(',')
        return units_list


class Google_search (object):
    """Holds the information retrieved from the google api search"""
    
    def __init__ (self,  query,  prefix):
        self.prefix = prefix
        self.database_obj = Database(self.prefix)
        self.query = urllib.urlencode({'q': 'recept %s' %query})
        self.api_url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s&rsz=8' % self.query
        self.get_response()
    
    def get_response (self):
        """dictionary with response from the google api, e.g 'responseData, responseStatus etc' """
        
        search_response = urllib.urlopen(self.api_url)
        search_results = search_response.read()
        self.response = json.loads(search_results)

    def hits_amount (self):
        """Number of pages that where found and the top hits"""
        
        data = self.response['responseData']
        top_hits = len (data['results'])
        total_hits = data['cursor']['estimatedResultCount']
        result = {'top': top_hits,  'total': total_hits}
        return result

    def hits_urls (self):
        """The urls that were found"""
        
        data = self.response['responseData']
        hits = data['results']
        result_urls = []
        for hit in hits:
            result_urls.append (hit['url'])
        return result_urls

    def url_ingredients (self):
        """a dict with url as keys and a list with all the ingredients found 
        under a tag with class 'ingredients', if such tag is not found the url is omitted"""
        
        result_dict = collections.defaultdict(list)
        urls = self.hits_urls ()
        for url in urls:
            try:
                response = urllib2.urlopen(url)#Opens the url
                html = response.read ()#loads the html code
                soup = BeautifulSoup (html,  from_encoding='utf-8')#interprets (parse?) the html code
                ingredients = soup.find (True, class_= re.compile('ingredients'))#regex used here so *ingredients* are found
            except urllib2.HTTPError:
                ingredients = None
            
            if ingredients:
                ingredients_list = []
                ingredients = ingredients.find_all ('li')
                for ingredient in ingredients:
                    ingredients_list.append (ingredient.get_text())
                result_dict [url] = ingredients_list               
                
        return result_dict

    def ingredients (self):
        """returns an instance of the class 'Ingredients' """
        
        return Ingredients (self, self.database_obj)


class Ingredients (object):
    def __init__(self, google_search_obj,  database_obj):
        """"""
        self.search_obj = google_search_obj
        self.database_obj = database_obj
        self.prefix = self.database_obj.basepath
        self.ingredients_raw = self.search_obj.url_ingredients ()
        self.simple_words = self.database_obj.load_simplewords_list()

    def parsed_ingredients (self):        
        """ A list with dictionaries with keys: 'ingredient', 'amount' and 'unit' """
        
        result_dict = collections.defaultdict (dict)
        
        for url,  ingredients in self.ingredients_raw.iteritems():

            result_list = []
            for ingredient in ingredients:
                ingredient_obj = Ingredient (self.database_obj, ingredient)
                amount = ingredient_obj.amount
                unit = ingredient_obj.unit
                clean_ingredient = ingredient_obj.cleaned_ingredient_string
                result_list.append ({'ingredient': clean_ingredient, 
                                                        'amount': amount, 
                                                        'unit': unit})
            result_dict [url] = result_list

        return result_dict


class Ingredient (object):
    def __init__ (self, database_obj,  ingredient_string):
        self.database_obj = database_obj
        self.simple_words_list = self.database_obj.load_simplewords_list()
        self.units_list = self.database_obj.load_unit_list ()
        self.ingredient_string = ' '.join(ingredient_string.split())
        self.amount ()
        self.unit ()
        self.clean_ingredient_string ()

    def amount (self):
        amount_pattern = re.compile(ur"\d*\.\d+|\d*\s?-?\d*\u2044?/?\xbd?\d*",  re.UNICODE)
        amount_search = amount_pattern.search(self.ingredient_string) #Finds digits, floats or fraction at beginning of string
        if amount_search:
            self.amount = amount_search.group().strip()
        else:
            self.amount = None

    def unit (self):
        pattern = re.compile(r'\b(?:%s)\b' % '|'.join(self.units_list),  re.IGNORECASE | re.UNICODE)
        unit_search = pattern.search (self.ingredient_string)
        if unit_search:
            self.unit = unit_search.group().strip()
        else:
            self.unit = None

    def clean_ingredient_string (self):
        simple_words_pattern = re.compile(r'\b(?:%s)\b' % '|'.join(self.simple_words_list),  re.IGNORECASE | re.UNICODE)
        simple_words_search = simple_words_pattern.findall (self.ingredient_string)
        
        parenthesis_search = re.search(r"\(.*\)",self.ingredient_string)#Finds and removes parenthesis
        if parenthesis_search:
            parenthesis_search = parenthesis_search.group()
        
        to_be_removed = []
        to_be_removed.extend( (self.unit,  self.amount,  parenthesis_search))
        [to_be_removed.append(word) for word in simple_words_search]
        
        excess_pattern = re.compile(r'\b(?:%s)\b' % '|'.join(filter(None, to_be_removed)),  re.IGNORECASE | re.UNICODE)
        
        cleaned = excess_pattern.sub (r'', self.ingredient_string )
        self.cleaned_ingredient_string = ' '.join(cleaned.split()).lower()






if __name__=='__main__':

    parser = argparse.ArgumentParser('Get a comparison of recipes') 

    parser.add_argument('-s' ,'--search',  help = 'The recipe you want to search and compare')
    parser.add_argument('-p' ,'--prefix',  help = 'The path to the environment where food and word database is')

    args = parser.parse_args()
    if args.search and args.prefix:
        from pprint import pprint
        search = Google_search (args.search, args.prefix)
        gredients = Ingredients (search,  search.database_obj)
        pprint (gredients.parsed_ingredients())
        
                
                # ingredient = Ingredient ()
#                
#                ingredient = ' '.join(ingredient.split())#removes whitespace characters except one space
#                amount_pattern = re.compile(ur"\d*\.\d+|\d+\s?-?\d*\u2044?/?\d*",  re.UNICODE)
#                amount_search = amount_pattern.search(ingredient) #Finds digits, floats or fraction at beginning of string
#                if amount_search:
#                    amount = amount_search.group().strip()
#                    ingredient = ingredient.replace(amount, '')
#
#                    unit = ingredient.split()[0] # Pics out the string indicating unit
#                    ingredient = ingredient.replace(unit, "")
#                    
#                    finding = re.search(r"\(.*\)", ingredient)#Finds and removes parenthesis                
#                    if finding:
#                        ingredient = ingredient.replace (finding.group(),  '')
#                        
#                    found_simple_words = pattern.findall(ingredient)#Finds and removes simple words e.g. 'och', 'eller' , 
#                    if found_simple_words:
#                        for word in found_simple_words:
#                            print word
#                            ingredient = ingredient.replace(word, '')# here regex split() could be used instead
#                    
#                    ingredient = ' '.join(ingredient.split())#removes whitespace characters except one space
#                    
#                    if not ingredient:
#                        ingredient = unit
#                        unit = 'st'
#
#                    result_list.append ({'ingredient': ingredient.lower().strip(','), 
#                                                        'amount': amount, 
#                                                        'unit': unit})
#            result_dict [url] = result_list
  





