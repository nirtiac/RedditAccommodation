__author__ = 'Caitrin'
import DataProcessor
def main():


/home/carmst16/NLP_Final_Project/RedditAccomodation/

feature_list = ['pronoun', 'ppron', 'i', 'we', 'you', 'shehe', 'they', 'ipron', 'article', 'prep', 'conj', 'negate', 'quant', 'discrep', 'tentat', 'certain', 'differ', 'Dic']
    original_umask = os.umask(0)
    date1 = datetime.datetime(2015, 1, 1)
    date2 =datetime.datetime(2016, 12, 30)

            self.FEATURE_LIST = feature_list
        self.MINIMUM_CONVO_LENGTH = minimum_convo_length
        self.LENGTH_RESTRICTION = length_restriction
        self.results_path = self.BASE_PATH + "results"
        self.minimum_length = 10
        self.maximum_number_of_comment_pairs = 1000

    #intitial_subreddit_list  = ["Agorism","alltheleft","Anarchism","AnarchistNews","AnarchObjectivism","Anarcho_Capitalism","Anarchy101","BullMooseParty","centrist","christian_ancaps","Classical_Liberals","communism","Conservative","conservatives","CornbreadLiberals","DebateaCommunist","DebateCommunism","democrats","demsocialist","futuristparty","Green_Anarchism","GreenParty","labor","leftcommunism","leninism","Liberal","Libertarian","LibertarianDebates","LibertarianLeft","libertarianmeme","LibertarianSocialism","LibertarianWomen","moderatepolitics","monarchism","neoprogs","NeutralPolitics","new_right","Objectivism","paleoconservative","peoplesparty","PirateParty","progressive","Republican","republicans","SocialDemocracy","socialism","TrueLibertarian","Trueobjectivism","voluntarism"]
    test_subreddit_list = ["monarchism"]
    final_subreddit_list = ["monarchism", "DebateCommunism", "socialism", "SocialDemocracy", "LibertarianSocialism", "conservatives", "GreenParty", "PirateParty", "democrats", "Objectivism", "moderatepolitics", "christian_ancaps", "futuristparty", "DebateaCommunist", "LibertarianDebates", "paleoconservative",  "BullMooseParty", "Liberal"]
    pared_subreddit_list = ["monarchism", "DebateCommunism", "socialism", "SocialDemocracy", "conservatives", "GreenParty",  "democrats", "Objectivism", "moderatepolitics", "futuristparty", "DebateaCommunist", "LibertarianDebates", "Liberal"]

    dp = DataProcessor(final_subreddit_list, (date1, date2), 100)
    method = "length_restricted"
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
