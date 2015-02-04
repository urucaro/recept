#!/usr/bin/python
#-*- coding:  utf8 -*-

import rcpt
import rcpt.livsmedel
from pprint import pprint
import argparse
import difflib
import collections
import xapian


def sort_ingredients (database_obj,  all_url_ingredients): 
    result_dict = collections.defaultdict(list)
    to_be_found_list = []
    
    for url,  ingredients in all_url_ingredients.iteritems():       

        for ingredient in ingredients:
            print ingredient
            inner_dict = {url :{'amount': ingredient ['amount'], 
                            'unit': ingredient ['unit']}}
            ingredient_name = ingredient['ingredient'].split()
            if len(ingredient_name) <= 1:
                result_dict [ingredient_name[0]].append(inner_dict)
            else:
                hit_list = []
                for word in ingredient_name:
                    match = search (database_obj.xap_db_path, word)
                    if match:
                        hit_list.append(word)
                if len(hit_list) == 1:
                    result_dict [hit_list[0]].append(inner_dict)
                elif len(hit_list) == 0:
#                    inner_dict [url]['ingredient name'] = ingredient_name
#                    to_be_found_list.append(inner_dict)
                    print ingredient_name
                else:
                    inner_dict [url]['hit_list'] = hit_list
                    to_be_found_list.append(inner_dict)

    for item in to_be_found_list:
        for url,  ingredient in item.iteritems():
            word_set = set (ingredient ['hit_list'])
            dict_set = result_dict.keys()
            common_word = ' '.join(set.intersection(word_set,  dict_set))
            if common_word:
                del item [url]['hit_list']
                result_dict [common_word].append (item)
            else:
                print 'här är ett icke ord!!!!!!!!!!!!!'
                print item [url]['hit_list']

            
    return result_dict
    
    

def check_similarity (a, b):
    cut_off = 0.9
    compare = difflib.SequenceMatcher(None, a, b).ratio()
    return 1 > compare > cut_off

def search (xap_db_path, querystring, offset=0, pagesize=10):
    # offset - defines starting point within result set
    # pagesize - defines number of records to retrieve

    # Open the database we're going to search.
    db = xapian.Database (xap_db_path)
    # Set up a QueryParser with a stemmer and suitable prefixes
    queryparser = xapian.QueryParser()
    queryparser.set_stemmer(xapian.Stem("swedish"))
    queryparser.set_stemming_strategy(queryparser.STEM_SOME)
    queryparser.add_prefix("food", "XFOOD")
    
    xapian_flags = xapian.QueryParser.FLAG_WILDCARD | xapian.QueryParser.FLAG_BOOLEAN | \
                        xapian.QueryParser.FLAG_SYNONYM | xapian.QueryParser.FLAG_BOOLEAN_ANY_CASE | \
                        xapian.QueryParser.FLAG_LOVEHATE | xapian.Query.OP_PHRASE

    # And parse the query
    queryparser.set_database (db)
    query = queryparser.parse_query (querystring, xapian_flags)
    # Use an Enquire object on the database to run the query
    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    matches = []
    for match in enquire.get_mset(offset, pagesize):
        s_fields = match.document.get_data()
        fields =  unicode (s_fields,'utf-8')
#        print u"%(rank)i: #%(docid)3.3i %(data)s" % {
#        'rank': match.rank + 1,
#        'docid': match.docid,
#        'data': fields
#        }
#        part = [match.rank,  match.docid,  fields]
        matches.append(fields)
    

    return matches


if __name__=='__main__':

    parser = argparse.ArgumentParser('Get a comparison of recipes') 

    parser.add_argument('-s' ,'--search',  help = 'The recipe you want to search and compare')
    parser.add_argument('-p' ,'--prefix',  help = 'The path to the environment where food database is')

    args = parser.parse_args()
    if args.search and args.prefix:
        search_obj = rcpt.Google_search(args.search,  args.prefix)
        ingredients_obj = search_obj.ingredients ()
        parsed_ingredients = ingredients_obj.parsed_ingredients()
        sorted = sort_ingredients(search_obj.database_obj,  parsed_ingredients)
        pprint (dict(sorted))
#        with file('/home/carolina/Desktop/enfil.csv)
        
        
        
        
        

    
