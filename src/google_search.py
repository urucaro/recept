#!/usr/bin/python
#-*- coding:  utf8 -*-

import json
import urllib
import urllib2
import argparse
from bs4 import BeautifulSoup
from collections import defaultdict
import pprint
import re



def showsome(searchfor):
    query = urllib.urlencode({'q': 'recept %s' %searchfor})
    url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s&rsz=8' % query
    search_response = urllib.urlopen(url)
    search_results = search_response.read()
    results = json.loads(search_results)
    data = results['responseData']
    hits = data['results']

    result_urls = []
    for h in hits:
        result_urls.append (h['url'])
        print ' ', h['url']
    print 'Top %d hits:' % len(hits)
    print 'Total results: %s' % data['cursor']['estimatedResultCount']
    print 'For more results, see %s' % data['cursor']['moreResultsUrl']
    return result_urls

def ingredients (result_urls):
    result = defaultdict(list)
    for url in result_urls:
        response = urllib2.urlopen(url)#Opens the url
        html = response.read ()#loads the html code
        soup = BeautifulSoup (html,  from_encoding='utf-8')#interprets (parse?) the html code
        ingredients = soup.find (True, class_= re.compile('ingredients'))
        if ingredients:
            ingredients = ingredients.find_all ('li')
            for ingredient in ingredients:
                result [url].append(ingredient.get_text().replace("\n", "").strip())
    return result

def parse_ingredients (ingredients_urls):
    result = defaultdict(list)
    for url, ingredients in ingredients_urls.iteritems():
        for ingredient in ingredients:
            if not ingredient:
                print url
                break
            amount_search = re.search(r"\d*\.\d+|\d*\s?-?\d*/?\d*",  ingredient)
            if amount_search.group():
                amount = amount_search.group()
                ingredient = ingredient.replace(amount, '')
                unit = ingredient.split()[0]
                ingredient = ingredient.replace(unit,  '')
                result[url].append([amount, unit, ingredient])
            else:
                result[url].append(["", "",  ingredient])
          
    return result
            







if __name__=='__main__':#gÃ¶r att det bara kÃ¶rs om det Ã¤r huvudprogramme

    parser = argparse.ArgumentParser('Get a comparison of recepies') 

    parser.add_argument('-s' ,'--search',  help = 'The recipe you want to search and compare')

    args = parser.parse_args()
    if args.search:
        result_urls = showsome(args.search)
        ingred = ingredients(result_urls)
        parsed_ingred = parse_ingredients(ingred)
        pprint.pprint (dict(parsed_ingred))
        
        

