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
class DataProcessor:


    def __init__(self, subreddit_list, daterange, post_length_limit):
        self.daterange = daterange
        self.subreddit_list = subreddit_list
        self.client = MongoClient()
        self.DATA_PATH = "/home/carmst16/NLP_Final_Project/RedditAccomodation/data/"
        self.LIWCInputPath = "/home/carmst16/NLP_Final_Project/RedditAccomodation/LIWC_just_socialism/"
        self.LIWC_RESULTS_PATH = "/home/carmst16/NLP_Final_Project/RedditAccomodation/LIWC_Output_Restricted0/"
        self.db = self.client.reddit
        self.comments = self.db.comms
        self.all_subreddit_comment_tuples = dict()
        self.feature_list = ['pronoun', 'ppron', 'i', 'we', 'you', 'shehe', 'they', 'ipron', 'article', 'prep', 'conj', 'negate', 'quant', 'discrep', 'tentat', 'certain', 'differ', 'Dic']
        self.results_path = "/home/carmst16/NLP_Final_Project/RedditAccomodation/results_sunyams_thing/"
        self.minimum_length = 10
        self.maximum_number_of_comment_pairs = 1000
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
                if total_so_far > self.maximum_number_of_comment_pairs:
                        break
                for paren_child in all_link_ids[link]:
                    if total_so_far > self.maximum_number_of_comment_pairs:
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


                        #if they're the same person
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
                if total_so_far > self.maximum_number_of_comment_pairs:
                        break
                for paren_child in all_link_ids[link]:
                    if total_so_far > self.maximum_number_of_comment_pairs:
                        break

                    id, parent_id = paren_child
                    if (id in indexed_subreddit_data) and (parent_id in indexed_subreddit_data):

                        if len(indexed_subreddit_data[id]["body"]) < self.minimum_length:
                            continue
                        if len(indexed_subreddit_data[parent_id]["body"]) < self.minimum_length:
                            continue

                        par = indexed_subreddit_data[parent_id]["author"]
                        chil = indexed_subreddit_data[id]["author"]

                        #print par, chil
                        #print type(par), type(chil)
                        par = par.encode('ascii','ignore')
                        chil = chil.encode('ascii','ignore')

                        if ("deleted" in par) or ("deleted" in chil):
                            continue

                        #if they're the same person
                        if par in chil:
                            continue

                        if (par, chil) not in comment_tuples:
                            comment_tuples[(par, chil)] = list()

                        parent_body = indexed_subreddit_data[parent_id]["body"]
                        child_body = indexed_subreddit_data[id]["body"]

                        if parent_body is not "" and child_body is not "":
                            parent_body = parent_body.encode('utf-8').strip()
                            child_body = child_body.encode('utf-8').strip()
                            parent_body.translate(None, string.punctuation)
                            child_body.translate(None, string.punctuation)
                            comment_tuples[(par, chil)].append((str(parent_body), str(child_body)))
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
        print "in accom stats"
        results_dict = {}
        for subreddit in self.subreddit_list:
            results_dict[subreddit] = {}
            liwc_path = self.LIWC_RESULTS_PATH + subreddit+self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y")+".txt"

            for feature in self.feature_list:
                acc_dict, acc_terms = new_accomm.accommodation(self.all_subreddit_comment_tuples[subreddit], feature, liwc_path)
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


    def get_changed_context_tuples(self):


        pass

def main():

    original_umask = os.umask(0)
    date1 = datetime.datetime(2015, 1, 1)
    date2 =datetime.datetime(2016, 12, 30)

    #intitial_subreddit_list  = ["Agorism","alltheleft","Anarchism","AnarchistNews","AnarchObjectivism","Anarcho_Capitalism","Anarchy101","BullMooseParty","centrist","christian_ancaps","Classical_Liberals","communism","Conservative","conservatives","CornbreadLiberals","DebateaCommunist","DebateCommunism","democrats","demsocialist","futuristparty","Green_Anarchism","GreenParty","labor","leftcommunism","leninism","Liberal","Libertarian","LibertarianDebates","LibertarianLeft","libertarianmeme","LibertarianSocialism","LibertarianWomen","moderatepolitics","monarchism","neoprogs","NeutralPolitics","new_right","Objectivism","paleoconservative","peoplesparty","PirateParty","progressive","Republican","republicans","SocialDemocracy","socialism","TrueLibertarian","Trueobjectivism","voluntarism"]
    test_subreddit_list = ["monarchism"]
    final_subreddit_list = ["monarchism", "DebateCommunism", "socialism", "SocialDemocracy", "LibertarianSocialism", "conservatives", "GreenParty", "PirateParty", "democrats", "Objectivism", "moderatepolitics", "christian_ancaps", "futuristparty", "DebateaCommunist", "LibertarianDebates", "paleoconservative",  "BullMooseParty", "Liberal"]
    pared_subreddit_list = ["monarchism", "DebateCommunism", "socialism", "SocialDemocracy", "conservatives", "GreenParty",  "democrats", "Objectivism", "moderatepolitics", "futuristparty", "DebateaCommunist", "LibertarianDebates", "Liberal"]

    dp = DataProcessor(pared_subreddit_list, (date1, date2), 100)
    method = "basic_pairs"
    dp.create_tuples(method)
    #dp.turn_tuples_to_list()
    #dp.get_cohesion_results()

    #dp.write_cohesion_to_text()
    #need to first initialize self.all_subreddit_comment_tuples!!
    #dp.create_txt_files()
    #need to first have finished LIWC inputs.
    results_dict = dp.get_accommodation_stats(method)
    dp.test_accom_cohesion_pearson_correlation(results_dict)

if __name__ == "__main__":
    main()
