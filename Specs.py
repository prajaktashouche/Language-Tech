


class Specification:
    ###here we can store all relevant specifications, for now i have question words (not used) and regex patterns with corresponding object - property - result order
    ###takes a dictionary as input
    def __init__(self, specList):
        self.question_words = specList['question_words']
        self.patterns = specList['patterns']
        self.deps = specList['deps']
        self.basic_question_formats = specList['basic_question_formats']
