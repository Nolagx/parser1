from lark import Lark, Transformer, v_args, Visitor, Tree
from lark.visitors import Interpreter, Visitor_Recursive
from datatypes import DataTypes, get_datatype_enum

NODES_OF_LIST_WITH_VAR_NAMES = {"term_list", "const_term_list"}
NODES_OF_LIST_WITH_RELATION_NODES = {"rule_body_relation_list"}
NODES_OF_LIST_WITH_FREE_VAR_NAMES = {"term_list", "free_var_name_list"}
NODES_OF_TERM_LISTS = {"term_list", "const_term_list"}
NODES_OF_RULE_BODY_TERM_LISTS = {"term_list"}
SCHEMA_DEFINING_NODES = {"decl_term_list", "free_var_name_list"}


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


@v_args(inline=False)
class RemoveTokensTransformer(Transformer):
    """
    transforms the lark tree by removing the redundant tokens.
    should be used before all the other passes as they assume no tokens exists
    """

    def __init__(self, **kw):
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


class StringVisitor(Visitor_Recursive):
    """
     Fixes the strings in the lark tree.
     Removes the line overflow escapes from strings
     """

    def __init__(self, **kw):
        super().__init__()

    def string(self, tree):
        tree.children[0] = tree.children[0].replace('\\\n', '')


class CheckReferencedVariablesInterpreter(Interpreter):
    """
    A lark tree semantic check.
    checks whether each variable reference refers to a defined variable.
    """

    def __init__(self, **kw):
        super().__init__()
        self.vars = set()
        self.symbol_table = kw['symbol_table']

    def __add_var_name_to_vars(self, var_name_node):
        assert_correct_node(var_name_node, "var_name", 1)
        var_name = var_name_node.children[0]
        self.vars.add(var_name)

    def __check_if_var_not_defined(self, var_name_node):
        assert_correct_node(var_name_node, "var_name", 1)
        var_name = var_name_node.children[0]
        if var_name not in self.vars and not self.symbol_table.contains_variable(var_name):
            raise Exception

    def __check_if_vars_in_list_not_defined(self, tree):
        assert tree.data in NODES_OF_LIST_WITH_VAR_NAMES
        for child in tree.children:
            if child.data == "var_name":
                self.__check_if_var_not_defined(child)

    def assignment(self, tree):
        value_type = tree.children[1].data
        assert_correct_node(tree, "assignment", 2, "var_name", value_type)
        if value_type == "var_name":
            self.__check_if_var_not_defined(tree.children[1])
        self.__add_var_name_to_vars(tree.children[0])

    def read_assignment(self, tree):
        value_type = tree.children[1].data
        assert_correct_node(tree, "read_assignment", 2, "var_name", value_type)
        if value_type == "var_name":
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

    def ie_relation(self, tree):
        assert_correct_node(tree, "ie_relation", 3, "relation_name", "term_list", "term_list")
        self.__check_if_vars_in_list_not_defined(tree.children[1])
        self.__check_if_vars_in_list_not_defined(tree.children[2])


class CheckFilesInterpreter(Interpreter):
    """
        A lark tree semantic check.
        checks for existence and access to external documents
        """

    def __init__(self, **kw):
        super().__init__()
        self.symbol_table = kw['symbol_table']
        self.var_name_to_value = dict()

    def assignment(self, tree):
        value_node = tree.children[1]
        value_type = value_node.data
        assert_correct_node(tree, "assignment", 2, "var_name", value_type)
        if value_type == "var_name":
            right_var_name = value_node.children[0]
            if self.symbol_table.contains_variable(right_var_name):
                value = self.symbol_table.get_variable_value(right_var_name)
            elif right_var_name in self.var_name_to_value:
                value = self.var_name_to_value[right_var_name]
            else:
                assert 0
        else:
            value = value_node.children[0]
        left_var_name = tree.children[0].children[0]
        self.var_name_to_value[left_var_name] = value

    def read_assignment(self, tree):
        read_param_node = tree.children[1]
        read_param_type = read_param_node.data
        assert_correct_node(tree, "read_assignment", 2, "var_name", read_param_type)
        assert_correct_node(read_param_node, read_param_type, 1)
        read_param = read_param_node.children[0]
        if read_param_type == "var_name":
            if read_param in self.var_name_to_value:
                read_param = self.var_name_to_value[read_param]
            elif self.symbol_table.contains_variable(read_param):
                read_param = self.symbol_table.get_variable_value(read_param)
            else:
                assert 0
        assert_correct_node(tree.children[0], "var_name", 1)
        left_var_name = tree.children[0].children[0]
        try:
            file = open(read_param, 'r')
            self.var_name_to_value[left_var_name] = file.read()
            file.close()
        except Exception:
            raise Exception("couldn't open file")


class CheckReservedRelationNames(Interpreter):
    def __init__(self, **kw):
        super().__init__()

    def relation_name(self, tree):
        assert_correct_node(tree, "relation_name", 1)
        name = tree.children[0]
        if name.startswith("__rgxlog__"):
            raise Exception


class CheckReferencedRelationsInterpreter(Interpreter):
    """
    A lark tree semantic check.
    checks whether each non ie relation reference refers to a defined relation.
    Also checks if the relation reference uses the correct arity.
    """

    def __init__(self, **kw):
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
            raise Exception
        arity = len(term_list_node.children)
        correct_arity = self.relation_name_to_arity[relation_name]
        if arity != correct_arity:
            raise Exception

    def __check_if_relation_already_defined(self, relation_name_node):
        assert_correct_node(relation_name_node, "relation_name", 1)
        relation_name = relation_name_node.children[0]
        if relation_name in self.relation_name_to_arity:
            raise Exception

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
        rule_head_node = tree.children[0]
        rule_body_node = tree.children[1]
        assert_correct_node(rule_head_node, "rule_head", 2, "relation_name", "free_var_name_list")
        assert_correct_node(rule_body_node, "rule_body", 1, "rule_body_relation_list")
        self.__check_if_relation_already_defined(rule_head_node.children[0])
        relation_list_node = rule_body_node.children[0]
        assert_correct_node(relation_list_node, "rule_body_relation_list")
        for relation_node in relation_list_node.children:
            if relation_node.data == "relation":
                assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
                self.__check_if_relation_not_defined(relation_node.children[0], relation_node.children[1])
        self.__add_relation_definition(rule_head_node.children[0], rule_head_node.children[1])


class CheckReferencedIERelationsVisitor(Visitor_Recursive):
    """
    A lark tree semantic check.
    checks whether each ie relation reference refers to a defined ie function.
    """

    def __init__(self, **kw):
        super().__init__()
        self.symbol_table = kw['symbol_table']

    def ie_relation(self, tree):
        assert_correct_node(tree, "ie_relation", 3, "relation_name", "term_list", "term_list")
        func_name_node = tree.children[0]
        assert_correct_node(func_name_node, "relation_name", 1)
        if not self.symbol_table.contains_ie_function(func_name_node.children[0]):
            raise Exception


class CheckRuleSafetyVisitor(Visitor_Recursive):
    """
    A lark tree semantic check.
    checks whether the rules in the programs are safe.

    For a rule to be safe, two conditions must apply:

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

    def __init__(self, **kw):
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
        elif relation_node.data == "ie_relation":
            assert_correct_node(relation_node, "ie_relation", 3, "relation_name", "term_list", "term_list")
            return self.__get_set_of_free_var_names(relation_node.children[1])
        else:
            assert 0

    def __get_set_of_output_free_var_names(self, relation_node):
        if relation_node.data == "relation":
            assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
            return self.__get_set_of_free_var_names(relation_node.children[1])
        elif relation_node.data == "ie_relation":
            assert_correct_node(relation_node, "ie_relation", 3, "relation_name", "term_list", "term_list")
            return self.__get_set_of_free_var_names(relation_node.children[2])
        else:
            assert 0

    def rule(self, tree):
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
            raise Exception
        # check that every relation in the rule body is safe
        # initialize assuming every relation is unsafe and every free variable is unbound
        safe_relation_indexes = set()
        bound_free_vars = set()
        found_safe_relation = True
        while len(safe_relation_indexes) != len(rule_body_relations) and found_safe_relation:
            found_safe_relation = False
            for idx, relation_node in enumerate(rule_body_relations):
                if idx not in safe_relation_indexes:
                    input_free_vars = self.__get_set_of_input_free_var_names(relation_node)
                    unbound_free_vars = input_free_vars.difference(bound_free_vars)
                    if not unbound_free_vars:
                        # relation is safe, mark all of its output variables as bound
                        found_safe_relation = True
                        output_free_vars = self.__get_set_of_output_free_var_names(relation_node)
                        bound_free_vars = bound_free_vars.union(output_free_vars)
                        safe_relation_indexes.add(idx)
        if len(safe_relation_indexes) != len(rule_body_relations):
            raise Exception


class ReorderRuleBodyVisitor(Visitor_Recursive):
    """
    Reorders each rule body so that each relation in the rule body has its input free variables bound by
    the relations to its right.
    """

    def __init__(self, **kw):
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
        elif relation_node.data == "ie_relation":
            assert_correct_node(relation_node, "ie_relation", 3, "relation_name", "term_list", "term_list")
            return self.__get_set_of_free_var_names(relation_node.children[1])
        else:
            assert 0

    def __get_set_of_output_free_var_names(self, relation_node):
        if relation_node.data == "relation":
            assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
            return self.__get_set_of_free_var_names(relation_node.children[1])
        elif relation_node.data == "ie_relation":
            assert_correct_node(relation_node, "ie_relation", 3, "relation_name", "term_list", "term_list")
            return self.__get_set_of_free_var_names(relation_node.children[2])
        else:
            assert 0

    def rule(self, tree):
        assert_correct_node(tree, "rule", 2, "rule_head", "rule_body")
        assert_correct_node(tree.children[1], "rule_body", 1, "rule_body_relation_list")
        rule_body_relation_list_node = tree.children[1].children[0]
        assert_correct_node(rule_body_relation_list_node, "rule_body_relation_list")
        rule_body_relations = rule_body_relation_list_node.children
        # initialize assuming every relation is unsafe and every free variable is unbound
        reordered_relations = []
        reordered_relations_idx = set()
        bound_free_vars = set()
        found_safe_relation = True
        while len(reordered_relations) != len(rule_body_relations) and found_safe_relation:
            found_safe_relation = False
            for idx, relation_node in enumerate(rule_body_relations):
                if idx not in reordered_relations_idx:
                    input_free_vars = self.__get_set_of_input_free_var_names(relation_node)
                    unbound_free_vars = input_free_vars.difference(bound_free_vars)
                    if not unbound_free_vars:
                        # relation is safe, mark all of its output variables as bound
                        found_safe_relation = True
                        output_free_vars = self.__get_set_of_output_free_var_names(relation_node)
                        bound_free_vars = bound_free_vars.union(output_free_vars)
                        reordered_relations_idx.add(idx)
                        reordered_relations.append(relation_node)
        if len(reordered_relations) != len(rule_body_relations):
            raise Exception
        rule_body_relation_list_node.children = reordered_relations


class TypeCheckingInterpreter(Interpreter):
    """
    A lark tree semantic check.
    Assumes that relations and ie relations references and correct arity were checked.
    Also assumes variable references were checked.

    performs the following checks:
    1. checks if relation references are properly typed.
    2. checks if ie relations are properly typed.
    3. checks if free variables in rules do not have conflicting types.

    example for the semantic check failing on check no. 3:
    new A(str)
    new B(int)
    C(X) <- A(X), B(X) # error since X is expected to be both an int and a string
    """

    def __init__(self, **kw):
        super().__init__()
        self.symbol_table = kw['symbol_table']

    def __add_var_type(self, var_name_node, var_type: DataTypes):
        assert_correct_node(var_name_node, "var_name", 1)
        var_name = var_name_node.children[0]
        self.symbol_table.set_variable_type(var_name, var_type)

    def __get_var_type(self, var_name_node):
        assert_correct_node(var_name_node, "var_name", 1)
        var_name = var_name_node.children[0]
        return self.symbol_table.get_variable_type(var_name)

    def __add_relation_schema(self, relation_name_node, relation_schema):
        assert_correct_node(relation_name_node, "relation_name", 1)
        relation_name = relation_name_node.children[0]
        self.symbol_table.set_relation_schema(relation_name, relation_schema)

    def __get_relation_schema(self, relation_name_node):
        assert_correct_node(relation_name_node, "relation_name", 1)
        relation_name = relation_name_node.children[0]
        return self.symbol_table.get_relation_schema(relation_name)

    def __get_const_value_type(self, const_term_node):
        term_type = const_term_node.data
        if term_type == "var_name":
            assert_correct_node(const_term_node, "var_name", 1)
            return self.__get_var_type(const_term_node)
        else:
            return get_datatype_enum(term_type)

    def __get_term_types_list(self, term_list_node: Tree, free_var_mapping: dict = None,
                              relation_name_node: Tree = None):
        """
        get a list of the term types. The optional variables determine what type is assigned to a free
        variable, one and only one of them should be used.
        :param term_list_node: node of a list of terms (e.g. terms used when declaring a fact).
        :param free_var_mapping: when encountering a free variable, get its type from this mapping.
        :param relation_name_node: when encountering a free variable, get its type from the schema of this relation.
        :return: a list of the term types nb 
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
                term_types.append(self.__get_const_value_type(term_node))
        return term_types

    def assignment(self, tree):
        assert_correct_node(tree, "assignment", 2, "var_name", tree.children[1].data)
        self.__add_var_type(tree.children[0], self.__get_const_value_type(tree.children[1]))

    def read_assignment(self, tree):
        assert_correct_node(tree, "read_assignment", 2, "var_name", tree.children[1].data)
        self.__add_var_type(tree.children[0], DataTypes.STRING)

    def relation_declaration(self, tree):
        assert_correct_node(tree, "relation_declaration", 2, "relation_name", "decl_term_list")
        decl_term_list_node = tree.children[1]
        assert_correct_node(decl_term_list_node, "decl_term_list")
        declared_schema = []
        for term_node in decl_term_list_node.children:
            if term_node.data == "decl_string":
                declared_schema.append(DataTypes.STRING)
            elif term_node.data == "decl_span":
                declared_schema.append(DataTypes.SPAN)
            elif term_node.data == "decl_int":
                declared_schema.append(DataTypes.INT)
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
            raise Exception

    def remove_fact(self, tree):
        assert_correct_node(tree, "remove_fact", 2, "relation_name", "const_term_list")
        relation_name_node = tree.children[0]
        term_list_node = tree.children[1]
        term_types = self.__get_term_types_list(term_list_node)
        schema = self.__get_relation_schema(relation_name_node)
        if schema != term_types:
            raise Exception

    def query(self, tree):
        assert_correct_node(tree, "query", 1, "relation")
        relation_node = tree.children[0]
        assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
        relation_name_node = relation_node.children[0]
        term_list_node = relation_node.children[1]
        term_types = self.__get_term_types_list(term_list_node, relation_name_node=relation_name_node)
        schema = self.__get_relation_schema(relation_name_node)
        if schema != term_types:
            raise Exception

    def __type_check_rule_body_term_list(self, term_list_node: Tree, correct_types: list,
                                         free_var_to_type: dict):
        """
        checks if a rule body relation is properly typed
        also checks for conflicting free variables
        :param term_list_node: the term list of a rule body relation
        :param correct_types: a list of the types that the terms in the term list should have
        :param free_var_to_type: a mapping of free variables to their type (those that are currently known)
        :return:
        """
        assert term_list_node.data in NODES_OF_RULE_BODY_TERM_LISTS
        assert len(term_list_node.children) == len(correct_types)
        for idx, term_node in enumerate(term_list_node.children):
            correct_type = correct_types[idx]
            if term_node.data == "free_var_name":
                assert_correct_node(term_node, "free_var_name", 1)
                free_var = term_node.children[0]
                if free_var in free_var_to_type:
                    # free var already has a type, make sure there's no conflict with the currently wanted type
                    free_var_type = free_var_to_type[free_var]
                    if free_var_type != correct_type:
                        # found a conflicted free var
                        raise Exception
                else:
                    # free var does not currently have a type, map it to the correct type
                    free_var_to_type[free_var] = correct_type
            else:
                term_type = self.__get_const_value_type(term_node)
                if term_type != correct_type:
                    # term is not properly typed
                    raise Exception

    def rule(self, tree):
        assert_correct_node(tree, "rule", 2, "rule_head", "rule_body")
        assert_correct_node(tree.children[0], "rule_head", 2, "relation_name", "free_var_name_list")
        assert_correct_node(tree.children[1], "rule_body", 1, "rule_body_relation_list")
        rule_head_name_node = tree.children[0].children[0]
        rule_head_term_list_node = tree.children[0].children[1]
        rule_body_relation_list_node = tree.children[1].children[0]
        assert_correct_node(rule_head_name_node, "relation_name", 1)
        assert_correct_node(rule_head_term_list_node, "free_var_name_list")
        assert_correct_node(rule_body_relation_list_node, "rule_body_relation_list")
        rule_body_relations = rule_body_relation_list_node.children
        free_var_to_type = dict()
        # Look for conflicting free variables and improperly typed relations
        for idx, relation_node in enumerate(rule_body_relations):
            if relation_node.data == "relation":
                assert_correct_node(relation_node, "relation", 2, "relation_name", "term_list")
                relation_name_node = relation_node.children[0]
                term_list_node = relation_node.children[1]
                schema = self.__get_relation_schema(relation_name_node)
                self.__type_check_rule_body_term_list(term_list_node, schema, free_var_to_type)
            elif relation_node.data == "ie_relation":
                assert_correct_node(relation_node, "ie_relation", 3, "relation_name", "term_list", "term_list")
                # TODO
            else:
                assert 0

        # no issues were found, add the new schema to the schema dict
        rule_head_schema = []
        for rule_head_term_node in rule_head_term_list_node.children:
            assert_correct_node(rule_head_term_node, "free_var_name", 1)
            free_var_name = rule_head_term_node.children[0]
            assert free_var_name in free_var_to_type
            var_type = free_var_to_type[free_var_name]
            rule_head_schema.append(var_type)
        self.__add_relation_schema(rule_head_name_node, rule_head_schema)
