__author__ = 'Sunyam'

# Step 1: Write turns to .txt files
# Step 2: Run LIWC manually (once)
# Step 3: Parse the LIWC output to calculate cohesion

import pandas as pd
import random

'''
- Takes in a list of tuples (reply-pairs)
- Writes all the turns to .txt files
'''
def write_to_txt(turns):
    for tup in turns:
        index = turns.index(tup)
        with open('./try/tuple_'+str(index)+'_person_1.txt', 'wb') as f1:
            f1.write(tup[0])
        with open('./try/tuple_'+str(index)+'_person_2.txt', 'wb') as f2:
            f2.write(tup[1])
            
            
'''
- Takes in real turns
- Returns shuffled fake turns
'''
def create_fake_turns(turns):
    temp1 = []
    temp2 = []
    for (p, q) in turns:
        temp1.append(p)
        temp2.append(q)
    
    # Shuffling: Will keep repeating until it gets it right.
    while True:
        temp1_ran = random.sample(temp1, len(temp1))
        temp2_ran = random.sample(temp2, len(temp2))
        fake_turns = zip(temp1_ran, temp2_ran)
        # Checking if any of the tuples are still same:
        p = len(set(turns).intersection(set(fake_turns)))
        if p == 0:
            break
    return fake_turns


'''
- Takes in stylistic dimension C, list of tuples, and path to LIWC output file.
- Returns Cohesion value.
'''
def cohesion_value(C, turns, liwc_path):
    liwc_df = pd.read_csv(liwc_path, delimiter='\t')[['Filename', C]]
    
    total_rows = liwc_df.shape[0]
#     print "Total number of rows in dataframe: ", total_rows
    # Throw an error if this number is not even:
    if total_rows % 2 != 0:
        print "ERROR. Total number of rows in LIWC dataframe: ", total_rows
        exit(0)
    
    total_number_of_turns = total_rows / 2.0
    turns_with_C = 0.0
    
    # List of tuples that I'll pass to create_fake_turns:
    real_turns = []
       
    for tup in turns:
        conv_index = turns.index(tup)
        temp_df = liwc_df.loc[liwc_df.Filename.str.startswith('tuple_' + str(conv_index))]
        # Throw an error if there are not 2 rows (because it a reply pair)
        if temp_df.shape[0] != 2:
            print "ERROR. temp_df should have two rows, but this one doesn't: ", temp_df
            exit(0)
            
        c_values = temp_df[C].values
        if 0 not in c_values:
            turns_with_C += 1    
        # Creating a tuple of filenames (will be used in second_prob)
        real_turns.append(tuple(temp_df['Filename'].values))
    
    first_prob = turns_with_C / total_number_of_turns
#     print "\nFirst probability: ", first_prob
    
    # For second probability: converting df to list of tuples
    fake_turns = create_fake_turns(real_turns)
#     print "\nReal: ", real_turns
#     print "\nFake:", fake_turns
    
    # Need a dictionary to map filenames to C count:
    fn_C_map = dict(zip(liwc_df.Filename, liwc_df.iloc[:,1]))
#     print fn_C_map
    faketurns_withC = 0.0
    for f1, f2 in fake_turns:
        c1 = fn_C_map[f1]
        c2 = fn_C_map[f2]
        if c1 != 0.0 and c2 != 0.0:
            faketurns_withC += 1
            
    second_prob = faketurns_withC / total_number_of_turns
#     print "\nSecond probability: ", second_prob
    
    cohesion = first_prob - second_prob
    return cohesion

    
# EXAMPLE:
# turns = [('a hey','an hi'), ('good?', 'yeah I think'), ('the won', 'a india'), ('the bye', 'see you the the')]
# Step 1: write_to_txt(turns)
# Step 2: run LIWC and save results
# Step 3: cohesion_value('article', turns, path_to_liwc_results)
