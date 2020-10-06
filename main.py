from lark import Lark, Transformer, v_args, Visitor, Tree
from lark.visitors import Interpreter, Visitor_Recursive
from pyDatalog import pyDatalog
from enum import Enum
import exceptions

NODES_OF_LIST_WITH_VAR_NAMES = {"term_list", "const_term_list"}
NODES_OF_LIST_WITH_RELATION_NAMES = {"rule_body_relation_list"}
NODES_OF_LIST_WITH_FREE_VAR_NAMES = {"term_list", "free_var_name_list"}


class VarTypes(Enum):
    STRING = 0
    SPAN = 1
    INT = 2


class Relation:
    def __init__(self, name, terms):
        self.name = name
        self.terms = terms

    def get_string_representation(self):
        ret = self.name + "("
        for idx, term in enumerate(self.terms):
            ret += term
            if idx < len(self.terms) - 1:
                ret += ", "
        ret += ")"
        return ret

    def __repr__(self):
        return self.get_string_representation()


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

    def __check_if_var_not_defined(self, var_name_node):
        assert_correct_node(var_name_node, "var_name", 1)
        var_name = var_name_node.children[0]
        if var_name not in self.vars:
            raise NameError("variable " + var_name + " is not defined")

    def __check_if_vars_in_list_not_defined(self, tree):
        assert tree.data in NODES_OF_LIST_WITH_VAR_NAMES
        for child in tree.children:
            if child.data == "var_name":
                self.__check_if_var_not_defined(child)

    def assign_literal_string(self, tree):
        assert_correct_node(tree, "assign_literal_string", 2, "var_name", "string")
        self.__add_var_name_to_vars(tree.children[0])

    def assign_string_from_file_string_param(self, tree):
        assert_correct_node(tree, "assign_string_from_file_string_param", 2, "var_name", "string")
        self.__add_var_name_to_vars(tree.children[0])

    def assign_string_from_file_var_param(self, tree):
        assert_correct_node(tree, "assign_string_from_file_var_param", 2, "var_name", "var_name")
        self.__check_if_var_not_defined(tree.children[1])
        self.__add_var_name_to_vars(tree.children[0])

    def assign_span(self, tree):
        assert_correct_node(tree, "assign_span", 2, "var_name", "span")
        self.__add_var_name_to_vars(tree.children[0])

    def assign_int(self, tree):
        assert_correct_node(tree, "assign_int", 2, "var_name", "integer")
        self.__add_var_name_to_vars(tree.children[0])

    def assign_var(self, tree):
        assert_correct_node(tree, "assign_var", 2, "var_name", "var_name")
        self.__check_if_var_not_defined(tree.children[1])
        self.__add_var_name_to_vars(tree.children[0])

    def relation(self, tree):
        assert_correct_node(tree, "relation", 2, "relation_name", "term_list")
        self.__check_if_vars_in_list_not_defined(tree.children[1])

    def fact(self, tree):
        assert_correct_node(tree, "fact", 2, "relation_name", "const_term_list")
        self.__check_if_vars_in_list_not_defined(tree.children[1])

    def rgx_ie_relation(self, tree):
        assert_correct_node(tree, "rgx_ie_relation", 3, "term_list", "term_list", "var_name")
        self.__check_if_vars_in_list_not_defined(tree.children[0])
        self.__check_if_vars_in_list_not_defined(tree.children[1])
        self.__check_if_var_not_defined(tree.children[2])

    def func_ie_relation(self, tree):
        assert_correct_node(tree, "func_ie_relation", 3, "function_name", "term_list", "term_list")
        self.__check_if_vars_in_list_not_defined(tree.children[1])
        self.__check_if_vars_in_list_not_defined(tree.children[2])

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
        assert_correct_node(tree, "fact", 2, "relation_name", "const_term_list")
        self.__check_if_relation_not_defined(tree.children[0])

    def rule(self, tree):
        assert_correct_node(tree, "rule", 2, "rule_head", "rule_body")
        assert_correct_node(tree.children[1], "rule_body", 1, "rule_body_relation_list")
        self.__check_if_list_relations_not_defined(tree.children[1].children[0])
        assert_correct_node(tree.children[0], "rule_head", 2, "relation_name", "free_var_name_list")
        # TODO allow adding rules to the same relation (currently allowed)? under what conditions?
        self.__add_relation_name_to_relations(tree.children[0].children[0])


class CheckRuleSafetyVisitor(Visitor_Recursive):

    def __init__(self):
        super().__init__()

    @staticmethod
    def _get_set_of_free_var_names(list_node):
        assert list_node.data in NODES_OF_LIST_WITH_FREE_VAR_NAMES
        free_var_names = set()
        for term_node in list_node.children:
            if term_node.data == "free_var_name":
                assert_correct_node(term_node, "free_var_name", 1)
                free_var_names.add(term_node.children[0])
        return free_var_names

    def _get_set_of_input_free_var_names(self, relation_node):
        if relation_node.data == "relation":
            assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
            return set()  # normal relations don't have an input
        elif relation_node.data == "func_ie_relation":
            assert_correct_node(relation_node, "func_ie_relation", 3, "function_name", "term_list", "term_list")
            return self._get_set_of_free_var_names(relation_node.children[1])
        else:
            assert_correct_node(relation_node, "rgx_ie_relation", 3, "term_list", "term_list", "var_name")
            return self._get_set_of_free_var_names(relation_node.children[0])

    def _get_set_of_output_free_var_names(self, relation_node):
        if relation_node.data == "relation":
            assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
            return self._get_set_of_free_var_names(relation_node.children[1])
        elif relation_node.data == "func_ie_relation":
            assert_correct_node(relation_node, "func_ie_relation", 3, "function_name", "term_list", "term_list")
            return self._get_set_of_free_var_names(relation_node.children[2])
        else:
            assert_correct_node(relation_node, "rgx_ie_relation", 3, "term_list", "term_list", "var_name")
            return self._get_set_of_free_var_names(relation_node.children[1])

    def rule(self, tree):
        """
        This function checks that a rule is safe. For a rule to be safe, two conditions must apply:

        1. Every free variable in the head occurs at least once in the body as an output of a relation.

        examples:
        a. "parent(X,Y) <- son(X)" is not a safe rule because the free variable Y only appears in the rule head.
        b. "parent(X,Z) <- parent(X,Y), parent(Y,Z)" is a safe rule as both X,Z that appear in the rule head, also
            appear in the rule body.
        c. "happy(X) <- is_happy<X>(Y)" is not a safe rule as X does not appear as an output of a relation.

        2. Every free variable is bound.
        A bound free variable is a free variable that has a constraint that imposes a
        limit on the amount of values it can take.

        In order to check that every free variable is bound, we will check that every relation in the rule body
        is a safe relation, meaning:
        a. A safe relation is one where its input relation is safe,
        meaning all its input's free variables are bound.
        b. A bound variable is one that exists in the output of a safe relation.

        examples:
        a. "rel2(X,Y) <- rel1(X,Z),ie1<X>(Y)" is safe as the only input free variable, X, exists in the output of
        the safe relation rel1(X,Z).
        b. " rel2(Y) <- ie1<Z>(Y)" is not safe as the input free variable Z does not exist in the output of any
        safe relation.
        """
        assert_correct_node(tree, "rule", 2, "rule_head", "rule_body")
        assert_correct_node(tree.children[0], "rule_head", 2, "relation_name", "free_var_name_list")
        assert_correct_node(tree.children[1], "rule_body", 1, "rule_body_relation_list")
        rule_head_term_list_node = tree.children[0].children[1]
        rule_body_relation_list_node = tree.children[1].children[0]
        assert_correct_node(rule_head_term_list_node, "free_var_name_list")
        assert_correct_node(rule_body_relation_list_node, "rule_body_relation_list")
        # check that every free variable in the head occurs at least once in the body as an output of a relation.
        # get the free variables in the rule head
        rule_head_free_vars = self._get_set_of_free_var_names(rule_head_term_list_node)
        # get the free variables in the rule body
        rule_body_free_vars = set()
        for relation_node in rule_body_relation_list_node.children:
            # get all the free variables that appear in the relation's output
            relation_output_free_vars = self._get_set_of_output_free_var_names(relation_node)
            rule_body_free_vars = rule_body_free_vars.union(relation_output_free_vars)
        # make sure that every free var in the rule head appears at least once in the rule body
        invalid_free_var_names = rule_head_free_vars.difference(rule_body_free_vars)
        if invalid_free_var_names:
            raise exceptions.RuleNotSafeError(
                "the following free variables appear in the rule head but not in any"
                " relation's output in the rule body:\n" + str(invalid_free_var_names))
        # check that every relation in the rule body is safe
        # initialize assuming every relation is unsafe and every free variable is unbound
        safe_relation_nodes = set()
        bound_free_vars = set()
        found_safe_relation_in_cur_iter = True
        while len(safe_relation_nodes) != len(rule_body_relation_list_node.children) \
                and found_safe_relation_in_cur_iter:
            found_safe_relation_in_cur_iter = False
            for relation_node in rule_body_relation_list_node.children:
                if relation_node not in safe_relation_nodes:
                    input_free_vars = self._get_set_of_input_free_var_names(relation_node)
                    unbound_free_vars = input_free_vars.difference(bound_free_vars)
                    if not unbound_free_vars:
                        found_safe_relation_in_cur_iter = True
                        output_free_vars = self._get_set_of_output_free_var_names(relation_node)
                        bound_free_vars = bound_free_vars.union(output_free_vars)
                        safe_relation_nodes.add(relation_node)
        if not len(safe_relation_nodes) == len(rule_body_relation_list_node.children):
            # find and print all the free variables that are unbound
            all_input_free_vars = set()
            for relation_node in rule_body_relation_list_node.children:
                all_input_free_vars = \
                    all_input_free_vars.union(self._get_set_of_input_free_var_names(relation_node))
            unbound_free_vars = all_input_free_vars.difference(bound_free_vars)
            assert unbound_free_vars
            raise exceptions.RuleNotSafeError(
                "the following free variables are unbound\n" + str(unbound_free_vars))


class TypeCheckingInterpreter(Interpreter):

    def __init__(self):
        super().__init__()
        self.var_name_to_type = dict()
        self.relation_name_to_schema = dict()

    def __add_var_type(self, var_name_node, var_type: VarTypes):
        assert_correct_node(var_name_node, "var_name", 1)
        var_name = var_name_node.children[0]
        self.var_name_to_type[var_name] = var_type

    def __get_var_type(self, var_name_node):
        assert_correct_node(var_name_node, "var_name", 1)
        var_name = var_name_node.children[0]
        assert var_name in self.var_name_to_type
        return self.var_name_to_type[var_name]

    def __add_relation_schema(self, relation_name_node, relation_schema):
        assert_correct_node(relation_name_node, "relation_name", 1)
        relation_name = relation_name_node.children[0]
        assert relation_name not in self.relation_name_to_schema
        self.relation_name_to_schema[relation_name] = relation_schema

    def __get_relation_schema(self, relation_name_node):
        assert_correct_node(relation_name_node, "relation_name", 1)
        relation_name = relation_name_node.children[0]
        assert relation_name in self.relation_name_to_schema
        return self.relation_name_to_schema[relation_name]

    def __get_term_type(self, term_node):
        term_type = term_node.data
        if term_type == "string":
            return VarTypes.STRING
        elif term_type == "span":
            return VarTypes.SPAN
        elif term_type == "int":
            return VarTypes.INT
        elif term_type == "var_name":
            assert_correct_node(term_node, "var_name", 1)
            return self.__get_var_type(self.var_name_to_type[term_type])
        elif term_type == "free_var_name":
            # Can't determine type from the term node alone.
            # leave it to the caller to figure out what the free variable type is.
            return None
        else:
            assert 0

    def __get_term_sequence_types(self, term_list_node, free_var_mapping=None, relation_name_node=None):
        """
        :param term_list_node: list of terms (e.g. terms used when declaring a fact)
        :param free_var_mapping: when encountering a free variable, get it's type
        :param relation_name_node:
        :return:
        """
        pass

    def assign_literal_string(self, tree):
        assert_correct_node(tree, "assign_literal_string", 2, "var_name", "string")
        self.__add_var_type(tree.children[0], VarTypes.STRING)

    def assign_string_from_file_string_param(self, tree):
        assert_correct_node(tree, "assign_string_from_file_string_param", 2, "var_name", "string")
        self.__add_var_type(tree.children[0], VarTypes.STRING)

    def assign_string_from_file_var_param(self, tree):
        assert_correct_node(tree, "assign_string_from_file_var_param", 2, "var_name", "var_name")
        self.__add_var_type(tree.children[0], VarTypes.STRING)

    def assign_span(self, tree):
        assert_correct_node(tree, "assign_span", 2, "var_name", "span")
        self.__add_var_type(tree.children[0], VarTypes.SPAN)

    def assign_int(self, tree):
        assert_correct_node(tree, "assign_int", 2, "var_name", "integer")
        self.__add_var_type(tree.children[0], VarTypes.INT)

    def assign_var(self, tree):
        assert_correct_node(tree, "assign_var", 2, "var_name", "var_name")
        self.__add_var_type(tree.children[0], self.__get_var_type(tree.children[1]))

    def relation_declaration(self, tree):
        assert_correct_node(tree, "relation_declaration", 2, "relation_name", "decl_term_list")
        decl_term_list_node = tree.children[1]
        assert_correct_node(tree, "decl_term_list")
        declared_schema = []
        for term_node in decl_term_list_node.children:
            if term_node.data == "decl_string":
                declared_schema.append(VarTypes.STRING)
            elif term_node.data == "decl_span":
                declared_schema.append(VarTypes.SPAN)
            elif term_node.data == "decl_int":
                declared_schema.append(VarTypes.INT)
            else:
                assert 0
        self.__add_relation_schema(tree.children[0], declared_schema)

    def relation(self, tree):
        assert_correct_node(tree, "relation", 2, "relation_name", "term_list")
        relation_name_node = tree.children[0]
        relation_schema = self.__get_relation_schema(relation_name_node)


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


# TODO do this with visitor instead (more efficient)
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


# @v_args(inline=False)
# class StringTransformer(Transformer):
#
#     def string(self, string_list):
#         result = ""
#         for token in string_list:
#             string = token[1:-1]
#             result += string
#         return result

class StringVisitor(Visitor_Recursive):

    def string(self, tree):
        tree.children[0] = tree.children[0].replace('\\\n', '')


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
        parser = Lark(grammar, parser='lalr', debug=True)

        test_input = open("test_input2").read()
        parse_tree = parser.parse(test_input)
        parse_tree = RemoveTokensTransformer().transform(parse_tree)
        parse_tree = StringVisitor().visit(parse_tree)
        CheckReferencedVariablesInterpreter().visit(parse_tree)
        CheckReferencedRelationsInterpreter().visit(parse_tree)
        CheckRuleSafetyVisitor().visit(parse_tree)
        # parse_tree = PyDatalogRepresentationVisitor().visit(parse_tree)
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
