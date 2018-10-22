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
  #accommodation_terms = get_accommodation_terms(LIWC_output_file)
  #accommodation = accommodation(accommodation_terms)
 
  #does this for all 
  stats = get_accommodation_stats(LIWC_output_file)
  
  

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


class Methods:

def accommodation(all_terms):
  calculate accommodation according to formula
  
def cohesion(all_terms):
  calculate cohesion according to formula

-> this could be in either dataprocessor or methods
def get_accommodation_terms():
    does all the funky dataframe processing to get all the correct terms
    
 def get_cohesion_terms():
  does all the funky dataframe processing for cohesion
 
 #this will depend on hypothesis
 def get_accommodation_stats(LIWC_output_file, output_directory):
    calls get_accommodation_terms and accommodation using those terms
    then calls various stats functions like t-test
    writes these stats to file
