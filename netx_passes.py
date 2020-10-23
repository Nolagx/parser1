import networkx as nx
from custom_trees import NetxTree
from abc import ABC, abstractmethod
from term_graph import TermGraph, EvalState
from symbol_table import SymbolTable


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
    def visit(self, netx_tree: NetxTree, term_graph: TermGraph, symbol_table: SymbolTable):
        pass


class AddNetxTreeToTermGraphPass(NetxEnginePass):

    def __init__(self):
        super().__init__()
        self.term_graph_root = None

    def __add_const_assignment(self, netx_assignment_node, netx_tree: NetxTree, term_graph: TermGraph,
                               symbol_table: SymbolTable):
        assert self.term_graph_root is not None
        successors = list(netx_tree.successors(netx_assignment_node))
        var_name = netx_tree.get_node_value(successors[0])
        value = netx_tree.get_node_value(successors[1])
        new_node = term_graph.add_term(type='assignment', debug=var_name)
        symbol_table.add_variable(var_name, new_node)
        term_graph.add_dependency(self.term_graph_root, new_node)
        value_node = term_graph.add_term(type='const', value=value, status=EvalState.COMPUTED)
        term_graph.add_dependency(new_node, value_node)

    def visit(self, netx_tree: NetxTree, term_graph: TermGraph, symbol_table: SymbolTable):
        data_attr = nx.get_node_attributes(netx_tree, "data")
        self.term_graph_root = term_graph.add_root(type='root')
        for node in nx.dfs_preorder_nodes(netx_tree):
            if node not in data_attr:
                continue
            successors = list(netx_tree.successors(node))
            if data_attr[node] == "assign_literal_string":
                assert_correct_node(netx_tree, node, "assign_literal_string", 2, "var_name", "string")
                self.__add_const_assignment(node, netx_tree, term_graph, symbol_table)
            if data_attr[node] == "assign_int":
                assert_correct_node(netx_tree, node, "assign_int", 2, "var_name", "integer")
                self.__add_const_assignment(node, netx_tree, term_graph, symbol_table)
            # if data_attr[node] == "assign_span":
            #     assert_correct_node(netx_tree, node, "assign_span", 2, "var_name", "span")
            #     self.__add_const_assignment(node, netx_tree, term_graph, symbol_table)
