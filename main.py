from lark import Lark, Transformer, v_args, Visitor, Tree
from lark.visitors import Interpreter, Visitor_Recursive
from pyDatalog import pyDatalog
from enum import Enum
import exceptions

NODES_OF_LIST_WITH_VAR_NAMES = {"term_list", "const_term_list"}
NODES_OF_LIST_WITH_RELATION_NODES = {"rule_body_relation_list"}
NODES_OF_LIST_WITH_FREE_VAR_NAMES = {"term_list", "free_var_name_list"}
NODES_OF_TERM_LISTS = {"term_list", "const_term_list"}
NODES_OF_RULE_BODY_TERM_LISTS = {"term_list"}
SCHEMA_DEFINING_NODES = {"decl_term_list", "free_var_name_list"}


class VarTypes(Enum):
    STRING = 0
    SPAN = 1
    INT = 2


def get_error_line_string(tree):
    return "line " + str(tree.meta.line) + ": "


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

    def add_fact(self, tree):
        assert tree.data == "add_fact"
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
            raise NameError(get_error_line_string(var_name_node) + "variable " + var_name + " is not defined")

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

    def add_fact(self, tree):
        assert_correct_node(tree, "add_fact", 2, "relation_name", "const_term_list")
        self.__check_if_vars_in_list_not_defined(tree.children[1])

    def remove_fact(self, tree):
        assert_correct_node(tree, "remove_fact", 2, "relation_name", "const_term_list")
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
        self.relation_name_to_arity = dict()

    def __add_relation_definition(self, relation_name_node, schema_defining_node):
        assert_correct_node(relation_name_node, "relation_name", 1)
        assert schema_defining_node.data in SCHEMA_DEFINING_NODES
        relation_name = relation_name_node.children[0]
        assert relation_name not in self.relation_name_to_arity
        arity = len(schema_defining_node.children)
        self.relation_name_to_arity[relation_name] = arity

    def __check_if_relation_not_defined(self, relation_name_node, term_list_node):
        assert_correct_node(relation_name_node, "relation_name", 1)
        assert term_list_node.data in NODES_OF_TERM_LISTS
        relation_name = relation_name_node.children[0]
        if relation_name not in self.relation_name_to_arity:
            raise exceptions.RelationNotDefinedError(get_error_line_string(relation_name_node) + "relation " +
                                                     relation_name + " is not defined")
        arity = len(term_list_node.children)
        correct_arity = self.relation_name_to_arity[relation_name]
        if arity != correct_arity:
            raise exceptions.IncorrectArityError(
                get_error_line_string(relation_name_node) +
                "incorrect arity used for relation " + relation_name + ": " +
                str(arity) + " (expected " + str(correct_arity) + ")")

    def __check_if_relation_already_defined(self, relation_name_node):
        assert_correct_node(relation_name_node, "relation_name", 1)
        relation_name = relation_name_node.children[0]
        if relation_name in self.relation_name_to_arity:
            raise exceptions.RelationRedefinitionError(
                get_error_line_string(relation_name_node) + "relation "
                + relation_name + " is already defined")

    def relation_declaration(self, tree):
        assert_correct_node(tree, "relation_declaration", 2, "relation_name", "decl_term_list")
        self.__check_if_relation_already_defined(tree.children[0])
        self.__add_relation_definition(tree.children[0], tree.children[1])

    def query(self, tree):
        assert_correct_node(tree, "query", 1, "relation")
        relation_node = tree.children[0]
        assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
        self.__check_if_relation_not_defined(relation_node.children[0], relation_node.children[1])

    def add_fact(self, tree):
        assert_correct_node(tree, "add_fact", 2, "relation_name", "const_term_list")
        self.__check_if_relation_not_defined(tree.children[0], tree.children[1])

    def remove_fact(self, tree):
        assert_correct_node(tree, "remove_fact", 2, "relation_name", "const_term_list")
        self.__check_if_relation_not_defined(tree.children[0], tree.children[1])

    def rule(self, tree):
        assert_correct_node(tree, "rule", 2, "rule_head", "rule_body")
        rule_body_node = tree.children[1]
        assert_correct_node(rule_body_node, "rule_body", 1, "rule_body_relation_list")
        relation_list_node = rule_body_node.children[0]
        assert_correct_node(relation_list_node, "rule_body_relation_list")
        for relation_node in relation_list_node.children:
            if relation_node.data == "relation":
                assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
                self.__check_if_relation_not_defined(relation_node.children[0], relation_node.children[1])
        rule_head_node = tree.children[0]
        assert_correct_node(rule_head_node, "rule_head", 2, "relation_name", "free_var_name_list")
        # TODO allow adding rules to the same relation (currently allowed)? under what conditions?
        self.__add_relation_definition(rule_head_node.children[0], rule_head_node.children[1])


class CheckReferencedIERelationsVisitor(Visitor_Recursive):

    def __init__(self):
        super().__init__()

    def func_ie_relation(self, tree):
        assert_correct_node(tree, "func_ie_relation", 3, "function_name", "term_list", "term_list")
        # TODO

    def rgx_ie_relation(self, tree):
        assert_correct_node(tree, "rgx_ie_relation", 3, "term_list", "term_list", "var_name")
        # TODO


class CheckRuleSafetyVisitor(Visitor_Recursive):

    def __init__(self):
        super().__init__()

    @staticmethod
    def __get_set_of_free_var_names(list_node):
        assert list_node.data in NODES_OF_LIST_WITH_FREE_VAR_NAMES
        free_var_names = set()
        for term_node in list_node.children:
            if term_node.data == "free_var_name":
                assert_correct_node(term_node, "free_var_name", 1)
                free_var_names.add(term_node.children[0])
        return free_var_names

    def __get_set_of_input_free_var_names(self, relation_node):
        if relation_node.data == "relation":
            assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
            return set()  # normal relations don't have an input
        elif relation_node.data == "func_ie_relation":
            assert_correct_node(relation_node, "func_ie_relation", 3, "function_name", "term_list", "term_list")
            return self.__get_set_of_free_var_names(relation_node.children[1])
        else:
            assert_correct_node(relation_node, "rgx_ie_relation", 3, "term_list", "term_list", "var_name")
            return self.__get_set_of_free_var_names(relation_node.children[0])

    def __get_set_of_output_free_var_names(self, relation_node):
        if relation_node.data == "relation":
            assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
            return self.__get_set_of_free_var_names(relation_node.children[1])
        elif relation_node.data == "func_ie_relation":
            assert_correct_node(relation_node, "func_ie_relation", 3, "function_name", "term_list", "term_list")
            return self.__get_set_of_free_var_names(relation_node.children[2])
        else:
            assert_correct_node(relation_node, "rgx_ie_relation", 3, "term_list", "term_list", "var_name")
            return self.__get_set_of_free_var_names(relation_node.children[1])

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
        rule_body_relations = rule_body_relation_list_node.children
        # check that every free variable in the head occurs at least once in the body as an output of a relation.
        # get the free variables in the rule head
        rule_head_free_vars = self.__get_set_of_free_var_names(rule_head_term_list_node)
        # get the free variables in the rule body
        rule_body_free_vars = set()
        for relation_node in rule_body_relations:
            # get all the free variables that appear in the relation's output
            relation_output_free_vars = self.__get_set_of_output_free_var_names(relation_node)
            rule_body_free_vars = rule_body_free_vars.union(relation_output_free_vars)
        # make sure that every free var in the rule head appears at least once in the rule body
        invalid_free_var_names = rule_head_free_vars.difference(rule_body_free_vars)
        if invalid_free_var_names:
            raise exceptions.RuleNotSafeError(
                get_error_line_string(tree) +
                "the following free variables appear in the rule head but not in any"
                " relation's output in the rule body:\n" + str(invalid_free_var_names))
        # check that every relation in the rule body is safe
        # initialize assuming every relation is unsafe and every free variable is unbound
        safe_relation_indexes = set()
        bound_free_vars = set()
        found_safe_relation_in_cur_iter = True
        while len(safe_relation_indexes) != len(rule_body_relations) \
                and found_safe_relation_in_cur_iter:
            found_safe_relation_in_cur_iter = False
            for idx, relation_node in enumerate(rule_body_relations):
                if idx not in safe_relation_indexes:
                    input_free_vars = self.__get_set_of_input_free_var_names(relation_node)
                    unbound_free_vars = input_free_vars.difference(bound_free_vars)
                    if not unbound_free_vars:
                        # relation is safe, mark all of its output variables as bound
                        found_safe_relation_in_cur_iter = True
                        output_free_vars = self.__get_set_of_output_free_var_names(relation_node)
                        bound_free_vars = bound_free_vars.union(output_free_vars)
                        safe_relation_indexes.add(idx)
        if len(safe_relation_indexes) != len(rule_body_relations):
            # find and print all the free variables that are unbound
            all_input_free_vars = set()
            for relation_node in rule_body_relations:
                all_input_free_vars = \
                    all_input_free_vars.union(self.__get_set_of_input_free_var_names(relation_node))
            unbound_free_vars = all_input_free_vars.difference(bound_free_vars)
            assert unbound_free_vars
            raise exceptions.RuleNotSafeError(
                get_error_line_string(tree) + "the following free variables are unbound:\n" + str(unbound_free_vars))
        # TODO remove this assertion
        safe_relation_indexes_list = list(safe_relation_indexes)
        safe_relation_indexes_list.sort()
        assert safe_relation_indexes_list == list(range(len(rule_body_relations)))


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

    def __get_const_term_type(self, const_term_node):
        term_type = const_term_node.data
        if term_type == "string":
            return VarTypes.STRING
        elif term_type == "span":
            return VarTypes.SPAN
        elif term_type == "integer":
            return VarTypes.INT
        elif term_type == "var_name":
            assert_correct_node(const_term_node, "var_name", 1)
            return self.__get_var_type(const_term_node)
        else:
            # do not allow for term type of "free_var_name" as it is not a constant
            assert 0

    def __get_term_types_list(self, term_list_node: Tree, free_var_mapping: dict = None,
                              relation_name_node: Tree = None):
        """
        get a list of the term types. The optional variables determine what type is assigned to a free
        variable, one and only one of them should be used.
        :param term_list_node: node of a list of terms (e.g. terms used when declaring a fact).
        :param free_var_mapping: when encountering a free variable, get its type from this mapping.
        :param relation_name_node: when encountering a free variable, get its type from the schema of this relation.
        :return: a list of the term types
        """
        assert term_list_node.data in NODES_OF_TERM_LISTS
        term_nodes = term_list_node.children
        schema = None
        if relation_name_node is not None:
            assert_correct_node(relation_name_node, "relation_name", 1)
            schema = self.__get_relation_schema(relation_name_node)
            assert len(schema) == len(term_nodes)
        assert schema is None or free_var_mapping is None
        term_types = []
        for idx, term_node in enumerate(term_nodes):
            if term_node.data == "free_var_name":
                assert_correct_node(term_node, "free_var_name", 1)
                if schema:
                    term_types.append(schema[idx])
                elif free_var_mapping:
                    term_types.append(free_var_mapping[term_node.children[0]])
                else:
                    assert 0
            else:
                term_types.append(self.__get_const_term_type(term_node))
        return term_types

    @staticmethod
    def __get_type_list_string(type_list):
        ret = ""
        for idx, var_type in enumerate(type_list):
            if var_type == VarTypes.STRING:
                ret += "str"
            elif var_type == VarTypes.SPAN:
                ret += "spn"
            elif var_type == VarTypes.INT:
                ret += "int"
            else:
                assert 0
            if idx < len(type_list) - 1:
                ret += ", "
        return ret

    def __get_schema_string(self, relation_name_node, schema):
        assert_correct_node(relation_name_node, "relation_name", 1)
        return relation_name_node.children[0] + "(" + self.__get_type_list_string(schema) + ")"

    def __get_schema_comparison_string(self, relation_name_node, expected_schema, received_schema):
        assert_correct_node(relation_name_node, "relation_name", 1)
        assert expected_schema != received_schema
        return "expected: " + self.__get_schema_string(relation_name_node, expected_schema) + "\n" + \
               "got: " + self.__get_schema_string(relation_name_node, received_schema)

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
        assert_correct_node(decl_term_list_node, "decl_term_list")
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

    def add_fact(self, tree):
        assert_correct_node(tree, "add_fact", 2, "relation_name", "const_term_list")
        relation_name_node = tree.children[0]
        term_list_node = tree.children[1]
        term_types = self.__get_term_types_list(term_list_node)
        schema = self.__get_relation_schema(relation_name_node)
        if schema != term_types:
            raise exceptions.TermsNotProperlyTypedError(
                get_error_line_string(tree) + "the terms in the fact are not properly typed\n" +
                self.__get_schema_comparison_string(relation_name_node, schema, term_types))

    def remove_fact(self, tree):
        assert_correct_node(tree, "remove_fact", 2, "relation_name", "const_term_list")
        relation_name_node = tree.children[0]
        term_list_node = tree.children[1]
        term_types = self.__get_term_types_list(term_list_node)
        schema = self.__get_relation_schema(relation_name_node)
        if schema != term_types:
            raise exceptions.TermsNotProperlyTypedError(
                get_error_line_string(tree) + "the terms in the removed fact are not properly typed\n" +
                self.__get_schema_comparison_string(relation_name_node, schema, term_types))

    def query(self, tree):
        assert_correct_node(tree, "query", 1, "relation")
        relation_node = tree.children[0]
        assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
        relation_name_node = relation_node.children[0]
        term_list_node = relation_node.children[1]
        term_types = self.__get_term_types_list(term_list_node, relation_name_node=relation_name_node)
        schema = self.__get_relation_schema(relation_name_node)
        if schema != term_types:
            raise exceptions.TermsNotProperlyTypedError(
                get_error_line_string(tree) + "the terms in the query are not properly typed\n" +
                self.__get_schema_comparison_string(relation_name_node, schema, term_types))

    def __type_check_rule_body_term_list(self, term_list_node: Tree, correct_types: list,
                                         free_var_to_type: dict, conflicted_free_vars: dict):
        assert term_list_node.data in NODES_OF_RULE_BODY_TERM_LISTS
        assert len(term_list_node.children) == len(correct_types)
        term_list_is_properly_typed = True
        for idx, term_node in enumerate(term_list_node.children):
            correct_type = correct_types[idx]
            if term_node.data == "free_var_name":
                assert_correct_node(term_node, "free_var_name", 1)
                free_var = term_node.children[0]
                if free_var in free_var_to_type:
                    # free var already has a type, make sure there's no conflict with the currently wanted type
                    free_var_type = free_var_to_type[free_var]
                    if free_var_type != correct_type:
                        # found a conflicted free var, add it to the conflicted dict along with the conflicting types
                        if free_var not in conflicted_free_vars:
                            conflicted_free_vars[free_var] = set()
                        term_list_is_properly_typed = False
                        conflicted_free_vars[free_var].add(correct_type)
                        conflicted_free_vars[free_var].add(free_var_type)
                else:
                    # free var does not currently have a type, map it to the correct type
                    free_var_to_type[free_var] = correct_type
            else:
                term_type = self.__get_const_term_type(term_node)
                if term_type != correct_type:
                    term_list_is_properly_typed = False
        return term_list_is_properly_typed

    def rule(self, tree):
        assert_correct_node(tree, "rule", 2, "rule_head", "rule_body")
        assert_correct_node(tree.children[0], "rule_head", 2, "relation_name", "free_var_name_list")
        assert_correct_node(tree.children[1], "rule_body", 1, "rule_body_relation_list")
        rule_head_name_node = tree.children[0].children[0]
        assert rule_head_name_node.children[0] not in self.relation_name_to_schema
        rule_head_term_list_node = tree.children[0].children[1]
        rule_body_relation_list_node = tree.children[1].children[0]
        assert_correct_node(rule_head_name_node, "relation_name", 1)
        assert_correct_node(rule_head_term_list_node, "free_var_name_list")
        assert_correct_node(rule_body_relation_list_node, "rule_body_relation_list")
        rule_body_relations = rule_body_relation_list_node.children
        free_var_to_type = dict()
        conflicted_free_vars = dict()
        improperly_typed_relation_idxs = list()
        # The actual type checking. Look for conflicting free variables and improperly typed relations
        for idx, relation_node in enumerate(rule_body_relations):
            if relation_node.data == "relation":
                assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
                relation_name_node = relation_node.children[0]
                term_list_node = relation_node.children[1]
                schema = self.__get_relation_schema(relation_name_node)
                if not self.__type_check_rule_body_term_list(term_list_node, schema,
                                                             free_var_to_type, conflicted_free_vars):
                    improperly_typed_relation_idxs.append(idx)
            elif relation_node.data == "func_ie_relation":
                assert_correct_node(relation_node, "func_ie_relation", 3, "function_name", "term_list", "term_list")
                # TODO
            else:
                assert_correct_node(relation_node, "rgx_ie_relation", 3, "term_list", "term_list", "var_name")
                # TODO

        if conflicted_free_vars:
            error = get_error_line_string(tree) + "the following free variables have conflicting types\n"
            for free_var in conflicted_free_vars:
                error += free_var + ": " + "{" + self.__get_type_list_string(conflicted_free_vars[free_var]) + "}\n"
            raise exceptions.FreeVariableTypeConflict(error)

        if improperly_typed_relation_idxs:
            error = get_error_line_string(tree) + "the following rule body relations are not properly typed:\n"
            for idx in improperly_typed_relation_idxs:
                relation_node = rule_body_relations[idx]
                error += "at index " + str(idx) + ":\n"
                if relation_node.data == "relation":
                    assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
                    relation_name_node = relation_node.children[0]
                    relation_term_types = self.__get_term_types_list(relation_node.children[1],
                                                                     free_var_mapping=free_var_to_type)
                    schema = self.__get_relation_schema(relation_name_node)
                    error += self.__get_schema_comparison_string(relation_name_node, schema, relation_term_types)
                elif relation_node.data == "func_ie_relation":
                    assert_correct_node(relation_node, "func_ie_relation", 3,
                                        "function_name", "term_list", "term_list")
                    # TODO
                else:
                    assert_correct_node(relation_node, "rgx_ie_relation", 3,
                                        "term_list", "term_list", "var_name")
                    # TODO
                error += "\n"
            raise exceptions.TermsNotProperlyTypedError(error)

        # no issues were found, add the new schema to the schema dict
        rule_head_schema = []
        for rule_head_term_node in rule_head_term_list_node.children:
            assert_correct_node(rule_head_term_node, "free_var_name", 1)
            free_var_name = rule_head_term_node.children[0]
            assert free_var_name in free_var_to_type
            var_type = free_var_to_type[free_var_name]
            rule_head_schema.append(var_type)
        rule_head_name = rule_head_name_node.children[0]
        self.relation_name_to_schema[rule_head_name] = rule_head_schema


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
        parser = Lark(grammar, parser='lalr', debug=True, propagate_positions=True)

        test_input = open("test_input2").read()
        parse_tree = parser.parse(test_input)
        parse_tree = RemoveTokensTransformer().transform(parse_tree)
        parse_tree = StringVisitor().visit(parse_tree)
        CheckReferencedVariablesInterpreter().visit(parse_tree)
        CheckReferencedRelationsInterpreter().visit(parse_tree)
        CheckRuleSafetyVisitor().visit(parse_tree)
        TypeCheckingInterpreter().visit(parse_tree)
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
