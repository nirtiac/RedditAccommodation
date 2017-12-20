__author__ = 'Sunyam'

# Step 1: Write turns to .txt files
# Step 2: Run LIWC manually (once)
# Step 3: Parse the LIWC output to calculate cohesion

import pandas as pd
import random

'''
- Takes in a dictionary like: 
    {('user1', 'user2'): ('conv1', 'conv2', 'faketurnconv1', 'faketurnconv2'),
     ('user3', 'user4'): ('conv3', 'conv4', 'faketurnconv3', 'faketurnconv4')}
- Writes all the real and fake turns to .txt files
'''
def write_to_txt(dict_tuples):
    
    real_turns, fake_turns = convert_input(dict_tuples)
    
    for tup in real_turns:
        conv_index = real_turns.index(tup)
        with open('./try/realtuple_'+str(conv_index)+'_person_1.txt', 'wb') as f1:
            f1.write(tup[0])
        with open('./try/realtuple_'+str(conv_index)+'_person_2.txt', 'wb') as f2:
            f2.write(tup[1])
        
    for tup in fake_turns:
        conv_index = fake_turns.index(tup)
        with open('./try/faketuple_'+str(conv_index)+'_person_1.txt', 'wb') as f1:
            f1.write(tup[0])
        with open('./try/faketuple_'+str(conv_index)+'_person_2.txt', 'wb') as f2:
            f2.write(tup[1])


'''
- Takes in stylistic dimension C, dictionary that has both real and fake tuples (same as input to write_to_txt), and path to LIWC output file.
- Returns Cohesion value.
'''
def cohesion_value(C, dict_tuples, liwc_path):
    
    turns, fake_turns = convert_input(dict_tuples)
    
#     print "Real turns: ", turns
#     print "Fake turns: ", fake_turns
    
    liwc_df = pd.read_csv(liwc_path, delimiter='\t')[['Filename', C]]
#     print liwc_df
    total_rows = liwc_df.shape[0]
#     print "Total number of rows in dataframe: ", total_rows
    # Throw an error if this number is not even:
    if total_rows % 2 != 0:
        print "ERROR. Total number of rows in LIWC dataframe: ", total_rows
        exit(0)
    
    total_number_of_real_turns = len(turns)
    total_number_of_fake_turns = len(fake_turns)
    
    turns_with_C = 0.0
    faketurns_with_C = 0.0
    
    # For first probability:
    for tup in turns:
        conv_index = turns.index(tup)
        temp_df = liwc_df.loc[liwc_df.Filename.str.startswith('realtuple_' + str(conv_index))]
        # Throw an error if there are not 2 rows (because it a reply pair)
        if temp_df.shape[0] != 2:
            print "ERROR. temp_df should have two rows, but this one doesn't: ", temp_df
            exit(0)
            
        c_values = temp_df[C].values
        if 0 not in c_values:
            turns_with_C += 1
            
    first_prob = turns_with_C / total_number_of_real_turns
#     print "\nFirst probability: ", first_prob
    
    # For second probability:
    for tup in fake_turns:
        conv_index = fake_turns.index(tup)
        temp_df = liwc_df.loc[liwc_df.Filename.str.startswith('faketuple_' + str(conv_index))]
        # Throw an error if there are not 2 rows (because it a reply pair)
        if temp_df.shape[0] != 2:
            print "ERROR. temp_df should have two rows, but this one doesn't: ", temp_df
            exit(0)
            
        c_values = temp_df[C].values
        if 0 not in c_values:
            faketurns_with_C += 1    
            
    second_prob = faketurns_with_C / total_number_of_fake_turns
#     print "\nSecond probability: ", second_prob
    
    cohesion = first_prob - second_prob
    return cohesion


'''
Takes in dict_tuples (same as write_to_txt)
Returns a list of real tuples and a list of fake tuples
'''
def convert_input(dict_tuples):
    real_tuples = []
    fake_tuples = []
    for user_pair, value in dict_tuples.items():
        real_tuples.append(value[0:2])
        fake_tuples.append(value[2:4])
    return real_tuples, fake_tuples
    
    
# EXAMPLE RUN:
# mydict = {('user1', 'user2'): ('hi there, i am user1', 'hello i am user2', 'i am user3 now', 'india canada'),
#       ('user3', 'user4'): ('tax laws suck', 'yes they do', 'we can do this', 'i love ice cream')}
# write_to_txt(mydict)
# cohesion_value('pronoun', mydict, '/Users/sunyambagga/Desktop/new_cohesion_try (8 files)).txt')
