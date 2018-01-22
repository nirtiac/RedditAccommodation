__author__ = 'Caitrin'

import pickle
import pymongo
import os
import datetime
from pymongo import MongoClient
import accommodation
from collections import Counter
import scipy
from scipy.stats import ttest_rel
import csv
import liwc_cohesion
import string
import re
import new_accomm



#create a new dataprocessor object everytime you want to work with new subreddits and dates
class DataProcessor:


    def __init__(self, subreddit_list, daterange, base_path):
        self.daterange = daterange
        self.subreddit_list = subreddit_list
        self.client = MongoClient()
        self.db = self.client.reddit
        self.comments = self.db.comms
        self.BASE_PATH = base_path
        self.DATA_PATH = self.BASE_PATH + "data/"
        self.FOR_LIWC_INPUT_PATH = self.BASE_PATH + "for_liwc_input/"
        self.LIWC_OUTPUTED_PATH = self.BASE_PATH + "liwc_outputed_path"

        self.turns = {}
        self.TURNS_DATA_PATH = "/home/carmst16/NLP_Final_Project/RedditAccomodation/LIWC_TURNS/"

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

    #returns indexed subreddit data
    def get_subreddit_data(self, subreddit):
        start = self.daterange[0]
        end = self.daterange[1]

        all_data_file_path = self.DATA_PATH+subreddit+ "_" +self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y")+".pkl"

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

    #returns list of tuples, with restrictions
    def create_tuples(self, maximum_number_of_comment_pairs, minimum_convo_length = 5, length_restriction = False, minimum_length = 0):
        all_basic_subreddit_comment_tuples = {}
        for subreddit in self.subreddit_list:

            all_basic_subreddit_comment_tuples[subreddit] = {}

            total_so_far = 0
            indexed_subreddit_data = self.get_subreddit_data(subreddit)

            all_link_ids = dict()

            for comment in indexed_subreddit_data:

                parent_id = indexed_subreddit_data[comment]["parent_id"][3:]
                link_id = indexed_subreddit_data[comment]["link_id"][3:]
                id = indexed_subreddit_data[comment]["_id"]

                if link_id not in all_link_ids:
                    all_link_ids[link_id] = list()

                all_link_ids[link_id].append((id, parent_id))

            comment_tuples = dict()
            for link in all_link_ids:
                if total_so_far > maximum_number_of_comment_pairs:
                        break
                for paren_child in all_link_ids[link]:
                    if total_so_far > maximum_number_of_comment_pairs:
                        break
                    id, parent_id = paren_child
                    if (id in indexed_subreddit_data) and (parent_id in indexed_subreddit_data):

                        if length_restriction:
                            if len(indexed_subreddit_data[id]["body"]) < minimum_length:
                                continue
                            if len(indexed_subreddit_data[parent_id]["body"]) < minimum_length:
                                continue

                        par = indexed_subreddit_data[parent_id]["author"]
                        chil = indexed_subreddit_data[id]["author"]
                        par = par.encode('ascii','ignore')
                        chil = chil.encode('ascii','ignore')

                        if ("deleted" in par) or ("deleted" in chil):
                            continue

                        if par in chil:
                            continue

                        if (par, chil) not in comment_tuples:
                            comment_tuples[(par, chil)] = list()

                        parent_body = indexed_subreddit_data[parent_id]["body"]
                        child_body = indexed_subreddit_data[id]["body"]

                        regex = re.compile('[^a-zA-Z]')
                        if parent_body is not "" and child_body is not "":
                            parent_body = parent_body.encode('utf-8').strip()
                            child_body = child_body.encode('utf-8').strip()
                            parent_body = regex.sub(' ', parent_body)
                            child_body = regex.sub(' ', child_body)
                            comment_tuples[(par, chil)].append([str(parent_body), str(child_body)])
                            total_so_far += 1

            for interac in comment_tuples:
                if len(comment_tuples[interac]) > minimum_convo_length:
                    all_basic_subreddit_comment_tuples[subreddit][interac] = comment_tuples[interac]

    def create_txt_files(self, all_subreddit_comment_tuples, maximum_number_of_comment_pairs, minimum_convo_length = 5, length_restriction = False, minimum_length = 0):

        for subreddit in self.subreddit_list:
            file_path = self.FOR_LIWC_INPUT_PATH + subreddit + self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y") + str(maximum_number_of_comment_pairs) + "_" + str(minimum_convo_length) + str(minimum_length) + "/"

            if not os.path.exists(file_path):

                accommodation.write_to_txt(all_subreddit_comment_tuples[subreddit], file_path)

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
        print "in accom stats"
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

                #print subreddit, feature, results_dict[subreddit][feature]
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

        return results_dict

    def test_accom_cohesion_pearson_correlation(self, results_dict):

        #copy-pasted in I know
        cohesion_dict = {"Agorism":3.53571, "BullMooseParty":3.37736, "christian_ancaps":4.04762, "conservatives":3.93277, "DebateaCommunist":4.27632, "DebateCommunism":3.70792, "democrats":3.65179, "futuristparty":3.90476, "GreenParty":4.81633, "Liberal":4.32143, "LibertarianDebates":3.62857, "LibertarianSocialism":4.08929, "moderatepolitics":3.50000, "monarchism":4.45468, "Objectivism":3.93878, "paleoconservative":3.78571, "PirateParty":4.02679, "SocialDemocracy":4.22050, "socialism":3.91860}
        #cohesion_dict = {"monarchism" : 5}
        x = []
        y = []
        for subreddit in results_dict:
            x.append(cohesion_dict[subreddit])
            accom_values = [results_dict[subreddit][i][0] for i in results_dict[subreddit]]
            y.append(sum(accom_values)/float(len(accom_values)))

        print "cohesion_dict", x
        print "results_dict", y
        coef = scipy.stats.pearsonr(x, y)
        print coef
        return coef

    def turn_tuples_to_list(self):
        just_as_list = {}
        for subreddit in self.all_subreddit_comment_tuples:
            just_as_list[subreddit] = []
            for pair in self.all_subreddit_comment_tuples[subreddit]:
                for convo in self.all_subreddit_comment_tuples[subreddit][pair]:
                    just_as_list[subreddit].append(convo)

        self.turns = just_as_list

    def write_cohesion_to_text(self):
        for subreddit in self.turns:
            filepath = self.TURNS_DATA_PATH + "subreddit" + str(self.minimum_length) + "_" + subreddit+self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y") + "/"
            if not os.path.exists(filepath):
                os.makedirs(filepath, 0777)
            liwc_cohesion.write_to_txt(self.turns[subreddit], filepath)

    def get_cohesion_results(self):

        results_dict = {}
        for subreddit in self.subreddit_list:
            results_dict[subreddit] = {}
            liwc_path = "cohesion_results/" + "subreddit" + str(self.minimum_length) + "_" + subreddit+self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y") + ".txt"

            for feature in self.feature_list:
                cohesion_value = liwc_cohesion.cohesion_value(feature, self.turns[subreddit], liwc_path)

                print subreddit, feature, cohesion_value
