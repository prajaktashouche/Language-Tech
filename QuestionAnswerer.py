import requests
import sys

##this clss takes a questionParser object as an argument. Sends the query as a request and prints the answer


class QuestionAnswerer:
    def __init__(self, question):
        self.url = 'https://query.wikidata.org//sparql'
        self.data = None
        self.question = question

        self.runNLP()

    def runRegex(self):
        try:
            self.data = requests.get(self.url, params={'query': self.question.constructQuery(self.question.queryBodyFromList(self.question.query_list)), 'format': 'json'}).json()  ###this line sends the actual request and stores the answer
        except:
            print("could not construct query with question: " + self.question.question)
            self.data = None

    def runNLP(self):
        for key, tripleList in self.question.possible_triples.items():
            for triple in tripleList:
                try:
                    #print("triple is :")
                    #print(triple)
                    #print("format is ")
                    #print(self.question.specs.basic_question_formats[key])
                    q= self.question.constructQuery(self.question.queryStatementFromTriple(self.question.getTripleFromWordsAndFormat(triple, self.question.specs.basic_question_formats[key])))
                    #print(q)
                    self.data = requests.get(self.url, params={'query': q, 'format': 'json'}).json()
                    return
                except:
                    pass
        print("Could not construct query for the question :" + self.question.question)

    def getAnswer(self):
        if self.data:
            ###this defines what to print, based on the type. Currently there are only list type (simple answer ~ list one), so the others are not implemented
            #print(data)
            i=0
            #print(num)
            #self.question.constructQuery()
            if self.question.type == "true_false":
                ####TODO
                print(self.question.question)
                if query[arg]["target"] == data["results"]["bindings"][0][query[arg]["variable"]]["value"]:
                    print("yes")
                else:
                    print("no")
                exit()

            if self.question.type == "list" or self.question.type == "count":
                num = len(self.data['results']['bindings'])
            else:
                ####TODO
                num = query[arg]["numberOfAnswers"]

            if self.question.type == "count":
                ####TODO
                print(query[arg]["question"])
                print(num)
                exit()

            if self.question.type == "list":
                #print(self.question.question)
                #print('target is: ')
                #print(self.question.targetVariable)
                #print('data is ')
                #print(self.data)
                for answer in self.data['results']['bindings']:
                    if answer == '':
                        print('no answer found')
                    else:

                        print(answer[(self.question.targetVariable)[1:]]['value'])