import accommodation
import pickle
import pymongo
import os
import datetime
from pymongo import MongoClient
from collections import Counter
import scipy
from scipy.stats import ttest_rel, fisher_exact
import csv
import string
import re
import praw
#create a new dataprocessor object everytime you want to work with new subreddits and dates

class DataProcessor:

    def __init__(self, subreddit_list, daterange, base_path, feature_list, maximum_number_of_comment_pairs, length_restriction=False, minimum_convo_length=5, minimum_length=0):
    	self.redd = praw.Reddit(client_id='15-pbNIEH5XoUw',
                    		client_secret = 'AogNLQuvOYW5anWIfcG63CzW4_4',
                    		username='sbagga',
                    		password='forresearchpurposesonly',
                    		user_agent='sbagga research')
        self.daterange = daterange
        self.subreddit_list = subreddit_list
        self.client = MongoClient(serverSelectionTimeoutMS=45, connectTimeoutMS=20000)
        self.db = self.client.reddit
        self.comments = self.db.comms
        self.BASE_PATH = base_path
        self.DATA_PATH = self.BASE_PATH + "/data/"
        self.RESULTS_PATH = self.BASE_PATH + "/results/"
        self.FOR_LIWC_INPUT_PATH = self.BASE_PATH + "/nice_part2_for_liwc_input/"
        self.FEATURE_LIST = feature_list
        self.turns = {}
        self.MAX_PAIRS = maximum_number_of_comment_pairs
        self.MIN_CONVO_LENGTH = minimum_convo_length
        self.LENGTH_RESTRICTION = length_restriction
        self.MIN_STRING_LENGTH = minimum_length
#        self.TURNS_DATA_PATH = self.BASE_PATH + "/Assort_LIWC_TURNS/"
        self.pair_conv_str = self.daterange[0].strftime("%B%d_%Y")+"_"+ self.daterange[1].strftime("%B%d_%Y") + "_" + str(self.MAX_PAIRS) + "_" + str(self.MIN_CONVO_LENGTH) + "_" + str(self.MIN_STRING_LENGTH) + "_"

    def get_subreddit_data(self, subreddit):
        start = self.daterange[0]
        end = self.daterange[1]

        all_data_file_path = self.DATA_PATH + subreddit + "_" + self.daterange[0].strftime("%B%d_%Y")+"_" + self.daterange[1].strftime("%B%d_%Y") + ".pickle"
        print all_data_file_path
        if os.path.exists(all_data_file_path):
            print "Yay, we have it: ", subreddit
            indexed_subreddit_data = pickle.load(open(all_data_file_path, "rb"))
            print len(indexed_subreddit_data)

        else:
            print "Didn't already have it :("
            cursor = self.comments.find({"subreddit":subreddit, 'created_time':{'$gte':start, '$lt':end}}, {"created_time":1, "body":1, "parent_id":1, "link_id":1, "author":1, "score":1}, no_cursor_timeo$
#           print cursor
            subreddit_data = list(cursor)
#           print subreddit_data
            cursor.close()
            print "\nSubreddit: ", subreddit
            print "Total number of comments: ", len(subreddit_data)
            indexed_subreddit_data = dict()
            for comment in subreddit_data:
                indexed_subreddit_data[comment["_id"]] = comment

            pickle.dump(indexed_subreddit_data, open(all_data_file_path, "wb"))

        return indexed_subreddit_data        #returns list of tuples, with restrictions



    '''
            The output is a dictionary. Key is the subreddit-name; Value is a dictionary itself.
            That inner dictionary's Key is a ('user1', 'user2') tuple; Value is a list lists (basically a list of threads in that subreddit.) The inner list always has two elements/strings in it.
    '''
    def create_tuples(self, remove_deleted_users=True):
        all_basic_subreddit_comment_tuples = {}


        for subreddit in self.subreddit_list:

            all_basic_subreddit_comment_tuples[subreddit] = {}

            total_so_far = 0
            print "\n\n\n\nFOR: ", subreddit
            indexed_subreddit_data = self.get_subreddit_data(subreddit)
            #print indexed_subreddit_data
            print "Total number of comments extracted from MongoDB: ", len(indexed_subreddit_data)
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

#           print comment_tuples
            for interac in comment_tuples:
                if len(comment_tuples[interac]) >= self.MIN_CONVO_LENGTH:
                    all_basic_subreddit_comment_tuples[subreddit][interac] = comment_tuples[interac]
                else:
                    pass
#                   print comment_tuples[interac]
            print "For ", subreddit
            print "User-pairs left: ", len(all_basic_subreddit_comment_tuples[subreddit])
            counter = 0
            for val in all_basic_subreddit_comment_tuples[subreddit].values():
                counter += len(val)
                for k in val:
                    if len(k) != 2:
                        print "What's up here: ", val
#           print all_basic_subreddit_comment_tuples[subreddit]
            print "Total comments left: ", counter*2
        return all_basic_subreddit_comment_tuples


    def create_txt_files(self):
        all_basic_subreddit_comment_tuples = self.create_tuples()
        for subreddit in self.subreddit_list:
            print "Working on: ", subreddit
            if not os.path.exists(self.FOR_LIWC_INPUT_PATH+self.pair_conv_str):
                os.makedirs(self.FOR_LIWC_INPUT_PATH+self.pair_conv_str, 0777)

            accommodation.write_to_txt(all_basic_subreddit_comment_tuples[subreddit], self.FOR_LIWC_INPUT_PATH, self.pair_conv_str, subreddit)


    # Tests hypothesis A: Accommodation correlation with user-karma
    def hypothesis_A(self, sub_feat, tuples, liwc_results_file):
        results_dict = {}

        for (subreddit, feature) in sub_feat:
            print "Working on: ", subreddit

            liwc_path = liwc_results_file

            print "Running feature: ", feature

            acc_dict, acc_terms, total_userpairs, skipped = accommodation.accommodation_dict(tuples[subreddit], feature, liwc_path, subreddit, self.pair_conv_str)
#            print feature, acc_dict
            if acc_dict is None:
                continue

            results_dict[(subreddit, feature)] = self.hypoth_A_helper(acc_dict)

        # Write to CSV:
        for (key, value) in results_dict.items():
            subreddit = key[0]
            feature = key[1]

            filename = self.RESULTS_PATH + "/hypothA/" + subreddit + "_" + feature + "_" + self.daterange[0].strftime("%B%d_%Y")+"_" + self.daterange[1].strftime("%B%d_%Y") + ".csv"
            with open(filename, 'wb') as f:
                f.write("Avg accom,Karma\n")
                for (accom, karma) in value:
                    f.write(str(accom) + "," + str(karma) + "\n")


    # Returns a list of (avg_accomm, karma) tuples
    def hypoth_A_helper(self, acc_dict):

        accomm_karma = []

        user_pairs = acc_dict.keys()
        commenters = list(set(zip(*user_pairs)[0]))
        repliers = list(set(zip(*user_pairs)[1]))

        print "Unique commenters: ", len(commenters)
        print "Unique repliers: ", len(repliers)

        # Get comment karma:

        for username in commenters:

            try:
                user = self.redd.redditor(username)
                karma = user.comment_karma
#               print username, karma

            except:
                print "\n\nDeleted maybe: ", username
                print "Moving on to the next commenter."
                continue

            temp_score = 0.0
            count = 0

            for (userpair, accom) in acc_dict.items():
                if userpair[0] != username:
                    continue

                count += 1
                temp_score += accom

            avg_accom = temp_score / count

            accomm_karma.append((avg_accom, karma))

        return accomm_karma



if __name__ == '__main__':
    date1 = datetime.datetime(2016, 10, 30)
    date2 = datetime.datetime(2017, 10, 30)
    daterange = (date1, date2)
    print "\n\n", daterange
    maximum_number_of_comment_pairs = 12000000000
    base_path = '/home/sbagga1/Reddit-Accommodation/Accomm-Post16Sept'
    remove_deleted_users = True # False means that we DON'T want to remove deleted users.

    # Hate second set (pussy): Currently running
    subreddit_list = ['PussyPass']
    sub_feat = [('PussyPass', 'pronoun'), ('PussyPass', 'ppron'), ('PussyPass', 'prep')]
    feature_list = ['BLAH']

    dp = DataProcessor(subreddit_list, (date1, date2), base_path, feature_list, maximum_number_of_comment_pairs)

    # PRE-LIWC:
    #dp.create_txt_files()

    # POST-LIWC:
    liwc_results_file = '../hate_pus_output8008.txt'
    tuples = dp.create_tuples()
    dp.hypothesis_A(sub_feat, tuples, liwc_results_file)


# Nice part 1: DONE!
#subreddit_list = ['fountainpens', 'loseit', 'Anxiety', 'knitting', 'ABraThatFits']
#sub_feat = [('fountainpens', 'article'), ('fountainpens', 'conj'), ('Anxiety', 'ppron'), ('knitting', 'pronoun'), ('knitting', 'ppron'), ('knitting', 'article'), ('knitting', 'prep'), ('ABraThatFits', 'ppron'), ('ABraThatFits', 'article'), ('ABraThatFits', 'conj'), ('ABraThatFits', 'discrep'), ('loseit', 'pronoun'), ('loseit', 'ppron'), ('loseit', 'prep'), ('loseit', 'discrep'), ('loseit', 'Dic')]

# Nice 'try': DONE!
#subreddit_list = ['ForeverAlone', 'TheGirlSurvivalGuide']
#sub_feat = [('TheGirlSurvivalGuide', 'they'), ('ForeverAlone', 'pronoun'), ('ForeverAlone', 'article'), ('ForeverAlone', 'prep')]

# Nice part 2: Currently running on screen 22674
#subreddit_list = ['Buddhism', 'CasualConversation', 'depression', 'TwoXChromosomes', 'history']
#sub_feat = [('Buddhism', 'pronoun'), ('Buddhism', 'ppron'), ('Buddhism', 'ipron'), ('Buddhism', 'article'), ('Buddhism', 'prep'), ('Buddhism', 'conj'), ('Buddhism', 'tentat'), ('Buddhism', 'certain'), ('Buddhism', 'differ'), ('TwoXChromosomes', 'pronoun'), ('TwoXChromosomes', 'ipron'), ('TwoXChromosomes', 'article'), ('TwoXChromosomes', 'prep'), ('TwoXChromosomes', 'Dic'), ('CasualConversation', 'ppron'), ('CasualConversation', 'you'), ('CasualConversation', 'ipron'), ('CasualConversation', 'Dic'), ('depression', 'pronoun'), ('depression', 'ppron'), ('depression', 'prep'), ('depression', 'differ'), ('depression', 'Dic'), ('history', 'pronoun'), ('history', 'ipron'), ('history', 'article'), ('history', 'prep'), ('history', 'conj'), ('history', 'Dic')]

# Hate initial: DONE!
#subreddit_list = ['sjwhate', 'europeannationalism', 'DebateAltRight', 'uncensorednews', 'NationalSocialism', 'WhiteRights']
#sub_feat = [('sjwhate', 'ppron'), ('sjwhate', 'article'), ('sjwhate', 'prep'), ('sjwhate', 'conj'), ('europeannationalism', 'prep'), ('DebateAltRight', 'pronoun'), ('DebateAltRight', 'i'), ('DebateAltRight', 'you'), ('DebateAltRight', 'ipron'), ('DebateAltRight', 'article'), ('DebateAltRight', 'prep'), ('DebateAltRight', 'conj'), ('DebateAltRight', 'quant'), ('DebateAltRight', 'tentat'), ('DebateAltRight', 'differ'), ('uncensorednews', 'ppron'), ('uncensorednews', 'you'), ('uncensorednews', 'differ'), ('NationalSocialism', 'tentat'), ('WhiteRights', 'conj'), ('WhiteRights', 'quant')]

# Donald: DONE!
#subreddit_list = ['The_Donald']
#sub_feat = [('The_Donald', 'we'), ('The_Donald', 'differ'), ('The_Donald', 'Dic')]

# Hate second set (only MensRights because DankMemes has no p<0.05): Currently running
#subreddit_list = ['MensRights']
#sub_feat = [('MensRights', 'pronoun'), ('MensRights', 'ppron'), ('MensRights', 'i'), ('MensRights', 'you'), ('MensRights', 'ipron'), ('MensRights', 'prep'), ('MensRights', 'conj'), ('MensRights', 'discrep'), ('MensRights', 'tentat'), ('MensRights', 'certain'), ('MensRights', 'differ'), ('MensRights', 'Dic')]

# PRE-LIWC:
#dp.create_txt_files()

# POST-LIWC:
#liwc_results_file = '../tryoutput-38908.txt'
#liwc_results_file = '../donald_output106418.txt'
#liwc_results_file = '../filter_3_donald_output335786.txt'
#liwc_results_file = '../filter_3_tryoutput73576.txt'
#liwc_results_file = '../hate_initial_output114588.txt'
#liwc_results_file = '../nice_part1_output94182.txt'
#liwc_results_file = '../nice_part2_output351272.txt'
#liwc_results_file = '../hate_secondset_bigoutput25006.txt'
