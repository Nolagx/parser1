import networkx as nx
from custom_trees import NetxTree
from abc import ABC, abstractmethod
from term_graph import NetxTermGraph, EvalState
from symbol_table import SymbolTable
from complex_values import Span, Relation


def assert_correct_node(netx_tree: NetxTree, node, node_name, len_children=None, *children_names):
    nodes = netx_tree.nodes
    children = list(netx_tree.successors(node))
    assert nodes[node]['data'] == node_name, "bad node name: " + node_name + \
                                             "\n actual node name: " + nodes[node]['data']
    if len_children is not None:
        assert len(children) == len_children, \
            "bad children length: " + str(len_children) + "\n actual children length: " + str(len(children))
    if children_names is not None:
        for idx, name in enumerate(children_names):
            child_data = nodes[children[idx]]['data']
            assert child_data == name, \
                "bad child name at index " + str(idx) + ": " + name + \
                "\n actual child name: " + child_data


class NetxPass(ABC):
    """
    Abstract class networkx passes
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def visit(self, graph):
        pass


class NetxEnginePass(ABC):
    """
    Abstract class networkx passes
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def visit(self, netx_tree: NetxTree, term_graph: NetxTermGraph, symbol_table: SymbolTable):
        pass


class ResolveVariablesPass(NetxEnginePass):
    """
    This pass performs the variable assignments and replaces variable references with their values.
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def __get_span_value_of_node(netx_tree, symbol_table, span_node):
        # currently only supports spans with literal values
        assert_correct_node(netx_tree, span_node, "span", 2, "integer", "integer")
        successors = list(netx_tree.successors(span_node))
        assert_correct_node(netx_tree, successors[0], "integer")
        assert_correct_node(netx_tree, successors[1], "integer")
        left_num = netx_tree.get_node_value(successors[0])
        right_num = netx_tree.get_node_value(successors[1])
        return Span(left_num, right_num)

    def visit(self, netx_tree: NetxTree, term_graph: NetxTermGraph, symbol_table: SymbolTable):
        data_attr = nx.get_node_attributes(netx_tree, "data")
        nodes_to_remove = set()
        for node in nx.dfs_preorder_nodes(netx_tree, source=netx_tree.get_root()):
            if node not in data_attr:
                continue
            successors = list(netx_tree.successors(node))
            if data_attr[node] == "span":
                # convert span to a complex value, this is done here as span might contain variables in future updates
                assert_correct_node(netx_tree, node, "span", 2, "integer", "integer")
                span_value = self.__get_span_value_of_node(netx_tree, symbol_table, node)
                value_node = successors[0]
                netx_tree.nodes[value_node].clear()
                netx_tree.nodes[value_node]['value'] = span_value
                nodes_to_remove.add(successors[1])
            if data_attr[node] == "assign_literal_string":
                assert_correct_node(netx_tree, node, "assign_literal_string", 2, "var_name", "string")
                var_name = netx_tree.get_node_value(successors[0])
                var_value = netx_tree.get_node_value(successors[1])
                symbol_table.set_var_type_and_value(var_name, "string", var_value)
            if data_attr[node] == "assign_int":
                assert_correct_node(netx_tree, node, "assign_int", 2, "var_name", "integer")
                var_name = netx_tree.get_node_value(successors[0])
                var_value = netx_tree.get_node_value(successors[1])
                symbol_table.set_var_type_and_value(var_name, "integer", var_value)
            if data_attr[node] == "assign_span":
                assert_correct_node(netx_tree, node, "assign_span", 2, "var_name", "span")
                assert_correct_node(netx_tree, successors[1], "span", 2, "integer", "integer")
                var_name = netx_tree.get_node_value(successors[0])
                span_value = self.__get_span_value_of_node(netx_tree, symbol_table, successors[1])
                symbol_table.set_var_type_and_value(var_name, "span", span_value)
            if data_attr[node] == "assign_var":
                assert_correct_node(netx_tree, node, "assign_var", 2, "var_name", "var_name")
                left_var = netx_tree.get_node_value(successors[0])
                right_var = netx_tree.get_node_value(successors[1])
                var_type = symbol_table.get_variable_type(right_var)
                var_value = symbol_table.get_variable_value(right_var)
                symbol_table.set_var_type_and_value(left_var, var_type, var_value)
            # if data_attr[node] == "term_list" or data_attr[node] == "const_term_list":
            if data_attr[node] in ["term_list", "const_term_list"]:
                for term_node in list(netx_tree.successors(node)):
                    if data_attr[term_node] == "var_name":
                        assert_correct_node(netx_tree, term_node, "var_name", 1)
                        var_name = netx_tree.get_node_value(term_node)
                        var_type = symbol_table.get_variable_type(var_name)
                        var_value = symbol_table.get_variable_value(var_name)
                        netx_tree.nodes[term_node]['data'] = var_type
                        netx_tree.set_node_value(term_node, var_value)
            # TODO the from string from rgx_relation, depending on the syntax that is decided
        # can only remove nodes after the iteration
        for node in nodes_to_remove:
            netx_tree.remove_node(node)


class SimplifyRelationsPass(NetxPass):
    """
    this pass redefines each relation in the tree using classes from 'complex_values.py' file
    For example, a normal relation will be represented by a single node containing a complex_values.Relation
    instance as a value (instead of the default grammar representation that contains multiple nodes)
    """

    def __init__(self):
        super().__init__()

    def visit(self, netx_tree: NetxTree):
        # TODO ie_relations, rgx relations after syntax is decided
        data_attr = nx.get_node_attributes(netx_tree, "data")
        nodes_to_remove = list()
        for node in nx.dfs_preorder_nodes(netx_tree, source=netx_tree.get_root()):
            if node not in data_attr:
                continue
            successors = list(netx_tree.successors(node))
            if data_attr[node] in ["relation", "add_fact", "remove_fact", "rule_head"]:
                relation_name = netx_tree.get_node_value(successors[0])
                terms = []
                term_list_nodes = list(netx_tree.successors(successors[1]))
                for term_node in term_list_nodes:
                    terms.append(netx_tree.get_node_value(term_node))
                relation_value = Relation(relation_name, terms)
                netx_tree.nodes[successors[0]].clear()
                netx_tree.nodes[successors[0]]['value'] = relation_value
                nodes_to_remove.append(successors[1])
                nodes_to_remove.extend(term_list_nodes[1:])

        # can only remove nodes after the iteration
        for node in nodes_to_remove:
            netx_tree.remove_node(node)


class AddNetxTreeToTermGraphPass(NetxEnginePass):
    """Adds the input ast as a tree to the term graph forest"""

    def __init__(self):
        super().__init__()
        self.term_graph_root = None

    def visit(self, netx_tree: NetxTree, term_graph: NetxTermGraph, symbol_table: SymbolTable):
        data_attr = nx.get_node_attributes(netx_tree, "data")
        self.term_graph_root = term_graph.add_term(type='program_root')
        term_graph.add_dependency(term_graph.get_root(), self.term_graph_root)
        for node in nx.dfs_preorder_nodes(netx_tree, source=netx_tree.get_root()):
            if node not in data_attr:
                continue
            successors = list(netx_tree.successors(node))
            node_type = data_attr[node]
            if node_type in ["add_fact", "remove_fact"]:
                relation_value = netx_tree.get_node_value(node)
                new_node = term_graph.add_term(type=node_type, value=relation_value)
                term_graph.add_dependency(self.term_graph_root, new_node)
            if node_type == "query":
                relation_value = netx_tree.get_node_value(successors[0])
                new_node = term_graph.add_term(type=node_type, value=relation_value)
                term_graph.add_dependency(self.term_graph_root, new_node)
            if node_type == "rule":
                assert_correct_node(netx_tree, node, "rule", 2, "rule_head", "rule_body")
                new_rule_node = term_graph.add_term(type=node_type)
                rule_head_value = netx_tree.get_node_value(successors[0])
                new_rule_head_node = term_graph.add_term(type="rule_head", value=rule_head_value)
                new_rule_body_node = term_graph.add_term(type="rule_body")
                term_graph.add_dependency(self.term_graph_root, new_rule_node)
                term_graph.add_dependency(new_rule_node, new_rule_head_node)
                term_graph.add_dependency(new_rule_node, new_rule_body_node)
                rule_body_node = successors[1]
                assert_correct_node(netx_tree, rule_body_node, "rule_body", 1, "rule_body_relation_list")
                rule_body_relations_list_node = list(netx_tree.successors(rule_body_node))[0]
                assert_correct_node(netx_tree, rule_body_relations_list_node, "rule_body_relation_list")
                rule_body_relation_nodes = list(netx_tree.successors(rule_body_relations_list_node))
                for rule_body_relation_node in rule_body_relation_nodes:
                    rule_body_relation_type = data_attr[rule_body_relation_node]
                    rule_body_relation_value = netx_tree.get_node_value(rule_body_relation_node)
                    new_rule_body_relation_node = term_graph.add_term(type=rule_body_relation_type,
                                                                      value=rule_body_relation_value)
                    term_graph.add_dependency(new_rule_body_node, new_rule_body_relation_node)


# class AddNetxTreeToTermGraphPass(NetxEnginePass):
#
#     def __init__(self):
#         super().__init__()
#         self.term_graph_root = None
#
#     def __add_const_assignment(self, netx_assignment_node, netx_tree: NetxTree, term_graph: TermGraph,
#                                symbol_table: SymbolTable):
#         assert self.term_graph_root is not None
#         successors = list(netx_tree.successors(netx_assignment_node))
#         var_name = netx_tree.get_node_value(successors[0])
#         value = netx_tree.get_node_value(successors[1])
#         new_node = term_graph.add_term(type='assignment', debug=var_name)
#         # symbol_table.set_variable_value(var_name, new_node)
#         term_graph.add_dependency(self.term_graph_root, new_node)
#         value_node = term_graph.add_term(type='const', value=value, status=EvalState.COMPUTED)
#         term_graph.add_dependency(new_node, value_node)
#
#     def visit(self, netx_tree: NetxTree, term_graph: TermGraph, symbol_table: SymbolTable):
#         data_attr = nx.get_node_attributes(netx_tree, "data")
#         self.term_graph_root = term_graph.add_root(type='root')
#         for node in nx.dfs_preorder_nodes(netx_tree, source=netx_tree.get_root()):
#             if node not in data_attr:
#                 continue
#             successors = list(netx_tree.successors(node))
#             if data_attr[node] == "assign_literal_string":
#                 assert_correct_node(netx_tree, node, "assign_literal_string", 2, "var_name", "string")
#                 self.__add_const_assignment(node, netx_tree, term_graph, symbol_table)
#             if data_attr[node] == "assign_int":
#                 assert_correct_node(netx_tree, node, "assign_int", 2, "var_name", "integer")
#                 self.__add_const_assignment(node, netx_tree, term_graph, symbol_table)
#             # if data_attr[node] == "assign_span":
#             #     assert_correct_node(netx_tree, node, "assign_span", 2, "var_name", "span")
#             #     self.__add_const_assignment(node, netx_tree, term_graph, symbol_table)
