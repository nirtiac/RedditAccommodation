# RedditAccomodation

Class Structure
# Class Experiments

base_data_folder = "/wherever"

->let's break this into two functions, pre and post
def hypothesis_x():
  #Pre-LIWC
  subreddit_list = []
  date_range = []
  output_file = base_data_folder + "hypothesis_x"
  LIWC_output = "/x/"
  raw_subreddit_data = get_data_for_subreddits(subreddit_list, date_range)
  tuples = create_tuples_for_subreddits(raw_subreddit_data, x_func)
  write_to_text(tuples, output_file)
  
  #here we run LIWC manually. like good computer science students. 
  
  #Post-LIWC
  LIWC_output = get_LIWC_output(LIWC_output_file)
  #here swtich to calling the calculation hypotheses functions
  
  

# Class DataProcessor
->should get appropriate data from given source (either h-cluster or flatfiles)
->should have (separate) functions to 

get_data_for_subreddits(subreddit_list):
"""
calls get_data for each subreddit, returns as a dictionary of subreddit to data
"""
  get_data

def get_data(subreddit, date_range, fields):
"""
Should smartly fetch and cache
parameters: subreddit_list: list of subreddits
date_range: range of appropriate dates
return the list of comment objects containing, indexed on ID
"""

def create_tuples_for_subreddits(create_tuples_function_x):
"""
accepts a dictionary of subreddits to data, then calls the appropriate create_tuples, with the function passed as a param
"""

-> There will be several of these functions. Will return a key: [list of interactions]
-> Will include parameters such as max_pairs, length_restirction, min_string_length, min_convo_length, ignore_deleted_users
-> Parameter that will govern whether we return a list (for cohesion) or dictionaries (for accommodation)
def create_tuples_x(comment_object_list):
"""
comment_object_list: our data
returns: a dictionary of (tuple):[list of lists]
"""

-> one of several functions
def write_to_text_x(tuples)
""""
writes to a txt file ready for liwc processing. 
returns nothing
""""

def get_LIWC_output(liwcFilePath):
"""
gets the data and returns a dataframe
"""




