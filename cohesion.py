__author__ = 'Sunyam'

from nltk import pos_tag
from nltk.tokenize import word_tokenize
import random


'''
Input:
    C: stylistic dimension
    turns: list of tuples where each tuple is a reply-pair
    
Output:
    Cohesion value
'''
def cohesion_value(C, turns):
    total_number_of_turns = len(turns)
    
    turns_with_C = 0.0
    for (s1, s2) in turns:
        s1_tags = pos_tag(word_tokenize(s1))
        tags1 = list(zip(*s1_tags)[1])
        s2_tags = pos_tag(word_tokenize(s2))
        tags2 = list(zip(*s2_tags)[1])
        if C in tags1 and C in tags2:
            turns_with_C += 1
    
    first_prob = turns_with_C / total_number_of_turns
#     print "First Prob: ", first_prob
    
    # For second_prob, creating fake turns by changing tuples.
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
    
#     print "Real turns: ", turns
#     print "Fake turns: ", fake_turns

    faketurns_withC = 0.0
    for (s1, s2) in fake_turns:
        s1_tags = pos_tag(word_tokenize(s1))
        tags1 = list(zip(*s1_tags)[1])
        s2_tags = pos_tag(word_tokenize(s2))
        tags2 = list(zip(*s2_tags)[1])
        if C in tags1 and C in tags2:
            faketurns_withC += 1
            
    second_prob = faketurns_withC / total_number_of_turns
#     print "Second Prob: ", second_prob
    
    cohesion = first_prob - second_prob
    return cohesion
    

# EXAMPLE:
turns = [('a hey','an hi'), ('the good?', 'yeah I think'), ('the won', 'yes')]
print cohesion_value('DT', turns)
