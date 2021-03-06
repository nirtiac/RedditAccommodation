__author__ = 'Sunyam'

import pandas as pd
import numpy as np

'''
- Takes in a dictionary where key is user-pair-tuples and value is a list of conversations involving them; and file_path; and name of subreddit.
- Writes all the turns to .txt files

txtFileFormat: subredditName_ConversationIndex_userID_IndexWithinThatConversation_.txt
userID is to identify a user.
ConversationIndex is to indentify a thread.
Index is to identify the comment within a thread.
subredditName is to identify the subreddit.
'''
def write_to_txt(dict_input, file_path_half, pair_conv_str, subreddit_name):

    file_path = file_path_half + pair_conv_str

    conv_index = 0

    for user_pair, conversation in dict_input.items():
        person1 = user_pair[0]
        person2 = user_pair[1]
        #print person1, person2
        if person1 in person2: #lol
            continue
        for tup in conversation:
            index = conversation.index(tup)
            with open(file_path + str(subreddit_name) + '_' + str(conv_index) + '_' + str(person1) + '_' + str(index) + '_.txt', 'wb') as f1:
                f1.write(tup[0])
            with open(file_path + str(subreddit_name) + '_' + str(conv_index) + '_' + str(person2) + '_' + str(index) + '_.txt', 'wb') as f2:
                f2.write(tup[1])

        conv_index += 1

def accommodation_dict(dict_input, C, liwc_path, subreddit_name, pair_conv_str):

    liwc_df = pd.read_csv(liwc_path, delimiter='\t')[['Filename', C]]

    total_rows = liwc_df.shape[0]
#     print "Total number of rows in dataframe: ", total_rows
    # Throw an error if this number is not even:
    #if total_rows % 2 != 0:
        #print "ERROR. Total number of rows in LIWC dataframe: ", total_rows

    accom = {}
    accom_terms = {}
    conv_index = 0

    total_userpairs = len(dict_input.keys())
    skipped = 0

    for user_pair, conversation in dict_input.items():
#         print "Users: ", user_pair

        ## Calculating Second Probability in eq (2) ##
        total_number_of_replies = len(conversation)

        # Check to make sure the denom is not too small
        if total_number_of_replies < 3:
            print "Skipping cuz second-term-denom: ", total_number_of_replies
            continue

        # Selecting the second user (replier i.e. user_pair[1]) and make sure that it's only the current conversation:

        temp_df_1 = liwc_df.loc[liwc_df.Filename.str.startswith(pair_conv_str + str(subreddit_name) + '_' + str(conv_index) + '_' + str(user_pair[1]))]
        c_values_1 = temp_df_1[C].values
        user2_exhibit_C = np.count_nonzero(c_values_1)
        second_term = user2_exhibit_C / float(total_number_of_replies)
#         print replies_with_user2_C
#         print total_number_of_replies
#         print second_term

        ## Calculating First Probability in eq (2) ##
        temp_df_2 = liwc_df.loc[liwc_df.Filename.str.startswith(pair_conv_str + str(subreddit_name) + '_' + str(conv_index) + '_' + str(user_pair[0]))]
        c_values_2 = temp_df_2[C].values
        user1_exhibit_C = np.count_nonzero(c_values_2)

        if user1_exhibit_C == 0:
            skipped += 1
            #print "Skipping cuz first-term-denominator: ", user1_exhibit_C
            continue

        df_user2 = liwc_df.loc[liwc_df.Filename.str.startswith(pair_conv_str + str(subreddit_name) + '_' + str(conv_index) + '_' + str(user_pair[1]))]
        df_user1 = liwc_df.loc[liwc_df.Filename.str.startswith(pair_conv_str + str(subreddit_name) + '_' + str(conv_index) + '_' + str(user_pair[0]))]
        df_concat = pd.concat([df_user2, df_user1])

        both_users_exhibit_C = 0.0
        R = df_concat.shape[0]
        #print "df_concat", df_concat

        for k in range(0, (R/2)):
            temp_concatdf = df_concat.loc[df_concat.Filename.str.endswith('_'+str(k)+'_.txt')]
            # temp_concatdf should be of the shape (2,2):
            #print temp_concatdf
            if temp_concatdf.shape[0] != 2:
                # print "Error while calculating bothUsersExhibitC."
                continue
                #TODO: I changed this from return none to continue

            # Both users will exhibit C if 0 is not present in both
            if 0.0 not in temp_concatdf[C].tolist():
                both_users_exhibit_C += 1

        #TODO: I added this rudimentary smoothing
        #user1_exhibit_C += 1
        #both_users_exhibit_C +=1

        first_term = both_users_exhibit_C / float(user1_exhibit_C)
#        if user1_exhibit_C != 0:
#           first_term = both_users_exhibit_C / float(user1_exhibit_C)

#        else:
#           first_term = 0.0
#         print first_term

        accom[user_pair] = first_term - second_term
        accom_terms[user_pair] = (first_term, second_term)
#         print "\n\n"
        conv_index += 1

    print "Skipped: ", skipped
    return accom, accom_terms, total_userpairs, skipped


'''
- Takes in the accommodation dictionary returned by the above function.
- Returns the accommodation exhibited in the entire dataset.
'''
def dataset_accom(acc_dict):
    return np.array(acc_dict.values()).mean()

'''
- Takes in the accommodation dictionary of the above function
- Returns the first term and second term (page 7 of paper, below Figure 2)
'''
def influence(acc_dict):
    # Dictionary with key = user_pair; value = list of two floats: [Acc(a,b), Acc(b,a)]
    influence_dict = {}

    # Using the fact that sorted will have the user_pair in same order.
    for user_pair, accomm in acc_dict.items():
        SortedUserPair = tuple(sorted(user_pair))

        if SortedUserPair not in influence_dict:
            influence_dict[SortedUserPair] = [accomm]

        elif SortedUserPair in influence_dict:
            influence_dict[SortedUserPair].append(accomm)

    # Calculate first term (mean of max values) and second term (mean of min values):
    first = []
    second = []
    for user_pair, acc_list in influence_dict.items():
        # Checking if both users replied to each other (Eliminating one-way conversations)
        if len(acc_list) == 2:
            first.append(np.array(acc_list).max())
            second.append(np.array(acc_list).min())

    first_term = np.array(first).mean()
    second_term = np.array(second).mean()

    return first_term, second_term


'''
- Takes in the accommodation dictionary returned by accommodation_dict
- Returns a dictionary: key = user_pair; value = influence of user1 on user2
'''
def calculate_influence_dict(acc_dict):
    influence_dict = {}
    for user_pair, accom in acc_dict.items():
        reverse_userpair = tuple(reversed(user_pair))

        if reverse_userpair in acc_dict and user_pair in acc_dict:
            influence_dict[user_pair] = accom - acc_dict[reverse_userpair]
#         acc_dict.pop(user_pair)

    return influence_dict


# EXAMPLE RUN:
# my = {('user1', 'user2'): [('hi','hello'), ('how are you','good'), ('what else man', 'what do you think')],
#      ('user3', 'user4'): [('who is the best','we are'), ('you do not say','i will do whatever')],
#      ('user5', 'user2'): [('who is ','you and me'), ('cmon man','yeah let us do this')]}
# liwc_path = '../../accom_try (14 files)).txt'
# acc_dict = accommodation_dict(my, 'pronoun', liwc_path)
# print acc_dict
# print dataset_accom(acc_dict)
# print influence(acc_dict)
# print calculate_influence_dict(acc_dict)
