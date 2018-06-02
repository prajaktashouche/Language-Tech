import requests
import sys
from termcolor import colored

##this clss takes a questionParser object as an argument. Sends the query as a request and prints the answer


class QuestionAnswerer:
    def __init__(self, question):
        self.url = 'https://query.wikidata.org//sparql'
        self.data = None
        self.question = question
        self.triedAllExtensions = False


    def runRegex(self):
        try:
            self.data = requests.get(self.url, params={'query': self.question.constructQuery(self.question.queryBodyFromList(self.question.query_list)), 'format': 'json'}).json()  ###this line sends the actual request and stores the answer
        except:
            print("could not construct query with question: " + self.question.question)
            self.data = None

    def runNLPwithTripleList(self):
        for key, tripleList in self.question.possible_triples.items():
            for tripleString in list(tripleList):         ##creating a copy, so i can pop from the original
                tripleList.pop(tripleList.index(tripleString))
                try:
                    print("triple is :")
                    print(tripleString)
                    #print(triple.object.word + "-" + triple.property.word + "-"+ triple.result.word)
                    #print("format is ")
                    #print(self.question.specs.basic_question_formats[key])
                    tripleObject = self.question.getTripleFromWordsAndFormat(tripleString, self.question.specs.basic_question_formats[key])
                    if self.question.type == 'superlative':
                        print("reworking for superlative")
                        print("sort id is " + str(self.question.sort))
                        tripleObject.constructSuperlativeSparql(self.question.sort)
                        self.question.getVariableNames(tripleObject)
                    print(tripleObject.SQL)
                    q= self.question.constructQuery(self.question.queryStatementFromTriple(tripleObject))
                    print(q)
                    self.data = requests.get(self.url, params={'query': q, 'format': 'json'}).json()
                    ##print(self.data)
                    if self.data["results"]["bindings"] != []:          ##not just proper query, but check if we also got answers
                        return True
                except:                                                 ##no query constructed with the triple, so we try the next one
                    pass
        return False

    def runNLP(self):
        ## First try: only the words in the question
        print(colored('Start with existing list', 'green'))
        if self.runNLPwithTripleList():
            return True
        ##Second try: expand the list with nounified versions and synonims
        print(colored('Expanding list with nounify', 'blue'))

        self.question.addNounSynonims()                 ##first add the nouns and synonims for the tags in the original dep list
        self.question.extended_parse_spacy()            ## then add nouns and synonims for the tags in the extended list
        if self.runNLPwithTripleList():
            return True

        self.triedAllExtensions = True
        print("Could not construct query for the question :" + self.question.question)
        return False

    def possibleTriplesRemaining(self):
        print("checking the remaining triples")
        print("Object: " + str(len(self.question.possible_triples["Object"])) + " Property: " + str(
            len(self.question.possible_triples["Property"])) + " Result: " + str(
            len(self.question.possible_triples["Result"])))
        if len(self.question.possible_triples["Result"])>0 or len(self.question.possible_triples["Property"])>0 or len(self.question.possible_triples["Object"])>0:
            return True
        return False

    def extendable(self):
        for dep in self.question.nlp.tokens:
            for key, depList in self.question.specs.extended_deps.items():
                if dep.dep_ in depList:
                    return True
        return False

    def getAnswer(self):
        print("question is ")
        print(self.question.question)
        print(" with type " + self.question.type)
        ###this defines what to print, based on the type. Currently there are only list type (simple answer ~ list one), so the others are not implemented
        #print(data)

        ##in case there were initally no possible triples, and the list is also not extendable,  we extend with induced properties from the question word (like, 'Where is Singapore?')
        if not self.possibleTriplesRemaining() and not self.extendable():
            print(colored('No triples originally, Inducing properties from question words', 'green'))
            self.question.induceWordsFromQuestionWord()

        i=0
        #print(num)
        #self.question.constructQuery()
        if self.question.type == "true_false":              ##checks if any of the results from the query is the same as some word in the question (like 'is it true, that the capital of the Netherlands is Amsterdam?' --> Netherlands, capital --> query gives Amsterdam --> chacks if in the question --> print yes
            print(self.question.question)
            while self.possibleTriplesRemaining() and not self.triedAllExtensions :
                self.runNLP()
                for answer in self.data["results"]["bindings"]:
                    for word in self.question.nlp.tokens:
                        if word.text == answer[(self.question.targetVariable)[1:]]['value']:
                            print("yes")
                            return
                print("match not found, restarting the queries, number of possible triples remainig:")


            print("no")
            return


        # if self.question.type == "list" or self.question.type == "count":
        #     self.runNLP()
        #     num = len(self.data['results']['bindings'])
        # else:
        #     ####TODO
        #     num = query[arg]["numberOfAnswers"]

        if self.question.type == "count":
            ####TODO
            pass

        if self.question.type == 'superlative':
            numberOfAnswers = self.question.getNumberOfAnswers()-1
            count = 0
            # Running the trials
            if self.runNLP():
                #########################################

                for answer in self.data['results']['bindings']:
                    if answer == '':
                        print('no answer found')
                    else:
                        print(answer[(self.question.targetVariable)[1:]]['value'])
                    count += 1
                    if count>numberOfAnswers:
                        break

        if self.question.type == "list":
            #print(self.question.question)
            #print('target is: ')
            #print(self.question.targetVariable)
            #print('data is ')
            #print(self.data)

            # Running the trials
            if self.runNLP():
            #########################################

                for answer in self.data['results']['bindings']:
                    if answer == '':
                        print('no answer found')
                    else:
                        print(answer[(self.question.targetVariable)[1:]]['value'])
