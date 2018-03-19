__author__ = 'Caitrin'
from DataProcessor import DataProcessor
import datetime
import os

class RunExperiments:

    def __init__(self, subreddit_list):
        self.subreddit_list = subreddit_list
        self.date1 = datetime.datetime(2016, 4, 30)
        self.date2 = datetime.datetime(2017, 4, 30)
        self.base_path = "/home/carmst16/NLP_Final_Project/"
        self.maximum_number_of_comment_pairs = 1200
        self.feature_list = ['pronoun', 'ppron', 'i', 'we', 'you', 'shehe', 'they', 'ipron', 'article', 'prep', 'conj', 'negate', 'quant', 'discrep', 'tentat', 'certain', 'differ', 'Dic']

#No length restriction
    def experimentOnePreLIWC(self):

        dp = DataProcessor(self.subreddit_list, (self.date1, self.date2), self.base_path)
        dp.create_txt_files(self.maximum_number_of_comment_pairs, minimum_convo_length=1)

    #with length restriction
    def experimentTwoPreLIWC(self):


        dp = DataProcessor(self.subreddit_list, (self.date1, self.date2), self.base_path)
        dp.create_txt_files(self.maximum_number_of_comment_pairs, length_restriction=True, minimum_length=10)

    #with no length restriction
    def experimentOnePostLIWC(self, liwc_results_file):

        dp = DataProcessor(self.subreddit_list, (self.date1, self.date2), self.base_path, self.feature_list, self.maximum_number_of_comment_pairs)
        tuples = dp.create_tuples()
        results_by_subreddit = dp.get_accommodation_stats(tuples, liwc_results_file)


    #with length restriction
    def experimentTwoPostLIWC(self):

        dp = DataProcessor(self.subreddit_list, (self.date1, self.date2), self.base_path)
        tuples = dp.create_tuples(self.maximum_number_of_comment_pairs, length_restriction=True, minimum_length=10)
        results_by_subreddit = dp.get_accommodation_stats



def main():

    original_umask = os.umask(0)

    #intitial_subreddit_list  = ["Agorism","alltheleft","Anarchism","AnarchistNews","AnarchObjectivism","Anarcho_Capitalism","Anarchy101","BullMooseParty","centrist","christian_ancaps","Classical_Liberals","communism","Conservative","conservatives","CornbreadLiberals","DebateaCommunist","DebateCommunism","democrats","demsocialist","futuristparty","Green_Anarchism","GreenParty","labor","leftcommunism","leninism","Liberal","Libertarian","LibertarianDebates","LibertarianLeft","libertarianmeme","LibertarianSocialism","LibertarianWomen","moderatepolitics","monarchism","neoprogs","NeutralPolitics","new_right","Objectivism","paleoconservative","peoplesparty","PirateParty","progressive","Republican","republicans","SocialDemocracy","socialism","TrueLibertarian","Trueobjectivism","voluntarism"]
    #final_subreddit_list = ["monarchism", "DebateCommunism", "socialism", "SocialDemocracy", "LibertarianSocialism", "conservatives", "GreenParty", "PirateParty", "democrats", "Objectivism", "moderatepolitics", "christian_ancaps", "futuristparty", "DebateaCommunist", "LibertarianDebates", "paleoconservative",  "BullMooseParty", "Liberal"]

    Runner = RunExperiments([""])
    Runner.experimentOnePostLIWC("/home/carmst16/NLP_Final_Project/cur_test_results.txt")



    ##CAITRIN YOU ARE DEALING WITH THE FACT THAT YOU ARE GETTING ALL ONES

if __name__ == "__main__":
    main()
