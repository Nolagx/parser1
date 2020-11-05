from datatypes import DataTypes


class Span:
    """a representation of a span"""

    def __init__(self, left_num, right_num):
        self.left_num = left_num
        self.right_num = right_num

    def __str__(self):
        return "[" + str(self.left_num) + ", " + str(self.right_num) + ")"

    def get_pydatalog_string(self):
        return "(" + str(self.left_num) + ", " + str(self.right_num) + ")"


class Relation:

    def __init__(self, name, terms):
        self.name = name
        self.terms = terms

    def __str__(self):
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


class RelationDeclaration:

    def __init__(self, name, schema):
        self.name = name
        self.schema = schema

    def __str__(self):
        ret = self.name + "("
        for idx, term in enumerate(self.schema):
            if term == DataTypes.STRING:
                ret += 'str'
            elif term == DataTypes.SPAN:
                ret += 'spn'
            elif term == DataTypes.INT:
                ret += "int"
            else:
                assert 0
            if idx < len(self.schema) - 1:
                ret += ", "
        ret += ")"
        return ret
