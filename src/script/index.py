#!/usr/bin/python
#-*- coding:  utf8 -*-

import argparse
import rcpt.livsmedel
import xapian


def index (database_obj):
    count = 0
    xap_db_path = database_obj.xap_db_path
    
    # create or open the the database
    db = xapian.WritableDatabase(xap_db_path, xapian.DB_CREATE_OR_OPEN)
    
    # set up a termgenerator thats going to be used in indexing
    termgenerator = xapian.TermGenerator()
    termgenerator.set_stemmer(xapian.Stem("swedish"))
    
    
    foods_list = database_obj.foods_list
    
    for food in foods_list:
        xap_doc_id = food
        food_name_joint = '"' +food + '"'
        
        identifier = food
        
        # We make a document and tell the term generator to use this.
        doc = xapian.Document()
        termgenerator.set_document(doc)
        
        fields = {'food': food}
        str_fields = str(fields)
        
        doc.set_data (str_fields)

        # Index each field with a suitable prefix.
        termgenerator.index_text(food_name_joint, 1, 'XFOOD')
        
        # Index fields without prefixes for general search.
        termgenerator.index_text(food)
        
        # We use the identifier to ensure each object ends up in the
        # database only once no matter how many times we run the
        # indexer.
        idterm = u"Q" + identifier
        doc.add_boolean_term(idterm)
        db.replace_document(idterm, doc)
        
        count +=1
        print count

    






















#-----------------------------------------------------------------------------------------------------------
if __name__=='__main__':#gÃ¶r att det bara kÃ¶rs om det Ã¤r huvudprogrammet


    parser = argparse.ArgumentParser('Index the food names') 

    parser.add_argument('-p' ,'--prefix',  help = 'The path to database')
    parser.add_argument ('command',  help="Valid actions: index")


    args = parser.parse_args()
    if args.prefix:
        database_obj = rcpt.livsmedel.Database (args.prefix)
        print args.prefix
    else:
        import sys
        parser.error ('You have to give the path to the database') 
        sys.exit (-1)
        
    if args.command =='index':
        index (database_obj)






