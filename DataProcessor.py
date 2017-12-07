__author__ = 'Caitrin'

import pickle
import pymongo
import os
import datetime

from pymongo import MongoClient

from collections import Counter

class DataProcessor:

    def __init__(self, subreddit_list, daterange, post_length_limit):
        self.daterange = daterange
        self.subreddit_list = subreddit_list
        self.client = MongoClient()
        self.DATA_PATH = "/home/carmst16/RedditAccomodation/data/"
        self.db = self.client.reddit
        self.comments = self.db.comms

    def order_comment_threads(self, list_of_ids):

        a = list_of_ids
        nodes = {}
        for i in a:
            id, parent_id = i
            nodes[id] = { 'id': id }

        # pass 2: create trees and parent-child relations
        forest = []
        for i in a:
            id, parent_id = i
            node = nodes[id]

            # either make the node a new tree or link it to its parent
            if id == parent_id:
                # start a new tree in the forest
                forest.append(node)
            else:
                # add new_node as child to parent
                parent = nodes[parent_id]
                if not 'children' in parent:
                    # ensure parent has a 'children' field
                    parent['children'] = []
                children = parent['children']
                children.append(node)

        return nodes

    def get_subreddit_data(self, subreddit):
        start = self.daterange(0)
        end = self.daterange(1)

        all_data_file_path = self.DATA_PATH+subreddit+"_"+self.daterange(0)+"_"+ self.daterange(1).pkl

        #TODO: This could be really big
        if os.path.exists(all_data_file_path):
            print "yay we have it"
            subreddit_data = pickle.load(open(all_data_file_path, "r"))
        else:
            print "didn't already have it :("
            count = self.comments.find({"subreddit" : subreddit, 'created_time': {'$gte': start, '$lt': end}},
                                       {"body" : 1}).count()
            print "retrieving " + count + " documents"
            subreddit_data = self.comments.find({"subreddit" : subreddit, 'created_time': {'$gte': start, '$lt': end}},
                                                {"body" : 1})

            pickle.dump(subreddit_data, open(all_data_file_path, "w"))

        return subreddit_data

    def order_comments(self, subreddit):

        subreddit_data = self.get_subreddit_data(subreddit)
        all_link_ids = dict()
        ordered_all_link_ids = dict()

        for comment in subreddit_data:
            parent_id = comment["parent_id"][3:]
            link_id = comment["link_id"][3:]
            id = comment["id"]

            if link_id not in all_link_ids:
                all_link_ids[link_id] = list()

            all_link_ids.append((id, parent_id))


        for link in all_link_ids:
            ordered_list = self.order_comment_threads(all_link_ids[link])
            ordered_all_link_ids[link] = ordered_list

        print ordered_all_link_ids
        return ordered_all_link_ids

def main():


    date1 = datetime.datetime(2014, 11, 1)
    date2 =datetime.datetime(2014, 11, 2)

    dp = DataProcessor(["mcgill"], (date1, date2), 100)
    dp.order_comments("mcgill")


if "__name__" == "__main__":
    main()