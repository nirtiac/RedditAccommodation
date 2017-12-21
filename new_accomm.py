__author__ = 'Sunyam'

import pandas as pd
import numpy as np

'''
- Takes in a dictionary where key is user-pair-tuples and value is a list of conversations involving them.
- Writes all the turns to .txt files

Format: userID_ConversationIndex_IndexWithinThatConversation.txt
userID is to identify a user.
ConversationIndex is to indentify a thread.
Index is to identify the comment within a thread.
'''
def write_to_txt(dict_input):
    
    conv_index = 0
    for user_pair, conversation in dict_input.items():
        person1 = user_pair[0]
        person2 = user_pair[1]
        for tup in conversation:
            index = conversation.index(tup)
            with open('./new_accom_try/' + str(person1) + '_' + str(conv_index) + '_' + str(index) + '_.txt', 'wb') as f1:
                f1.write(tup[0])
            with open('./new_accom_try/' + str(person2) + '_' + str(conv_index) + '_' + str(index) + '_.txt', 'wb') as f2:
                f2.write(tup[1])
        
        conv_index += 1

'''
- Takes in a dictionary where key is user-pair-tuples and value is a list of conversations involving them; stylistic 
  dimension C; path to liwc output
- Returns a dictionary where key is user-pair-tuples and value is two-tuple (subtracting these two terms will yield the accommodation value).
'''
def accommodation(dict_input, C, liwc_path):
    liwc_df = pd.read_csv(liwc_path, delimiter='\t')[['Filename', C]]
#     print liwc_df
    total_rows = liwc_df.shape[0]
#     print "Total number of rows in dataframe: ", total_rows
    # Throw an error if this number is not even:
#    if total_rows % 2 != 0:
 #       print "ERROR. Total number of rows in LIWC dataframe: ", total_rows

    
    accom = {}
    accom_terms = {}

    conv_index = 0
    for user_pair, conversation in dict_input.items():
#         print "Users: ", user_pair
        
        # Calculating Second Probability: magnitude of C in b's reply / 100*number of replies
        total_number_of_replies = len(conversation)

        if total_number_of_replies < 5:
            continue

        denominator = 100*total_number_of_replies
        
        # Selecting the second user (replier i.e. user_pair[1]) and make sure that it's only the current conversation:
        temp_df_1 = liwc_df.loc[liwc_df.Filename.str.startswith(str(user_pair[1]) + '_' + str(conv_index) + "_")]
        c_values_1 = temp_df_1[C].values
        user2_exhibit_C = np.sum(c_values_1)
        
        second_term = user2_exhibit_C / float(denominator)

        # Calculating First Probability: minimum of magnitude of C in both a's and b's comments / magnitude of C in a's comment
        temp_df_2 = liwc_df.loc[liwc_df.Filename.str.startswith(str(user_pair[0]) + '_' + str(conv_index) + "_")]
        c_values_2 = temp_df_2[C].values
        user1_exhibit_C = np.sum(c_values_2)
                
        df_concat = pd.concat([temp_df_1, temp_df_2])
        both_users_exhibit_C = 0.0
        R = df_concat.shape[0]
        # R is the number of rows in the concatenated dataframe
        for k in range(0, (R/2)):
            temp_concatdf = df_concat.loc[df_concat.Filename.str.endswith('_'+str(k)+'_.txt')]
            # temp_concatdf should be of the shape (2,2):
            if temp_concatdf.shape[0] != 2:
                #print "Error while calculating bothUsersExhibitC."
                continue
                
            # Both users will exhibit C if 0 is not present in both
#             print temp_concatdf[C].tolist()
            if 0.0 not in temp_concatdf[C].tolist():
                m = np.array(temp_concatdf[C].tolist()).min()
                both_users_exhibit_C += m
                
        user1_exhibit_C += 1
        both_users_exhibit_C +=1
        first_term = both_users_exhibit_C / float(user1_exhibit_C)

        accom[user_pair] = first_term - second_term
        accom_terms[user_pair] = (first_term, second_term)
        conv_index += 1
    
    return accom, accom_terms

'''
- Takes in the accommodation dictionary of the above function.
- Returns the accommodation exhibited in the entire dataset.
'''
def dataset_accom(acc_dict):
    temp = []
    for first, second in acc_dict.values():
        temp.append(first-second)
    return np.array(temp).mean()
    
    
# EXAMPLE RUN:
# my = {('user1', 'user2'): [('hi','hello'), ('how are you','good'), ('what else man', 'what do you think')], 
#       ('user3', 'user4'): [('who is the best','we are'), ('you do not say','i will do whatever')],
#       ('user5', 'user2'): [('who is ','you and me'), ('cmon man','yeah let us do this')]}

# # write_to_txt(my)
# import pandas as pd
# liwc_path = '/Users/sunyambagga/Desktop/accom_try (14 files)).txt'

# acc_dict = accommodation_dict(my, 'pronoun', liwc_path)
# print my, "\n"
# print acc_dict, "\n"
# print dataset_accom(acc_dict)
# print pd.read_csv(liwc_path, delimiter='\t')[['Filename', 'pronoun', 'WC']]
