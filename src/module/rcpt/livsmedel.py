#!/usr/bin/python
#-*- coding:  utf8 -*-

import os
import argparse
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
        self.load_csv_data ()
        self.load_simplewords_list ()

    def load_csv_data (self):
        """reads database and returns a csv reader"""
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

    def search_food (self,  query):
        """Search the food list for close match,
        the query can be a long string with additional non food words"""
        
        

class Food (object):
    """Hold information about a particular food found in the database"""
    pass





if __name__=='__main__':

    parser = argparse.ArgumentParser('Get data about food in "Livsmedelsdatabasen"') 

    parser.add_argument('-s' ,'--search',  help = 'The recipe you want to search and compare')

    args = parser.parse_args()
    if args.search:
        from pprint import pprint 
        db = Database (args.search)
        head = db.csv_header
        titles = db.csv_col_titles
        foods = db.foods_list
        print head
        print titles
        print foods
        print len(foods)
        
        
        
        
