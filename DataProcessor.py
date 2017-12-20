__author__ = 'Caitrin'

import pickle
import pymongo
import os
import datetime
from bson.json_util import dumps
from pymongo import MongoClient
import accommodation
from collections import Counter
import scipy
from scipy.stats import ttest_rel
import csv
class DataProcessor:

    def __init__(self, subreddit_list, daterange, post_length_limit):
        self.daterange = daterange
        self.subreddit_list = subreddit_list
        self.client = MongoClient()
        self.DATA_PATH = "/home/carmst16/NLP_Final_Project/RedditAccomodation/data/"
        self.LIWC_RESULTS_PATH = "/home/carmst16/NLP_Final_Project/RedditAccomodation/LIWC_Output_Restricted0/"
        self.LIWCInputPath = "/home/carmst16/NLP_Final_Project/RedditAccomodation/LIWC_Restr_0_Input/"
        self.db = self.client.reddit
        self.comments = self.db.comms
        self.all_subreddit_comment_tuples = dict()
        self.feature_list = ['pronoun', 'ppron', 'i', 'we', 'you', 'shehe', 'they', 'ipron', 'article', 'prep', 'conj', 'negate', 'quant', 'discrep', 'tentat', 'certain', 'differ', 'Dic']
        self.results_path = "/home/carmst16/NLP_Final_Project/RedditAccomodation/results0/"
        self.minimum_lenth = 0
        self.maximum_number_of_comments = 1000
    #thanks to https://stackoverflow.com/questions/34964878/python-generate-a-dictionarytree-from-a-list-of-tuples
    def order_comment_threads(self, list_of_ids):

        a = list_of_ids
        print a
        nodes = {}
        for i in a:
            id, parent_id = i
            nodes[id] = {'id': id }

        # pass 2: create trees and parent-child relations
        forest = []
        for i in a:
            print "hi"
            print nodes
            id, parent_id = i
            node = nodes[id]

            # either make the node a new tree or link it to its parent
            if id == parent_id:
                # start a new tree in the forest
                forest.append(node)
            else:
                # add new_node as child to parent
                try:
                    parent = nodes[parent_id]
                except:
                    continue
                if not 'children' in parent:
                    # ensure parent has a 'children' field
                    parent['children'] = []
                children = parent['children']
                children.append(node)

        return nodes

    def get_subreddit_data(self, subreddit):
        start = self.daterange[0]
        end = self.daterange[1]

        all_data_file_path = self.DATA_PATH+subreddit+"_"+self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y")+".pkl"

        print subreddit
        #TODO: This could be really big
        if os.path.exists(all_data_file_path):
            print "yay we have it"
            indexed_subreddit_data = pickle.load(open(all_data_file_path, "r"))
        else:
            print "didn't already have it :("
            count = self.comments.find({"subreddit" : subreddit, 'created_time': {'$gte': start, '$lt': end}}).count()
            print "retrieving " + str(count) + " documents"
            subreddit_data = list(self.comments.find({"subreddit" : subreddit, 'created_time': {'$gte': start, '$lt': end}},{"body" : 1, "parent_id" : 1, "link_id" :1, "author" :1}))

            indexed_subreddit_data = dict()
            for comment in subreddit_data:
                indexed_subreddit_data[comment["_id"]] = comment

            pickle.dump(indexed_subreddit_data, open(all_data_file_path, "w"))

        return indexed_subreddit_data

    def get_basic_pairs(self):
        for subreddit in self.subreddit_list:

            total_so_far = 0
            indexed_subreddit_data = self.get_subreddit_data(subreddit)

            all_link_ids = dict()

            for comment in indexed_subreddit_data:

                #print indexed_subreddit_data[comment]
                parent_id = indexed_subreddit_data[comment]["parent_id"][3:]
                link_id = indexed_subreddit_data[comment]["link_id"][3:]
                id = indexed_subreddit_data[comment]["_id"]

                if link_id not in all_link_ids:
                    all_link_ids[link_id] = list()

                all_link_ids[link_id].append((id, parent_id))

            comment_tuples = dict()
            for link in all_link_ids:
                if total_so_far > self.maximum_number_of_comments:
                        break
                for paren_child in all_link_ids[link]:
                    if total_so_far > self.maximum_number_of_comments:
                        break
                    id, parent_id = paren_child
                    if (id in indexed_subreddit_data) and (parent_id in indexed_subreddit_data):

                        par = indexed_subreddit_data[parent_id]["author"]
                        chil = indexed_subreddit_data[id]["author"]

                        #print par, chil
                        #print type(par), type(chil)
                        par = par.encode('ascii','ignore')
                        chil = chil.encode('ascii','ignore')

                        if ("deleted" in par) or ("deleted" in chil):
                            continue

                        if (par, chil) not in comment_tuples:
                            comment_tuples[(par, chil)] = list()

                        parent_body = indexed_subreddit_data[parent_id]["body"]
                        child_body = indexed_subreddit_data[id]["body"]

                        if parent_body is not "" and child_body is not "":
                            parent_body = parent_body.encode('utf-8').strip()
                            child_body = child_body.encode('utf-8').strip()
                            comment_tuples[(par, chil)].append((parent_body, child_body))
                            total_so_far += 1

            self.all_subreddit_comment_tuples[subreddit] = comment_tuples

    #should have been decorated. oh well. copy paste is love
    def get_length_restricted_pairs(self):

        for subreddit in self.subreddit_list:
            total_so_far = 0
            indexed_subreddit_data = self.get_subreddit_data(subreddit)

            all_link_ids = dict()

            for comment in indexed_subreddit_data:

                #print indexed_subreddit_data[comment]
                parent_id = indexed_subreddit_data[comment]["parent_id"][3:]
                link_id = indexed_subreddit_data[comment]["link_id"][3:]
                id = indexed_subreddit_data[comment]["_id"]

                if link_id not in all_link_ids:
                    all_link_ids[link_id] = list()

                all_link_ids[link_id].append((id, parent_id))

            comment_tuples = dict()
            for link in all_link_ids:
                if total_so_far > self.maximum_number_of_comments:
                        break
                for paren_child in all_link_ids[link]:
                    if total_so_far > self.maximum_number_of_comments:
                        break

                    id, parent_id = paren_child
                    if (id in indexed_subreddit_data) and (parent_id in indexed_subreddit_data):

                        if len(indexed_subreddit_data[id]["body"] < self.minimum_lenth):
                            continue
                        if len(indexed_subreddit_data[parent_id]["body"] < self.minimum_lenth):
                            continue

                        par = indexed_subreddit_data[parent_id]["author"]
                        chil = indexed_subreddit_data[id]["author"]

                        #print par, chil
                        #print type(par), type(chil)
                        par = par.encode('ascii','ignore')
                        chil = chil.encode('ascii','ignore')

                        if ("deleted" in par) or ("deleted" in chil):
                            continue

                        if (par, chil) not in comment_tuples:
                            comment_tuples[(par, chil)] = list()

                        parent_body = indexed_subreddit_data[parent_id]["body"]
                        child_body = indexed_subreddit_data[id]["body"]

                        if parent_body is not "" and child_body is not "":
                            parent_body = parent_body.encode('utf-8').strip()
                            child_body = child_body.encode('utf-8').strip()
                            comment_tuples[(par, chil)].append((parent_body, child_body))
                            total_so_far += 1
            self.all_subreddit_comment_tuples[subreddit] = comment_tuples


    def create_tuples(self, method):

        if method == "basic_pairs":
            self.get_basic_pairs()

        if method == "length_restricted":
            self.get_length_restricted_pairs()

    def get_interactions_list(self):
        pass

    def create_txt_files(self):

        for subreddit in self.subreddit_list:
            file_path = self.LIWCInputPath + subreddit + self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y") + "/"

            if not os.path.exists(file_path):
                os.makedirs(file_path, 0777)

            accommodation.write_to_txt(self.all_subreddit_comment_tuples[subreddit], file_path)

    #for one stylistic dimension
    def two_tailed_paired_t_test(self, acc_terms):

        #"in order to allay concerns regarding the independence assumption of the test, for each two users a and b we only consider one of the two possible ordered pairs"
        already_passed_couples = []
        first_term_list = []
        second_term_list = []
        for user1, user2 in acc_terms:
            if (user2, user1) in already_passed_couples:
                continue
            else:
                already_passed_couples.append((user1, user2))

            first_term_list.append(acc_terms[(user1, user2)][0])
            second_term_list.append(acc_terms[(user1, user2)][1])
        statistic, pvalue = ttest_rel(first_term_list, second_term_list)

        return statistic, pvalue

    def get_accommodation_stats(self, method):

        results_dict = {}
        for subreddit in self.subreddit_list:
            results_dict[subreddit] = {}
            liwc_path = self.LIWC_RESULTS_PATH + subreddit+self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y")+".txt"

            for feature in self.feature_list:
                acc_dict, acc_terms = accommodation.accommodation_dict(self.all_subreddit_comment_tuples[subreddit], feature, liwc_path)
                if acc_dict is None:
                    print "no results"
                    continue
                stat_results = self.two_tailed_paired_t_test(acc_terms)
                results_dict[subreddit][feature] = (accommodation.dataset_accom(acc_dict), stat_results[0], stat_results[1])

                print subreddit, feature, results_dict[subreddit][feature]
                 #print " \t influence", accommodation.influence(acc_dict)
                #print accommodation.calculate_influence_dict(acc_dict)

        filename = self.results_path + "accom_stats_"+ method+ "_" + self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y")+".csv"
        with open(filename, 'wb') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(["subreddit", "feature", "accom_value", "statistic", "pvalue"])
            for subreddit in self.subreddit_list:
                for feature in self.feature_list:
                    toPrint = [subreddit, feature] + [x for x in results_dict[subreddit][feature]]
                    csvwriter.writerow(toPrint)
def main():

    original_umask = os.umask(0)
    date1 = datetime.datetime(2015, 1, 1)
    date2 =datetime.datetime(2016, 12, 30)

    #intitial_subreddit_list  = ["Agorism","alltheleft","Anarchism","AnarchistNews","AnarchObjectivism","Anarcho_Capitalism","Anarchy101","BullMooseParty","centrist","christian_ancaps","Classical_Liberals","communism","Conservative","conservatives","CornbreadLiberals","DebateaCommunist","DebateCommunism","democrats","demsocialist","futuristparty","Green_Anarchism","GreenParty","labor","leftcommunism","leninism","Liberal","Libertarian","LibertarianDebates","LibertarianLeft","libertarianmeme","LibertarianSocialism","LibertarianWomen","moderatepolitics","monarchism","neoprogs","NeutralPolitics","new_right","Objectivism","paleoconservative","peoplesparty","PirateParty","progressive","Republican","republicans","SocialDemocracy","socialism","TrueLibertarian","Trueobjectivism","voluntarism"]
    #test_subreddit_list = ["socialism"]
    final_subreddit_list = ["monarchism", "DebateCommunism", "socialism", "SocialDemocracy", "LibertarianSocialism", "conservatives", "GreenParty", "PirateParty", "democrats", "Objectivism", "moderatepolitics", "christian_ancaps", "futuristparty", "DebateaCommunist", "LibertarianDebates", "paleoconservative", "Agorism", "BullMooseParty", "Liberal"]
    dp = DataProcessor(final_subreddit_list, (date1, date2), 100)
    method = "basic_pairs"
    dp.create_tuples(method)
    #need to first initialize self.all_subreddit_comment_tuples!!
    #dp.create_txt_files()
    #need to first have finished LIWC inputs.
    dp.get_accommodation_stats(method)


if __name__ == "__main__":
    main()
