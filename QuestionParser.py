from Triples import *
from Specs import *
from TextNormalizer import *
from NLP import *
import re
class QuestionParser:
    ###takes a string and creates a sparql query

    def __init__(self, question, specs):
        self.specs = specs                   ##patterns, keywords, anything important could will be added here
        self.type = 'list'                                  ##for now we do not expect any other type
        self.variable = ''                                  ##the variable names that will be in the SELECT command
        self.targetVariable = ''                            ##the variable which will be printed in the end
        self.question = question                            ##question string
        self.possible_words = self.parse_spacy()            ##dictionary that stores possible words in a triple by type (Object, Property, Result)
        self.question_SQL = ''                              ##the Sparql query will be stored here (as string)
        self.possible_triples = self.tripleCombinations()   ##the possible query triples are here
        print("possible triples :")
        print(self.possible_triples)
        ##print(self.possible_triples)
        self.query_list = []                                ##the query statements (triples) are listed here
        ##self.parse_spacy()

    def parse_regex(self):
        for key in self.specs.patterns['triples']:              ##specs is a dict with regex pattern as key, and order of arguments as value
            #print(key)
            matchObj = re.search(key, self.question, re.M|re.I|re.U)
            if matchObj:
                #print("expression found")
                triple = [TextNormalizer(matchObj.group(1)).allowedTagKeeper('noun_adjective'), TextNormalizer(matchObj.group(2)).allowedTagKeeper('noun_adjective') , ""]          ##instead of complicated regex, i remove everything from a group that is not a noun, we know that only those are meaningful in wikidata IDs
                                                                                                                                                                ##an empty element is added in the end as a placeholder for the variable, that is obviously not in the text, for the sake of similar indexing with the order in specs
                #print(triple)
                T = Triple(triple, self.specs.patterns['triples'][key])
                self.variable = T.variable          ##set the question variables to be equal to the triple variables TODO: selection in multiple triples
                self.targetVariable = T.targetVariable
                self.query_list.append(T.SQL)

    def parse_spacy(self):
        possible_words = {"Object":[], "Property":[], "Result":[]}
        tripleType = ['Object', 'Property', {'variable': 'Result'}]   ###spacy can return in this structure always, this is important when constructing triples from regex, but kept here for making triple construction general
        nlp = NLP(self.question, self.specs)
        for key, val in self.specs.deps.items():
            for dep in val:
                ##print(dep)
                a = (nlp.returnDep(dep))
                if a != None:
                    possible_words[key].append(a)
            #print ("the " + key + "s of this sentence are ")
            #print(possible_words[key])
        return possible_words

    def generateCombinations(self, a, aIndex, b, bIndex, ret):          ##recursively generates each pair given two lists
        ret.append([a[aIndex], b[bIndex]])
        if aIndex<len(a)-1:
            self.generateCombinations(a, aIndex+1, b, bIndex, ret)
        if bIndex<len(b)-1:
            self.generateCombinations(a, aIndex, b, bIndex +1, ret)
        return ret


    def tripleCombinations(self):      ##this returns a triple with one position being "", placeholder for the variable
        possible_triples = {"Object":[],
                            "Property":[],
                            "Result":[]}
        a = self.possible_words["Object"]
        b = self.possible_words["Property"]
        if a and b:
            for combination in self.generateCombinations(a,0,b ,0, []):
                possible_triples["Result"].append([combination[0], combination[1], ""] )

        a = self.possible_words["Object"]
        b = self.possible_words["Result"]
        if a and b:
            for combination in self.generateCombinations(a, 0, b, 0, []):
                possible_triples["Property"].append([combination[0], "", combination[1]])

        a = self.possible_words["Property"]
        b = self.possible_words["Result"]
        if a and b:
            for combination in self.generateCombinations(a, 0, b, 0, []):
                possible_triples["Object"].append(["",combination[0], combination[1]])
        return possible_triples


    def queryBodyFromList(self, list):
        ret = ""
        for sentence in list:
            ret = ret + sentence + "\n"

        return ret

    def queryStatementFromTriple(self, triple):
        return triple.SQL

    def getTripleFromWordsAndFormat(self, words, format):
        T = Triple(words, format)
        self.variable = T.variable
        self.targetVariable = T.targetVariable
        return T


    def constructQuery(self, queryBody):
        self.question_SQL = "SELECT " + self.variable + """ WHERE {
        """
        self.question_SQL = self.question_SQL + queryBody
        self.question_SQL = self.question_SQL + """
        SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en" .                        
        } 
}
        """                                                             ##last part: gets labels for wikidata IDs
        print(self.question_SQL)
        return self.question_SQL
