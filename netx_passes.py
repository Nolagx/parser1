import networkx as nx
from custom_trees import NetxTree
from abc import ABC, abstractmethod
from term_graph import NetxTermGraph, EvalState
from symbol_table import SymbolTable
from complex_values import Span, Relation, RelationDeclaration, IERelation
from datatypes import DataTypes, get_datatype_string, get_datatype_enum


# TODO remove data_attr and the likes (can cause bugs)
# TODO check if the dfs commands are okay

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
        for node in nx.dfs_postorder_nodes(netx_tree, source=netx_tree.get_root()):
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
            if data_attr[node] == "assignment":
                value_node_type = data_attr[successors[1]]
                assert_correct_node(netx_tree, node, "assignment", 2, "var_name", value_node_type)
                left_var_name = netx_tree.get_node_value(successors[0])
                if value_node_type == "var_name":
                    right_var_name = netx_tree.get_node_value(successors[1])
                    assigned_value = symbol_table.get_variable_value(right_var_name)
                    assigned_type = symbol_table.get_variable_type(right_var_name)
                else:
                    value_node = list(netx_tree.successors(successors[1]))[0]
                    assigned_value = netx_tree.nodes[value_node]['value']
                    assigned_type = get_datatype_enum(value_node_type)
                symbol_table.set_variable_type(left_var_name, assigned_type)
                symbol_table.set_variable_value(left_var_name, assigned_value)
            if data_attr[node] == "read_assignment":
                # TODO
                pass
            if data_attr[node] in ["term_list", "const_term_list"]:
                for term_node in list(netx_tree.successors(node)):
                    if data_attr[term_node] == "var_name":
                        assert_correct_node(netx_tree, term_node, "var_name", 1)
                        var_name = netx_tree.get_node_value(term_node)
                        var_type = symbol_table.get_variable_type(var_name)
                        var_value = symbol_table.get_variable_value(var_name)
                        netx_tree.nodes[term_node]['data'] = get_datatype_string(var_type)
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

    @staticmethod
    def __get_term_value_list(netx_tree: NetxTree, term_nodes):
        values = []
        for term_node in term_nodes:
            values.append(netx_tree.get_node_value(term_node))
        return values

    @staticmethod
    def __get_term_type_list(netx_tree: NetxTree, term_nodes):
        types = []
        for term_node in term_nodes:
            node_type = netx_tree.nodes[term_node]['data']
            types.append(get_datatype_enum(node_type))
        return types

    def visit(self, netx_tree: NetxTree):
        data_attr = nx.get_node_attributes(netx_tree, "data")
        nodes_to_remove = list()
        for node in nx.dfs_preorder_nodes(netx_tree, source=netx_tree.get_root()):
            if node not in data_attr:
                continue
            successors = list(netx_tree.successors(node))
            if data_attr[node] in ["relation", "add_fact", "remove_fact", "rule_head"]:
                relation_name = netx_tree.get_node_value(successors[0])
                term_list_nodes = list(netx_tree.successors(successors[1]))
                term_values = self.__get_term_value_list(netx_tree, term_list_nodes)
                term_types = self.__get_term_type_list(netx_tree, term_list_nodes)
                relation_value = Relation(relation_name, term_values, term_types)
                netx_tree.nodes[successors[0]].clear()
                netx_tree.nodes[successors[0]]['value'] = relation_value
                nodes_to_remove.append(successors[1])
                nodes_to_remove.extend(term_list_nodes[1:])
            elif data_attr[node] == "ie_relation":
                assert_correct_node(netx_tree, node, "ie_relation", 3, "relation_name", "term_list", "term_list")
                relation_name = netx_tree.get_node_value(successors[0])
                input_term_nodes = list(netx_tree.successors(successors[1]))
                output_term_nodes = list(netx_tree.successors(successors[2]))
                input_term_values = self.__get_term_value_list(netx_tree, input_term_nodes)
                output_term_values = self.__get_term_value_list(netx_tree, output_term_nodes)
                input_term_types = self.__get_term_type_list(netx_tree, input_term_nodes)
                output_term_types = self.__get_term_type_list(netx_tree, output_term_nodes)
                relation_value = IERelation(relation_name, input_term_values, output_term_values,
                                            input_term_types, output_term_types)
                netx_tree.nodes[successors[0]].clear()
                netx_tree.nodes[successors[0]]['value'] = relation_value
                nodes_to_remove.extend(successors[1:])
                nodes_to_remove.extend(input_term_nodes)
                nodes_to_remove.extend(output_term_nodes)
            elif data_attr[node] == "relation_declaration":
                assert_correct_node(netx_tree, node, "relation_declaration", 2, "relation_name", "decl_term_list")
                relation_name = netx_tree.get_node_value(successors[0])
                schema_nodes = list(netx_tree.successors(successors[1]))
                relation_schema = []
                for schema_node in schema_nodes:
                    schema_node_type = netx_tree.nodes[schema_node]['data']
                    if schema_node_type == "decl_string":
                        relation_schema.append(DataTypes.STRING)
                    elif schema_node_type == "decl_span":
                        relation_schema.append(DataTypes.SPAN)
                    elif schema_node_type == "decl_int":
                        relation_schema.append(DataTypes.INT)
                    else:
                        assert 0
                netx_tree.nodes[successors[0]].clear()
                netx_tree.nodes[successors[0]]['value'] = RelationDeclaration(relation_name, relation_schema)
                nodes_to_remove.append(successors[1])
                nodes_to_remove.extend(schema_nodes)

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
            if node_type in ["add_fact", "remove_fact", "relation_declaration"]:
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
