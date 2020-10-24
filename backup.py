from lark import Lark, Transformer, v_args, Visitor, Tree
from lark.visitors import Interpreter, Visitor_Recursive
import pyDatalog

class Span:
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

    def get_string_representation(self):
        return "[" + str(self.start) + ", " + str(self.stop) + ")"

    def __repr__(self):
        return self.get_string_representation()


@v_args(inline=False)
class RelationTransformer(Transformer):

    def relation(self, args):
        name = args[0]
        terms = args[1:]
        # return Relation(name, terms)
        return Tree("relation", ["test"])


class PyDatalogRepresentationVisitor(Visitor_Recursive):

    def relation(self, tree):
        pass


class FactVisitor(Visitor):

    def add_fact(self, tree):
        assert tree.data == "add_fact"
        relation = tree.children[0]
        pyDatalog.assert_fact(relation.name, *relation.terms)


class QueryVisitor(Visitor):

    def query(self, tree):
        assert tree.data == "query"
        relation = tree.children[0]
        print(pyDatalog.ask(relation.get_string_format()))