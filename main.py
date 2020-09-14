from lark import Lark, Transformer, v_args, Visitor
from pyDatalog import pyDatalog


@v_args(inline=True)
class CalculateTree(Transformer):
    # noinspection PyUnresolvedReferences
    from operator import add, sub, mul, truediv as div, neg
    number = float

    def __init__(self):
        super().__init__()
        self.vars = {}

    def assign_var(self, name, value):
        self.vars[name] = value
        return value

    def var(self, name):
        return self.vars[name]


@v_args(inline=True)
class TestTransformer(Transformer):
    # get rid of "integer" in the tree
    integer = int
    # comment = lambda self: "comment"
    # def multiline_string(self, *string_list):
    #     result = ""
    #     for string in string_list:
    #         print(string)
    #         result += string
    #     return result
    #
    # def string(self, arg):
    #     print("AAAAAAAAAAAAAAAAAAAAAA")


@v_args(inline=False)
class StringTransformer(Transformer):

    def string(self, string_list):
        result = ""
        for token in string_list:
            string = token[1:-1]
            result += string
        return result


class Relation:
    def __init__(self, name, terms):
        self.name = name
        self.terms = terms

    def get_string_format(self):
        ret = self.name + "("
        for idx, term in enumerate(self.terms):
            ret += term
            if idx < len(self.terms) - 1:
                ret += ", "
        ret += ")"
        return ret

    def __repr__(self):
        return self.get_string_format()

@v_args(inline=False)
class RelationTransformer(Transformer):

    def relation(self, args):
        name = args[0]
        terms = args[1:]
        return Relation(name, terms)


class FactVisitor(Visitor):

    def fact(self, tree):
        assert tree.data == "fact"
        relation = tree.children[0]
        pyDatalog.assert_fact(relation.name, *relation.terms)


class QueryVisitor(Visitor):

    def query(self, tree):
        assert tree.data == "query"
        relation = tree.children[0]
        print(pyDatalog.ask(relation.get_string_format()))


@v_args(inline=False)
class StringTransformer(Transformer):

    def string(self, string_list):
        result = ""
        for token in string_list:
            string = token[1:-1]
            result += string
        return result

def main():
    with open('grammar.lark', 'r') as grammar:
        # parser = Lark(grammar, parser='lalr', transformer=CalculateTree())
        # parser = Lark(grammar, parser='lalr', transformer=CalculateTree2())
        parser = Lark(grammar, parser='earley', debug=False)

        test_input = open("test_input").read()
        parse_tree = parser.parse(test_input)
        parse_tree = TestTransformer().transform(parse_tree)
        parse_tree = StringTransformer().transform(parse_tree)
        parse_tree = RelationTransformer().transform(parse_tree)
        parse_tree = FactVisitor().visit(parse_tree)
        parse_tree = QueryVisitor().visit(parse_tree)
        print(parse_tree.pretty())
        print(parse_tree)

        # non_empty_lines = (line for line in test_input.splitlines() if len(line))

        # for line in non_empty_lines:
        #     # print(line)
        #     print(parser.parse(line))


if __name__ == "__main__":
    main()
