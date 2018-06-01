

from QuestionParser import *
from QuestionAnswerer import *

import requests
import sys

###The system works as follows:
##reads an input -> finds groups of words of interest (regex) -> removes unimportant word types (POS) -> creates an ordered triple based on the patterns defined in specification -> Gets the ID for the words in the triple -> constructs a query using the IDs -> requests and prints answer for the quesry
##The system is very general, works on every domain, and new patterns can be added with only a definition in the specification, no need to change the code in ant way
##Example: pattern with Y's X is added besides X of Y, works perfectly

##############################################  define specification for the task here ###################################
spec1 = {
    'question_words':['What', 'Who'],
    'basic_question_formats':{"Object":[{'variable':'Object'},'Property', 'Result'],
                        "Property":['Object', {'variable':'Property'}, 'Result'],
                        "Result": ['Object', 'Property', {'variable':'Result'}]},
    'patterns':{'triples':{
                r"(.*) of ([^\\?]+)":['Property', 'Object', {'variable':'Result'}],
                r"(.*)'s ([^\\?]+)":['Object', 'Property', {'variable':'Result'}]
                ###Throughout the code I call the elements of a wikidata triple Object - Property - Result
                ###This dictionary defines what order of these entities corresponds to a pattern (key), so the parser will know how to put the query together
                ##regex stopword removal (kept for potential use later): (?:the|a|an)?\s*
                },
    },
    'deps':{"Object": ["pobj", "poss", "nsubj", "conj"],                 ##we store here the possible deps (returned by spacy) for each element in a triple
            "Property" : ["attr", "nsubj", "acomp", "dobj"],
            "Result": ["pobj"]
            }
}
###the specs are passed to the outer class as an argument, several versions can be defined here separately
##########################################################################################################################
print('Exit by typing Bye')
question = ''
while question != 'Bye':
    question = input("Enter a question:")
    if question != 'Bye':                           ##no do while in python :(
        QuestionAnswerer(QuestionParser(question, Specification(spec1))).getAnswer()
