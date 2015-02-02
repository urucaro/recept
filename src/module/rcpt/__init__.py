#!/usr/bin/python
#-*- coding:  utf8 -*-

import urllib
import urllib2
import json
from bs4 import BeautifulSoup
import re
import argparse
import collections
import rcpt.livsmedel



class Google_search (object):
    """Holds the information retrieved from the google api search"""
    
    def __init__ (self,  query,  prefix):
        self.prefix = prefix
        self.database_obj = rcpt.livsmedel.Database(self.prefix)
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
    
    def get_simple_words ():
        pass

    def clean_ingredients (self):
        """Removes unessential characters, words, parenthesis and numbers from the ingredients"""

#    def find_ingredients (self):
#        """a raw list with all the ingredients found under a tag with class 'ingredients', can be None if class not found """
#        try:
#            response = urllib2.urlopen(self.url)#Opens the url
#            html = response.read ()#loads the html code
#            soup = BeautifulSoup (html,  from_encoding='utf-8')#interprets (parse?) the html code
#            ingredients = soup.find (True, class_= re.compile('ingredients'))#regex used here so *ingredients* are found
#        except urllib2.HTTPError:
#            ingredients = None
#            
#        if ingredients:
#            ingredients_list = []
#            ingredients = ingredients.find_all ('li')
#            for ingredient in ingredients:
#                ingredients_list.append (ingredient.get_text().replace("\n", "").strip())
#            return ingredients_list
#        else: 
#            return None

    def parsed_ingredients (self):        
        """ A list with dictionaries with keys: 'ingredient', 'amount' and 'unit' """
    
        pattern = re.compile(r'\b(?:%s)\b' % '|'.join(self.simple_words),  re.IGNORECASE | re.UNICODE)
        
        result_dict = collections.defaultdict (list)
        
        for url,  ingredients in self.ingredients_raw.iteritems():
            result_list = []
            for ingredient in ingredients:
                
                ingredient = ' '.join(ingredient.split())#removes whitespace characters except one space
                amount_pattern = re.compile(ur"\d*\.\d+|\d+\s?-?\d*\u2044?/?\d*",  re.UNICODE)
                amount_search = amount_pattern.search(ingredient) #Finds digits, floats or fraction at beginning of string
                if amount_search:
                    amount = amount_search.group().strip()
                    ingredient = ingredient.replace(amount, '')

                    unit = ingredient.split()[0] # Pics out the string indicating unit
                    ingredient = ingredient.replace(unit, "")
                    
                    finding = re.search(r"\(.*\)", ingredient)#Finds and removes parenthesis                
                    if finding:
                        ingredient = ingredient.replace (finding.group(),  '')
                        
                    found_simple_words = pattern.findall(ingredient)#Finds and removes simple words e.g. 'och', 'eller' , 
                    if found_simple_words:
                        for word in found_simple_words:
                            print word
                            ingredient = ingredient.replace(word, '')
                    
                    ingredient = ' '.join(ingredient.split())#removes whitespace characters except one space
                    
                    if not ingredient:
                        ingredient = unit
                        unit = 'st'

                    result_list.append ({'ingredient': ingredient.lower().strip(','), 
                                                        'amount': amount, 
                                                        'unit': unit})
            result_dict [url] = result_list
        return result_dict

class Ingredient (object):
    pass


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
  
            
            


