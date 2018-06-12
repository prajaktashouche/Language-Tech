


from Triples import *
from Specs import *
from TextNormalizer import *
from NLP import *
from test_nounify import *
from word2number import w2n
import re
from nltk.stem import WordNetLemmatizer
from IDfinder import *
import requests
import spacy
nlp = spacy.load('en_core_web_sm')

class QuestionParser:
    ###takes a string and creates a sparql query

    def __init__(self, question, specs):
        self.url = 'https://query.wikidata.org//sparql'
        self.lemmatizer = WordNetLemmatizer()
        self.specs = specs                   ##patterns, keywords, anything important could will be added here
        self.question = question  ##question string
        self.nlp = NLP(self.question, self.specs)
        self.possible_words = self.parse_spacy()  ##dictionary that stores possible words in a triple by type (Object, Property, Result)
        self.possible_words_backup = self.possible_words       ##we store the list in a backup list: when we create triples, the ones where no ID can be found are popped from the original (for efficiency), but in case we want to find synonims, we reset the word list from the backup
        self.elements = self.getElements()
        self.sort = None
        self.type = self.determineQuestionType()            ##true_false, count or list (single answer is just a list with 1 element)
        self.variable = ''                                  ##the variable names that will be in the SELECT command
        self.targetVariable = ''                            ##the variable which will be printed in the end
        self.qWord = self.getQuestionWord()

        self.question_SQL = ''                              ##the Sparql query will be stored here (as string)
        self.possible_triples = self.tripleCombinations()   ##the possible query triples are here

        print("possible triples :")
        print(self.possible_triples)
        ##print(self.possible_triples)
        self.query_list = []                                ##the query statements (triples) are listed here

        ##self.parse_spacy()

    def determineQuestionType(self):

        #check if true/false question, and check if superlative or comparative::

        if self.nlp.tokens[0].text.lower() in self.specs.true_false_list['starters']:
            return 'true_false'
        prevText = ""
        for word in self.nlp.tokens:
            text = word.text.lower()            #converting to lowercase as the keywords in the specs are lowercase
            if text in self.specs.true_false_list['somewhereInText']:
                return 'true_false'
            if text in self.specs.count_list['singles'] or ( prevText + " " + text) in self.specs.count_list['doubles']:
                return 'count'
            if word.tag_ == 'JJS' and word.dep_!= 'amod':
                self.getSortID()
                return "superlative"
            if word.tag_ == 'JJR':
                if self.isListComparative():
                    return 'comparative_list'
                else:
                    return 'comparative_objects'
            prevText = text


        #check if count type:
            #TODO

        #rest is list type:
        return "list"

    def isListComparative(self):            ##in case a comparative adjective is found, determines if it compares objects (what is bigger, France or Germany), or wants us to list things (What is bigger than France)
        ##property should be found in the common list
        for word in self.nlp.tokens:
            if word.text in self.specs.common_IDs:
                self.possible_words['Property'] = [word.text]       ##if properrty found, we know that it is the property of interest, we can delete others
                break
        ##check if there are two objects, that are the instance of the same thing, e.g. Germany and France instance of country
        for i in range(0,len(self.possible_words["Object"])):
            for j in range(i + 1,len(self.possible_words["Object"])):
                try:
                    #print("starting try block for comparative instances")
                    #print("words are")
                    #print(self.possible_words["Object"][i])
                    #print(self.possible_words["Object"][j])

                    data1 = requests.get(self.url, params = {'query':self.constructQuery(self.queryStatementFromTriple(self.getTripleFromWordsAndFormat([self.possible_words["Object"][i], "instance of", ""], self.specs.basic_question_formats["Result"]))), 'format': 'json'}).json()
                    data2 = requests.get(self.url, params = {'query':self.constructQuery(self.queryStatementFromTriple(self.getTripleFromWordsAndFormat([self.possible_words["Object"][j], "instance of", ""], self.specs.basic_question_formats["Result"]))), 'format': 'json'}).json()
                    #print("both queries succeeded")
                    for answer1 in data1['results']['bindings']:
                        for answer2 in data2['results']['bindings']:
                            if (answer1[(self.targetVariable)[1:]]['value'] == answer2[(self.targetVariable)[1:]]['value']):
                                print("comparing" + str(answer1) + " and " + str(answer2))
                                self.possible_words['Object'] = [self.possible_words["Object"][i], self.possible_words["Object"][j]]              #if match found, we know that these are the objects of interest, no need for other possible objects
                                self.possible_words['Result'] = []
                                return False
                except:
                    print("an error occured while comparing the words")
                    print(self.possible_words["Object"][i])
                    print(self.possible_words["Object"][j])
                    pass

        return True


    def getSortID(self):
        if self.type == 'superlative':
            for token in self.nlp.tokens:
                if token.tag_ == 'JJS':
                    possible_sort_words = [token.lemma_] + nounify(token.lemma_)
                    for word in possible_sort_words:
                        ID = IDfinder(word, "property", self.specs).findIdentifier()
                        if ID != '':
                            print("ID found for word " + word + ", ID is " + str(ID))
                            return ID
        return None

    def getQuestionWord(self):
        for word in self.nlp.tokens:
            if word.text in list(self.specs.question_words.keys()):
                return word.text

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
        for key, val in self.specs.deps.items():
            for dep in val:
                ##print(dep)
                a = (self.nlp.returnDep(dep))
                if a != None:
                    possible_words[key]+= a
            #print ("the " + key + "s of this sentence are ")
            #print(possible_words[key])
        return possible_words

    def extended_parse_spacy(self):                 ### the words with deps in the extended list are not added to the possible words, just their nounified versions
        for key, val in self.specs.extended_deps.items():
            for dep in val:
                ##print(dep)
                a = (self.nlp.returnDep(dep))
                if a != None:
                    print("extending with dep " + str(dep) + ", list is " + str(a))
                    for word in a:
                        print("trying the word" + word)
                        self.possible_words[key] += nounify(word)
        self.getElements()
        self.possible_triples = self.tripleCombinations()
                    # print ("the " + key + "s of this sentence are ")
                    # print(possible_words[key])

    def getNumberOfAnswers(self):
        for token in self.nlp.tokens:
            if token.tag_ == "CD":
                #print("found token " + token.text + " as number")
                try:
                    return w2n.word_to_num(token.text)
                except:
                    return 0
        return 0

    def addInstance(self):
        self.possible_words["Property"] = self.possible_words["Property"] + (self.specs.question_words["instance"])

    def addNounSynonims(self):
        self.possible_words = self.possible_words_backup
        for key, wordList in self.possible_words.items():
            for word in list(wordList):
                print("word is ")
                print(word)
                if isinstance(word, str):
                    self.possible_words[key] += nounify(word)
            print("key is " + str(key) + " extended list is ")
            print(wordList)

        self.getElements()

        self.possible_triples = self.tripleCombinations()
        return

    def induceWordsFromQuestionWord(self):
	    if self.qWord != None:                      #fixed
        	self.possible_words["Property"] = self.possible_words["Property"] + (self.specs.question_words[self.qWord])
        	self.possible_triples = self.tripleCombinations()

    def generateCombinations(self, a, aIndex, b, bIndex, ret):          ##recursively generates each pair given two lists
        ret.append([a[aIndex], b[bIndex]])
        if aIndex<len(a)-1:
            self.generateCombinations(a, aIndex+1, b, bIndex, ret)
        if bIndex<len(b)-1:
            self.generateCombinations(a, aIndex, b, bIndex +1, ret)
        return ret


    def tripleCombinations(self):      ##this returns a triple with one position being "", placeholder for the variable
        print("construction triples with input")

        print(self.possible_words)
        print("elements are")
        print(str(self.elements))
        wrapperTriple = Triple([], [], self.specs)
        possible_triples = {"Result":[],            ##first one is result, as the queries are constructed in this order, and most questions target the result
                            "Object":[],
                            "Property":[]}
        a = self.elements["Object"]
        b = self.elements["Property"]
        if a and b:
            combinations = self.generateCombinations(a,0,b ,0, [])
            for combination in combinations:
                if combination[0].word != combination[1].word:        ##same word should not appear in 2 positions
                    newTriple = Triple([combination[0],  combination[1], Element('', True, wrapperTriple)], [], self.specs)
                    possible_triples["Result"].append(newTriple)


        a = self.elements["Object"]
        b = self.elements["Result"]
        if a and b:
            combinations = self.generateCombinations(a, 0, b, 0, [])
            for combination in combinations:
                if combination[0].word != combination[1].word:  ##same word should not appear in 2 positions
                    newTriple = Triple([combination[0], Element('', True, wrapperTriple) ,combination[1]], [], self.specs)
                    possible_triples["Property"].append(newTriple)

        a = self.elements["Property"]
        b = self.elements["Result"]
        if a and b:
            combinations = self.generateCombinations(a, 0, b, 0, [])
            for combination in combinations:
                if combination[0].word != combination[1].word:  ##same word should not appear in 2 positions
                    newTriple = Triple([Element('', True, wrapperTriple),combination[0], combination[1] ], [],self.specs)
                    possible_triples["Object"].append(newTriple)
        return possible_triples

    def getElements(self):
        elements = {"Object":[],
                    "Property":[],
                    "Result":[]}
        wrapperTriple = Triple([],[],self.specs)
        for key, listCopy in self.possible_words.items():
            for word in list(listCopy):
                if word[0].islower():
                    word = self.lemmatizer.lemmatize(word)
                print("getting elements, word is " + word + " type is " + str(key).lower())
                if str(key) == 'Object':
                    newElement = Object(word, False, wrapperTriple)
                elif str(key) == 'Property':
                    newElement = Property(word, False, wrapperTriple)
                else:
                    newElement = Result(word, False, wrapperTriple)
                #ID = IDfinder(word, str(key).lower(), self.specs).findIdentifier()
                if newElement.SQL.split(":")[1] == '':
                    print("!!!!!!!!.................................................popped " + word)
                    self.possible_words[key].pop(self.possible_words[key].index(word))
                else:
                    elements[key] += [newElement]
        return elements

    def isValidTriple(self, triple, combinations):

        #checks if an ID is found for the elements in the triple, if not, all triples are removed from the possible triple list with the word without ID
        ##not in use anymore, left here in case we need it

        # print("Object is " + triple.object.word + " is variable = " + str(triple.object.isVariable) + " found id is " + str(triple.object.SQL))
        # print("Property is " + triple.property.word + " is variable = " + str(
        #     triple.property.isVariable) + " found id is " + str(triple.property.SQL))
        # print("Result is " + triple.result.word + " is variable = " + str(
        #     triple.result.isVariable) + " found id is " + str(triple.result.SQL))
        if not triple.object.isVariable and triple.object.SQL == 'wd:':
            print("####################  invlid object triple ######################")
            try:
                self.possible_words["Object"].pop(self.possible_words["Object"].index(triple.object.word))      ##if the ID is not found for a word, we pop it from the list
            except:
                print("already removed from possible word list :" + triple.object.word )
            self.removeFromCombinations(combinations, triple.object.word)

            return False
        if not triple.property.isVariable and triple.property.SQL == 'wdt:':
            print("####################  invlid property triple ######################")
            try:
                self.possible_words["Property"].pop(self.possible_words["Property"].index(triple.property.word))      ##if the ID is not found for a word, we pop it from the list
            except:
                print("already removed from possible word list :" + triple.property.word )

            self.removeFromCombinations(combinations, triple.property.word)

            return False
        if not triple.result.isVariable and triple.result.SQL == 'wd:':
            print("####################  invlid result triple ######################")
            try:
                self.possible_words["Result"].pop(self.possible_words["Result"].index(triple.result.word))      ##if the ID is not found for a word, we pop it from the list
            except:
                print("already removed from possible word list :" + triple.result.word )

            self.removeFromCombinations(combinations, triple.result.word)

            return False
        return True

    def removeFromCombinations(self, combinations, word):
        for comb in combinations:
            if word in comb:
                print("removing comb " + str(comb) + " because of word " + str(word))
                try:
                    combinations.pop(combinations.index(comb))
                except:
                    print("word " + word + " already removed")

    def queryBodyFromList(self, list):
        ret = ""
        for sentence in list:
            ret = ret + sentence + "\n"

        return ret

    def queryStatementFromTriple(self, triple):
        #print("triple query statement is ")
        #print(triple.SQL)
        return triple.SQL

    def getTripleFromWordsAndFormat(self, words, format):
        T = Triple(words, format, self.specs)
        self.getVariableNames(T)
        return T

    def getVariableNames(self, triple):
        print("Passing variable names, var is " + triple.variable + "targetvar is " + triple.targetVariable)
        self.variable = triple.variable
        self.targetVariable = triple.targetVariable

    def constructQuery(self, queryBody):
        #print("constructing query with " + queryBody)
        self.question_SQL = "SELECT " + self.variable + """ WHERE {
        """
        self.question_SQL = self.question_SQL + queryBody
        self.question_SQL = self.question_SQL + """
        SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en" .                        
        }
}
        """                                                             ##last part: gets labels for wikidata IDs
        #print("checking for sort")
        if self.sort != None:
            self.question_SQL += "\nORDER BY DESC(?sort)"
        print(self.question_SQL)
        return self.question_SQL
