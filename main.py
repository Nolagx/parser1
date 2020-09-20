from lark import Lark, Transformer, v_args, Visitor
from lark.visitors import Interpreter, Visitor_Recursive
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
class RemoveIntegerTransformer(Transformer):
    # get rid of "integer" in the tree
    integer = int


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


# class CheckReferencedVariablesVisitor(Visitor_Recursive):
#
#     def __init__(self):
#         super().__init__()
#         self.vars = set()
#
#     def assign_literal_string(self, tree):
#         assert_correct_node(tree, "assign_literal_string", 2, "name", "string")
#         var_name = tree.children[0].children[0]
#         self.vars.add(var_name)
#
#     def assign_string_from_file_string_param(self, tree):
#         assert_correct_node(tree, "assign_string_from_file_string_param", 2, "name", "string")
#         var_name = tree.children[0].children[0]
#         self.vars.add(var_name)
#
#     def assign_string_from_file_var_param(self, tree):
#         assert_correct_node(tree, "assign_string_from_file_var_param", 2, "name", "name")
#         right_var_name = tree.children[1].children[0]
#         if right_var_name not in self.vars:
#             raise NameError("variable " + right_var_name + " is not defined")
#         left_var_name = tree.children[0].children[0]
#         self.vars.add(left_var_name)
#
#     def assign_span(self, tree):
#         assert_correct_node(tree, "assign_span", 2, "name", "span")
#         var_name = tree.children[0].children[0]
#         self.vars.add(var_name)
#
#     def assign_var(self, tree):
#         assert_correct_node(tree, "assign_var", 2, "name", "name")
#         right_var_name = tree.children[1].children[0]
#         if right_var_name not in self.vars:
#             raise NameError("variable " + right_var_name + " is not defined")
#         left_var_name = tree.children[0].children[0]
#         self.vars.add(left_var_name)
#
#     # TODO after we decide what to do with free variables:
#     # TODO relation
#     # TODO rgx_relation
#     def rgx_relation(self, tree):
#         assert tree.data == "rgx_relation"
#         assert tree.children[0].data == "string"
#         assert tree.children[-1].data == "name"
#         var_name = tree.children[-1].children[0]
#         if var_name not in self.vars:
#             raise NameError("variable " + var_name + " is not defined")
#     # TODO ie relation
#     # TODO declare rules? (raise issue)
#
#     # TODO maybe use for variable assignment at a different visitor?
#     # def assign_var(self, name, value):
#     #     self.vars[name] = value
#     #     return value
#
#     # def var(self, name):
#     #     return self.vars[name]

class CheckReferencedVariablesInterpreter(Interpreter):

    def __init__(self):
        super().__init__()
        self.vars = set()

    def assign_literal_string(self, tree):
        assert_correct_node(tree, "assign_literal_string", 2, "var_name", "string")
        var_name = tree.children[0].children[0]
        self.vars.add(var_name)

    def assign_string_from_file_string_param(self, tree):
        assert_correct_node(tree, "assign_string_from_file_string_param", 2, "var_name", "string")
        var_name = tree.children[0].children[0]
        self.vars.add(var_name)

    def assign_string_from_file_var_param(self, tree):
        assert_correct_node(tree, "assign_string_from_file_var_param", 2, "var_name", "var_name")
        right_var_name = tree.children[1].children[0]
        if right_var_name not in self.vars:
            raise NameError("variable " + right_var_name + " is not defined")
        left_var_name = tree.children[0].children[0]
        self.vars.add(left_var_name)

    def assign_span(self, tree):
        assert_correct_node(tree, "assign_span", 2, "var_name", "span")
        var_name = tree.children[0].children[0]
        self.vars.add(var_name)

    def assign_var(self, tree):
        assert_correct_node(tree, "assign_var", 2, "var_name", "var_name")
        right_var_name = tree.children[1].children[0]
        if right_var_name not in self.vars:
            raise NameError("variable " + right_var_name + " is not defined")
        left_var_name = tree.children[0].children[0]
        self.vars.add(left_var_name)

    # TODO after we decide what to do with free variables:
    # TODO relation
    # TODO rgx_relation
    def rgx_ie_relation(self, tree):
        assert_correct_node(tree, "rgx_ie_relation", 3, "term_list", "term_list", "var_name")
        var_name = tree.children[-1].children[0]
        if var_name not in self.vars:
            raise NameError("variable " + var_name + " is not defined")
    # TODO ie relation

    # TODO maybe use for variable assignment at a different visitor?
    # def assign_var(self, name, value):
    #     self.vars[name] = value
    #     return value

    # def var(self, name):
    #     return self.vars[name]


class MultilineStringToStringVisitor(Visitor_Recursive):

    def __init__(self):
        super().__init__()

    def multiline_string(self, tree):
        assert_correct_node(tree, "multiline_string")
        result = ""
        for child_string in tree.children:
            result += child_string
        # redefine the node to be a regular string node
        tree.data = "string"
        tree.children = [result]


@v_args(inline=False)
class RemoveTokensTransformer(Transformer):
    def __init__(self):
        super().__init__(visit_tokens=True)

    def INT(self, args):
        return int(args[0:])

    def LOWER_CASE_NAME(self, args):
        return args[0:]

    def UPPER_CASE_NAME(self, args):
        return args[0:]

    def STRING(self, args):
        # removes the quotation marks
        return args[1:-1]


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


def assert_correct_node(tree, node_name, len_children=None, *children_names):
    assert tree.data == node_name, "bad node name: " + node_name + \
                                   "\n actual node name: " + tree.data
    if len_children is not None:
        assert len(tree.children) == len_children, "bad children length: " + str(len_children) + \
                                                   "\n actual children length: " + str(len(tree.children))
    if children_names is not None:
        for idx, name in enumerate(children_names):
            assert tree.children[idx].data == name, "bad child name at index " + str(idx) + ": " + \
                                                    name + \
                                                    "\n actual child name: " + tree.children[idx].data


def main():
    with open('grammar.lark', 'r') as grammar:
        # parser = Lark(grammar, parser='lalr', transformer=CalculateTree())
        # parser = Lark(grammar, parser='lalr', transformer=CalculateTree2())
        parser = Lark(grammar, parser='earley', debug=False)

        test_input = open("test_input").read()
        parse_tree = parser.parse(test_input)
        # parse_tree = StringTransformer().transform(parse_tree)
        # parse_tree = RelationTransformer().transform(parse_tree)
        # parse_tree = FactVisitor().visit(parse_tree)
        # parse_tree = QueryVisitor().visit(parse_tree)
        # parse_tree = RemoveIntegerTransformer().transform(parse_tree)
        parse_tree = RemoveTokensTransformer().transform(parse_tree)
        parse_tree = MultilineStringToStringVisitor().visit(parse_tree)
        CheckReferencedVariablesInterpreter().visit(parse_tree)
        print("===================")
        print(parse_tree.pretty())
        for child in parse_tree.children:
            print(child)

        # non_empty_lines = (line for line in test_input.splitlines() if len(line))

        # for line in non_empty_lines:
        #     # print(line)
        #     print(parser.parse(line))


if __name__ == "__main__":
    main()
