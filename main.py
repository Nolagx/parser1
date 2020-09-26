from lark import Lark, Transformer, v_args, Visitor
from lark.visitors import Interpreter, Visitor_Recursive
from pyDatalog import pyDatalog
import exceptions

NODES_OF_LIST_WITH_VAR_NAMES = {"term_list", "fact_term_list"}
NODES_OF_LIST_WITH_RELATION_NAMES = {"rule_body_relation_list"}


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


class CheckReferencedVariablesInterpreter(Interpreter):

    def __init__(self):
        super().__init__()
        self.vars = set()

    def __add_var_name_to_vars(self, var_name_node):
        assert_correct_node(var_name_node, "var_name", 1)
        var_name = var_name_node.children[0]
        self.vars.add(var_name)

    def __check_defined_variable(self, var_name_node):
        assert_correct_node(var_name_node, "var_name", 1)
        var_name = var_name_node.children[0]
        if var_name not in self.vars:
            raise NameError("variable " + var_name + " is not defined")

    def __check_defined_variables_in_list(self, tree):
        assert tree.data in NODES_OF_LIST_WITH_VAR_NAMES
        for child in tree.children:
            if child.data == "var_name":
                self.__check_defined_variable(child)

    def assign_literal_string(self, tree):
        assert_correct_node(tree, "assign_literal_string", 2, "var_name", "string")
        self.__add_var_name_to_vars(tree.children[0])

    def assign_string_from_file_string_param(self, tree):
        assert_correct_node(tree, "assign_string_from_file_string_param", 2, "var_name", "string")
        self.__add_var_name_to_vars(tree.children[0])

    def assign_string_from_file_var_param(self, tree):
        assert_correct_node(tree, "assign_string_from_file_var_param", 2, "var_name", "var_name")
        self.__check_defined_variable(tree.children[1])
        self.__add_var_name_to_vars(tree.children[0])

    def assign_span(self, tree):
        assert_correct_node(tree, "assign_span", 2, "var_name", "span")
        self.__add_var_name_to_vars(tree.children[0])

    def assign_int(self, tree):
        assert_correct_node(tree, "assign_int", 2, "var_name", "integer")
        self.__add_var_name_to_vars(tree.children[0])

    def assign_var(self, tree):
        assert_correct_node(tree, "assign_var", 2, "var_name", "var_name")
        self.__check_defined_variable(tree.children[1])
        self.__add_var_name_to_vars(tree.children[0])

    def relation(self, tree):
        assert_correct_node(tree, "relation", 2, "relation_name", "term_list")
        self.__check_defined_variables_in_list(tree.children[1])

    def fact(self, tree):
        assert_correct_node(tree, "fact", 2, "relation_name", "fact_term_list")
        self.__check_defined_variables_in_list(tree.children[1])

    def rgx_ie_relation(self, tree):
        assert_correct_node(tree, "rgx_ie_relation", 3, "rgx_relation_arg", "term_list", "var_name")
        if tree.children[0].children[0].data == "var_name":
            self.__check_defined_variable(tree.children[0].children[0])
        self.__check_defined_variables_in_list(tree.children[1])
        self.__check_defined_variable(tree.children[2])

    def func_ie_relation(self, tree):
        assert_correct_node(tree, "func_ie_relation", 3, "function_name", "term_list", "term_list")
        self.__check_defined_variables_in_list(tree.children[1])
        self.__check_defined_variables_in_list(tree.children[2])

    # TODO maybe use for variable assignment at a different visitor?
    # def assign_var(self, name, value):
    #     self.vars[name] = value
    #     return value

    # def var(self, name):
    #     return self.vars[name]


class CheckReferencedRelationsInterpreter(Interpreter):

    def __init__(self):
        super().__init__()
        self.relations = set()

    def __add_relation_name_to_relations(self, relation_name_node):
        assert_correct_node(relation_name_node, "relation_name", 1)
        relation_name = relation_name_node.children[0]
        self.relations.add(relation_name)

    def __check_if_relation_not_defined(self, relation_name_node):
        assert_correct_node(relation_name_node, "relation_name", 1)
        relation_name = relation_name_node.children[0]
        if relation_name not in self.relations:
            raise NameError("relation " + relation_name + " is not defined")

    def __check_if_relation_already_defined(self, relation_name_node):
        assert_correct_node(relation_name_node, "relation_name", 1)
        relation_name = relation_name_node.children[0]
        if relation_name in self.relations:
            raise NameError("relation " + relation_name + " is already defined")

    @staticmethod
    def __get_relation_name_node(tree):
        if tree.data == "relation":
            assert_correct_node(tree, "relation", 2, "relation_name", "term_list")
            return tree.children[0]

    def __check_if_list_relations_not_defined(self, list_node):
        assert list_node.data in NODES_OF_LIST_WITH_RELATION_NAMES
        for child in list_node.children:
            if child.data == "relation":
                self.__check_if_relation_not_defined(self.__get_relation_name_node(child))

    def relation_declaration(self, tree):
        assert_correct_node(tree, "relation_declaration", 2, "relation_name", "decl_term_list")
        self.__check_if_relation_already_defined(tree.children[0])
        self.__add_relation_name_to_relations(tree.children[0])

    def query(self, tree):
        assert_correct_node(tree, "query", 1, "relation")
        self.__check_if_relation_not_defined(self.__get_relation_name_node(tree.children[0]))

    def fact(self, tree):
        assert_correct_node(tree, "fact", 2, "relation_name", "fact_term_list")
        self.__check_if_relation_not_defined(tree.children[0])

    def rule(self, tree):
        assert_correct_node(tree, "rule", 2, "rule_head", "rule_body")
        assert_correct_node(tree.children[1], "rule_body", 1, "rule_body_relation_list")
        self.__check_if_list_relations_not_defined(tree.children[1].children[0])
        assert_correct_node(tree.children[0], "rule_head", 2, "relation_name", "free_var_name_list")
        # TODO allow adding rules to the same relation (currently allowed)? under what conditions?
        self.__add_relation_name_to_relations(tree.children[0].children[0])


class CheckRuleSafetyInterpreter(Interpreter):

    def __init__(self):
        super().__init__()

    def rule(self, tree):
        assert_correct_node(tree, "rule", 2, "rule_head", "rule_body")
        assert_correct_node(tree.children[0], "rule_head", 2, "relation_name", "free_var_name_list")
        assert_correct_node(tree.children[1], "rule_body", 1, "rule_body_relation_list")
        rule_head_vars_list_node = tree.children[0].children[1]
        rule_body_relation_nodes = tree.children[1].children[0]
        assert_correct_node(rule_head_vars_list_node, "free_var_name_list")
        assert_correct_node(rule_body_relation_nodes, "rule_body_relation_list")
        # get the free variables in the rule head
        rule_head_free_vars = set()
        for free_var_node in rule_head_vars_list_node.children:
            assert_correct_node(free_var_node, "free_var_name", 1)
            rule_head_free_vars.add(free_var_node.children[0])
        # get the free variables in the rule body
        rule_body_free_vars = set()
        for relation_node in rule_body_relation_nodes.children:
            # first we must find the terms list depending on the relation we're dealing with
            if relation_node.data == "relation":
                assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
                term_list_node = relation_node.children[1]
            elif relation_node.data == "func_ie_relation":
                assert_correct_node(relation_node, "func_ie_relation", 3, "function_name", "term_list", "term_list")
                term_list_node = relation_node.children[2]  # get only the output parameters
            else:
                assert_correct_node(relation_node, "rgx_ie_relation", 3, "rgx_relation_arg", "term_list", "var_name")
                term_list_node = relation_node.children[1]
            assert_correct_node(term_list_node, "term_list")
            # get all the free variables that appear in the relation's output
            for term_node in term_list_node.children:
                if term_node.data == "free_var_name":
                    assert_correct_node(term_node, "free_var_name", 1)
                    rule_body_free_vars.add(term_node.children[0])
        # finally, make sure that every free var in the rule head appears at least once in the rule body
        for rule_head_free_var in rule_head_free_vars:
            if rule_head_free_var not in rule_body_free_vars:
                raise exceptions.RuleNotSafeError(
                    "free variable " + rule_head_free_var + " appears in rule head but not in rule body")


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

        test_input = open("test_input2").read()
        parse_tree = parser.parse(test_input)
        # parse_tree = StringTransformer().transform(parse_tree)
        # parse_tree = RelationTransformer().transform(parse_tree)
        # parse_tree = FactVisitor().visit(parse_tree)
        # parse_tree = QueryVisitor().visit(parse_tree)
        # parse_tree = RemoveIntegerTransformer().transform(parse_tree)
        parse_tree = RemoveTokensTransformer().transform(parse_tree)
        parse_tree = MultilineStringToStringVisitor().visit(parse_tree)
        CheckReferencedVariablesInterpreter().visit(parse_tree)
        CheckReferencedRelationsInterpreter().visit(parse_tree)
        CheckRuleSafetyInterpreter().visit(parse_tree)
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
