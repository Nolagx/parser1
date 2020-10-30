class Span:
    """a representation of a span"""

    def __init__(self, left_num, right_num):
        self.left_num = left_num
        self.right_num = right_num

    def __repr__(self):
        print(self.__str__())

    def __str__(self):
        return "[" + str(self.left_num) + ", " + str(self.right_num) + ")"

    def get_pydatalog_string(self):
        return "(" + str(self.left_num) + ", " + str(self.right_num) + ")"


class Relation:

    def __init__(self, name, terms):
        self.name = name
        self.terms = terms

    def get_string_representation(self):
        ret = self.name + "("
        for idx, term in enumerate(self.terms):
            ret += str(term)
            if idx < len(self.terms) - 1:
                ret += ", "
        ret += ")"
        return ret

    def get_pydatalog_string(self):
        ret = self.name + "("
        for idx, term in enumerate(self.terms):
            if isinstance(term, Span):
                ret += term.get_pydatalog_string()
            else:
                ret += str(term)
            if idx < len(self.terms) - 1:
                ret += ", "
        ret += ")"
        return ret

    def __repr__(self):
        return self.get_string_representation()
