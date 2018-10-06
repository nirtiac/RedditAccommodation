import pickle
import pymongo
import os
import datetime
from pymongo import MongoClient
import accommodation
from collections import Counter, namedtuple
import scipy
from scipy.stats import ttest_rel, fisher_exact
import csv
import liwc_cohesion
import string
import re
from recordclass import recordclass
import numpy as np

#create a new dataprocessor object everytime you want to work with new subreddits and dates
class DataProcessor:

    def __init__(self, subreddit_list, daterange, base_path, feature_list, maximum_number_of_comment_pairs, length_restriction=False, minimum_convo_length=2, minimum_length=0):
        self.daterange = daterange
        self.subreddit_list = subreddit_list
        self.client = MongoClient(serverSelectionTimeoutMS=30,  connectTimeoutMS=20000)
        self.db = self.client.reddit
        self.comments = self.db.comms
        self.BASE_PATH = base_path
        self.DATA_PATH = self.BASE_PATH + "data/"
        self.RESULTS_PATH = self.BASE_PATH + "results/"
        self.FOR_LIWC_INPUT_PATH = self.BASE_PATH + "for_liwc_input/"
        self.FEATURE_LIST = feature_list
        self.turns = {}
        self.MAX_PAIRS = maximum_number_of_comment_pairs
        self.MIN_CONVO_LENGTH = minimum_convo_length
        self.LENGTH_RESTRICTION = length_restriction
        self.MIN_STRING_LENGTH = minimum_length
        self.TURNS_DATA_PATH = self.BASE_PATH + "ALL_LIWC_TURNS/"
        self.pair_conv_str = self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y") + "_" + str(self.MAX_PAIRS) + "_" + str(self.MIN_CONVO_LENGTH) + "_" + str(self.MIN_STRING_LENGTH) + "_"

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

        all_data_file_path = self.DATA_PATH+subreddit+ "_" +self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y")+".pickle"
        print all_data_file_path
        #TODO: This could be really big
        if os.path.exists(all_data_file_path):
            print "Yay, we have it."
            indexed_subreddit_data = pickle.load(open(all_data_file_path, "r"))

        else:
            print "Didn't already have it :("
            subreddit_data = list(self.comments.find({"subreddit":subreddit, 'created_time':{'$gte':start, '$lt':end}}, {"created_time":1, "body":1, "parent_id":1, "link_id":1, "author":1, "score":1}))
            indexed_subreddit_data = dict()
            for comment in subreddit_data:
                indexed_subreddit_data[comment["_id"]] = comment

            pickle.dump(indexed_subreddit_data, open(all_data_file_path, "w"))
        return indexed_subreddit_data

    #returns list of tuples, with restrictions
    '''
        The output is a dictionary. Key is the subreddit-name; Value is a dictionary itself.
        That inner dictionary's Key is a ('user1', 'user2') tuple; Value is a list lists (basically a list of threads in that subreddit.) The inner list always has two elements/strings in it.
    '''
    def create_tuples(self, remove_deleted_users):
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
                if total_so_far > self.MAX_PAIRS:
                        break
                for paren_child in all_link_ids[link]:
                    if total_so_far > self.MAX_PAIRS:
                        break
                    id, parent_id = paren_child
                    if (id in indexed_subreddit_data) and (parent_id in indexed_subreddit_data):

                        if self.LENGTH_RESTRICTION:
                            if len(indexed_subreddit_data[id]["body"]) < self.MIN_STRING_LENGTH:
                                continue
                            if len(indexed_subreddit_data[parent_id]["body"]) < self.MIN_STRING_LENGTH:
                                continue

                        par = indexed_subreddit_data[parent_id]["author"]
                        chil = indexed_subreddit_data[id]["author"]
                        par = par.encode('ascii','ignore')
                        chil = chil.encode('ascii','ignore')

                        # Deleted users filter:
                        if remove_deleted_users:
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
                if len(comment_tuples[interac]) > self.MIN_CONVO_LENGTH:
                    all_basic_subreddit_comment_tuples[subreddit][interac] = comment_tuples[interac]

        return all_basic_subreddit_comment_tuples



    def get_user_karma(self, user, cur_date):
        """
        Gets the user's comment karma up to the given date.
        :param user: username
        :param cur_date: the given date
        :return: the karma as an integer
        """
        pass

    #TODO: get rid of threads??
    def bin_data_on_karma(self, indexed_subreddit_data):
        """
        Given a dictionary of subreddit data indexed on comment id, bin comment-reply pairs based on their comment and reply scores
        :param indexed_subreddit_data:
        :return: a dictionary of key (comment_karma, reply_karma) and value list of (comment_text, reply) tuples
        """

        ids_touched = [] #this keeps track of all ids used in creating our binned data. we don't want to use somethign twice

        #creating a recordclass object - a mutable named tuple
        CommentReply = recordclass("CommentReply", ["comment_text", "reply_text", "comment_karma", "reply_karma"])
        unbinned_data = []


        for reply_id in indexed_subreddit_data:
            if reply_id in ids_touched:
                continue
            comment_id = indexed_subreddit_data[reply_id]["parent_id"]
            if comment_id not in indexed_subreddit_data:
                continue

            reply = indexed_subreddit_data[reply_id]
            comment = indexed_subreddit_data[comment_id]

            reply_karma = self.get_user_karma(reply["username"], reply["created_time"])
            comment_karma = self.get_user_karma(comment["username"], comment["created_time"])


            reply_text = reply["body"]
            comment_text = comment["body"]

            unbinned_data.append(CommentReply(comment_text, reply_text, comment_karma, reply_karma))

        all_comment_karma = [x.comment_karma for x in unbinned_data]
        all_reply_karma = [x.reply_karma for x in unbinned_data]

        max_comment_karma = max(all_comment_karma)
        min_comment_karma = min(all_comment_karma)

        max_reply_karma = max(all_comment_karma)
        min_reply_karma = min(all_reply_karma)

        bins = np.linspace(0.0, 1.0, num=20)

        #normalize both comment_karma and reply_karma and replace with the bin #

        for t in unbinned_data:
            normed_comm = (float(t.comment_karma - min_comment_karma))/(float(max_comment_karma - min_comment_karma))
            t.comment_karma = np.digitize([normed_comm], bins)[0]

            normed_reply = (float(t.reply_karma - min_reply_karma))/(float(max_reply_karma - min_reply_karma))
            t.reply_karma = np.digitize([normed_reply], bins)[0]

        binned_data = {}

        for t in unbinned_data:
            if (t.comment_karma, t.reply_karma) not in binned_data:
                binned_data[(t.comment_karma, t.reply_karma)] = []
            binned_data[(t.comment_karma, t.reply_karma)].append((t.comment_text, t.reply_text))

        return binned_data




#    def create_txt_files(self):
#        all_basic_subreddit_comment_tuples = self.create_tuples()
#        for subreddit in self.subreddit_list:
#            print "Working on: ", subreddit
#            if not os.path.exists(self.FOR_LIWC_INPUT_PATH+self.pair_conv_str):
#                os.makedirs(self.FOR_LIWC_INPUT_PATH+self.pair_conv_str, 0777)
#
#            accommodation.write_to_txt(all_basic_subreddit_comment_tuples[subreddit], self.FOR_LIWC_INPUT_PATH, self.pair_conv_str, subreddit)

#    #for one stylistic dimension
#    def two_tailed_paired_t_test(self, acc_terms):
#        #"in order to allay concerns regarding the independence assumption of the test, for each two users a and b we only consider one of the two possible ordered pairs"
#        already_passed_couples = []
#        first_term_list = []
#        second_term_list = []
#        for user1, user2 in acc_terms:
#            if (user2, user1) in already_passed_couples:
#                continue
#            else:
#                already_passed_couples.append((user1, user2))
#
#            first_term_list.append(acc_terms[(user1, user2)][0])
#            second_term_list.append(acc_terms[(user1, user2)][1])
#        statistic, pvalue = ttest_rel(first_term_list, second_term_list)
#
#        return statistic, pvalue
#
#    def get_accommodation_stats(self, tuples, liwc_results_file):
#        results_dict = {}
#        for subreddit in self.subreddit_list:
#            results_dict[subreddit] = {}
#            liwc_path = liwc_results_file
#
#            for feature in self.FEATURE_LIST:
#                acc_dict, acc_terms = accommodation.accommodation_dict(tuples[subreddit], feature, liwc_path, subreddit, self.pair_conv_str)
#                # print feature, acc_dict
#                if acc_dict is None:
#                    continue
#                stat_results = self.two_tailed_paired_t_test(acc_terms)
#                results_dict[subreddit][feature] = (accommodation.dataset_accom(acc_dict), stat_results[0], stat_results[1])
#
#                #print subreddit, feature, results_dict[subreddit][feature]
#                 #print " \t influence", accommodation.influence(acc_dict)
#                #print accommodation.calculate_influence_dict(acc_dict)
#
#        filename = self.RESULTS_PATH + "accom_stats_" + self.daterange[0].strftime("%B%d_%Y")+"_" + self.daterange[1].strftime("%B%d_%Y") + "_" + str(self.MAX_PAIRS) + "_" + str(self.MIN_CONVO_LENGTH) + "_" + str(self.MIN_STRING_LENGTH) +".csv"
#        with open(filename, 'wb') as csvfile:
#            csvwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
#            csvwriter.writerow(["subreddit", "feature", "accom_value", "statistic", "pvalue"])
#            for subreddit in self.subreddit_list:
#                for feature in self.FEATURE_LIST:
#                    toPrint = [subreddit, feature] + [x for x in results_dict[subreddit][feature]]
#                    csvwriter.writerow(toPrint)
#        print "RESULTS DICT", results_dict
#        return results_dict
#
#    def test_accom_cohesion_pearson_correlation(self, results_dict, cohesion_results):
#        #copy-pasted in I know
#        #cohesion_dict = {"Agorism":3.53571, "BullMooseParty":3.37736, "christian_ancaps":4.04762, "conservatives":3.93277, "DebateaCommunist":4.27632, "DebateCommunism":3.70792, "democrats":3.65179, "futuristparty":3.90476, "GreenParty":4.81633, "Liberal":4.32143, "LibertarianDebates":3.62857, "LibertarianSocialism":4.08929, "moderatepolitics":3.50000, "monarchism":4.45468, "Objectivism":3.93878, "paleoconservative":3.78571, "PirateParty":4.02679, "SocialDemocracy":4.22050, "socialism":3.91860}
#        #cohesion_dict = {"monarchism" : 5}
#        x = []
#        y = []
#        for subreddit in results_dict:
#            x.append(cohesion_results[subreddit])
#            accom_values = [results_dict[subreddit][i][0] for i in results_dict[subreddit]]
#            y.append(sum(accom_values)/float(len(accom_values)))
#
#        coef = scipy.stats.pearsonr(x, y)
#        return coef


    # Output is a dictionary where key is subreddit, value is a list of lists. The inner list always has two strings.
    def turn_tuples_to_list(self, all_subreddit_comment_tuples):
        just_as_list = {}
        for subreddit in all_subreddit_comment_tuples:
            just_as_list[subreddit] = []
            for pair in all_subreddit_comment_tuples[subreddit]:
                for convo in all_subreddit_comment_tuples[subreddit][pair]:
                    just_as_list[subreddit].append(convo)

        self.turns = just_as_list
    
    def write_cohesion_to_text(self):
        for subreddit in self.turns:
	    print "Working on: ", subreddit
            filepath = self.TURNS_DATA_PATH + "subreddit" + str(self.MIN_STRING_LENGTH) + "_" + subreddit + self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y") + "/"
            if not os.path.exists(filepath):
                os.makedirs(filepath, 0777)
            liwc_cohesion.write_to_txt(self.turns[subreddit], filepath, subreddit)
    
    def get_cohesion_results(self, liwc_path):
        results_dict = {}
        for subreddit in self.subreddit_list:
            
            if self.turns[subreddit] == []:
                print "EMPTY: ", subreddit
                continue

            results_dict[subreddit] = {}

            for feature in self.FEATURE_LIST:
                cohesion_value, first_num, first_den, second_num, second_den = liwc_cohesion.cohesion_value(feature, self.turns[subreddit], liwc_path, subreddit)
                
                # Fisher's exact test:
                a = first_num
                b = first_den - a
                c = second_num
                d = second_den - c
                oddsratio, pvalue = fisher_exact([[a, b], [c, d]])
                
#                print subreddit, feature, cohesion_value
                results_dict[subreddit][feature] = (cohesion_value, oddsratio, pvalue, first_den)

        with open('./HighAssortLarge-cohesion-result-dict.pickle', 'wb') as f:
            pickle.dump(results_dict, f)

        # Writing the resuts to a CSV:
        filename = self.RESULTS_PATH + "COHESION_HighAssortLarge_stats_" + self.daterange[0].strftime("%B%d_%Y")+"_" + self.daterange[1].strftime("%B%d_%Y") + ".csv"
        with open(filename, 'wb') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(["subreddit", "feature", "cohesion_value", "oddsratio", "pvalue", "number_of_turns"])
            for subreddit in self.subreddit_list:

                if self.turns[subreddit] == []:
                    print "EMPTY: ", subreddit
                    continue
                
                for feature in self.FEATURE_LIST:
                    toPrint = [subreddit, feature] + [x for x in results_dict[subreddit][feature]]
                    csvwriter.writerow(toPrint)






# For Hockey:
#subreddit_list = ['CollegeRepublicans', 'EuropeanFederalists', 'Postleftanarchism', 'collapse', 'LateStageCapitalism', 'AnaheimDucks', 'Coyotes', 'BostonBruins', 'sabres', 'CalgaryFlames', 'canes', 'hawks', 'ColoradoAvalanche', 'BlueJackets', 'DallasStars', 'DetroitRedWings', 'EdmontonOilers', 'FloridaPanthers', 'losangeleskings', 'wildhockey', 'Habs', 'Predators', 'devils', 'NewYorkIslanders', 'rangers', 'OttawaSenators', 'Flyers', 'penguins', 'SanJoseSharks', 'stlouisblues', 'TampaBayLightning', 'leafs', 'canucks', 'goldenknights', 'caps', 'winnipegjets']

# For politics:
#subreddit_list = ['Agorism', 'alltheleft', 'Anarchism', 'AnarchistNews', 'AnarchObjectivism', 'Anarcho_Capitalism', 'Anarchy101', 'BullMooseParty', 'centrist', 'christian_ancaps', 'Classical_Liberals', 'communism', 'Conservative', 'conservatives', 'CornbreadLiberals', 'DebateaCommunist', 'DebateCommunism', 'democrats', 'demsocialist','futuristparty', 'Green_Anarchism', 'GreenParty', 'labor', 'leftcommunism', 'leninism', 'Liberal', 'Libertarian', 'LibertarianDebates', 'LibertarianLeft', 'libertarianmeme', 'LibertarianSocialism', 'LibertarianWomen', 'moderatepolitics', 'monarchism', 'neoprogs', 'NeutralPolitics', 'new_right', 'Objectivism', 'paleoconservative', 'peoplesparty', 'PirateParty', 'progressive', 'Republican', 'republicans', 'SocialDemocracy', 'socialism', 'TrueLibertarian', 'Trueobjectivism', 'voluntarism']

# Others:
subreddit_list = ['CrazyIdeas', 'nsfw2', 'place', 'MuseumOfReddit', 'O_Faces', 'KidsAreFuckingStupid', 'SexInFrontOfOthers', 'humor', 'CollegeAmateurs', 'cursedimages', 'gettingherselfoff', 'BonerMaterial', 'montageparodies', 'suicidegirls', 'compsci', 'Nicegirls', 'SpecArt', 'goddesses', 'gif', 'tippytaps'] #, 'legaladvice', 'buildapc', 'SketchDaily', 'photography', 'gonewildcurvy', 'nflstreams', 'apolloapp', 'soccerstreams', 'shortscarystories', 'de_IAmA', 'gonewildcolor', 'headphones', 'GoneWildTube', 'AsiansGoneWild', 'GoneWildSmiles', 'astrophotography', 'Gonewild18', 'NSFW411', 'GWNerdy', 'baconreader', 'altgonewild', 'userbattles', 'anachronism', 'GapingGuys', 'instrumentalmusic', 'bikepaths', 'forex_trades', 'behavior', 'dapps', 'Animism', 'MusicProducerSpot', 'tshirtdesigns', 'Latina_best', 'hotwifeUK', 'AngelinaValentine', 'Mushroom_Cultivation', 'work_in_progress', 'historyincolor', 'java101', 'relationship_guidance', 'MAABMakeup', 'dribbble', 'crackpack', 'musicanova', 'Vivian_Rose', 'carsatan', 'SpaceXNow', 'FMExposed', 'SexySubs', 'TheSexualDragon', 'HistoryQuotes', 'GayBeards', 'TheLustFrontier', 'SadDads', 'BubblesGW', 'ElectionPolls', 'paradigmchange', 'barelyinteresting', 'Shhhnsfw24', 'jm_delphi', 'BustyKhaleesi', 'SosAndTheTiny', 'Emma_Mason', 'europeannationalism', 'NationalSocialism', 'WeissSturm', 'Physical_Removal', 'DebateAltRight', 'WhiteRights', 'The_Donald', 'uncensorednews', 'sjwhate', 'incels', 'KotakuInAction', 'TumblrInAction', 'PussyPassDenied', 'CringeAnarchy', 'conspiracy', 'TheRedPill', 'Drama', 'watchpeopledie', 'MGTOW', 'aznidentity', 'ShitPoliticsSays', 'Coontown', 'fatpeoplehate', 'TheGirlSurvivalGuide', 'ForeverAlone', 'ChangeMyView', 'TwoXChromosomes', 'depression', 'Anxiety', 'CasualConversation', 'RandomKindness', 'fountainpens', 'knitting', 'Buddhism', 'ABraThatFits', 'loseit', 'history']
date1 = datetime.datetime(2016, 4, 30)
date2 = datetime.datetime(2017, 4, 30)
daterange = (date1, date2)
maximum_number_of_comment_pairs = 1200
feature_list = ['pronoun', 'ppron', 'i', 'we', 'you', 'shehe', 'they', 'ipron', 'article', 'prep', 'conj', 'negate',
                'quant', 'discrep', 'tentat', 'certain', 'differ', 'Dic']

base_path = '/home/sbagga1/Reddit-Accommodation/'

# FOR COHESION:
remove_deleted_users = False
dp = DataProcessor(subreddit_list, (date1, date2), base_path, feature_list, maximum_number_of_comment_pairs)

# PRE-LIWC:
tuples = dp.create_tuples(keep_deleted_users)
dp.turn_tuples_to_list(tuples)
dp.write_cohesion_to_text()

# POST-LIWC:
#liwc_results_file = '../POLITICS_LIWC_TURNS_22302_files.txt'
#liwc_results_file = '../HockeyCohesion-Results-11066files.txt'
#liwc_results_file = '../Results_ALL_LIWC_TURNS_2026files.txt'
#tuples = dp.create_tuples()
#dp.turn_tuples_to_list(tuples)
#dp.get_cohesion_results(liwc_results_file)
