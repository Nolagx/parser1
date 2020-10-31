from abc import ABC, abstractmethod
import networkx as nx
from term_graph import EvalState
from complex_values import Relation, RelationDeclaration
from pyDatalog import pyDatalog


class DatalogEngineBase(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def declare_relation(self, declaration):
        pass

    @abstractmethod
    def add_fact(self, fact):
        pass

    @abstractmethod
    def remove_fact(self, fact):
        pass

    @abstractmethod
    def query(self, query):
        pass

    @abstractmethod
    def add_rule(self, rule_head, rule_body):
        pass

    @abstractmethod
    def get_temp_result(self, relation):
        pass

    @abstractmethod
    def remove_temp_result(self, relation):
        pass


class PydatalogEngine(DatalogEngineBase):

    def __init__(self):
        super().__init__()
        self.temp_relations = dict()
        self.new_temp_relation_idx = 0

    def declare_relation(self, declaration: RelationDeclaration):
        # add and remove a temporary fact to the relation that is declared, this creates an empty
        # relation in pyDatalog so it is allowed to be queried
        relation_name = declaration.name
        schema_length = len(declaration.schema)
        temp_fact = relation_name + "("
        for i in range(schema_length):
            temp_fact += "1"
            if i != schema_length - 1:
                temp_fact += ", "
        temp_fact += ")"
        pyDatalog.load("+" + temp_fact)
        pyDatalog.load("-" + temp_fact)

    def add_fact(self, fact: Relation):
        print("+" + fact.get_pydatalog_string())
        pyDatalog.load("+" + fact.get_pydatalog_string())

    def remove_fact(self, fact: Relation):
        print("-" + fact.get_pydatalog_string())
        pyDatalog.load("-" + fact.get_pydatalog_string())

    def query(self, query: Relation):
        print("print(" + query.get_pydatalog_string() + ")")
        pyDatalog.load("print(" + query.get_pydatalog_string() + ")")

    def add_rule(self, rule_head: Relation, rule_body):
        rule_string = rule_head.get_pydatalog_string() + " <= "
        for idx, rule_body_relation in enumerate(rule_body):
            rule_string += rule_body_relation.get_pydatalog_string()
            if idx < len(rule_body) - 1:
                rule_string += " & "
        print(rule_string)
        pyDatalog.load(rule_string)

    def get_temp_result(self, relation: Relation):
        # TODO enforce __rgxlog__{x} as a name that cannot be used by the user (x is any integer)
        temp_relation_name = "__rgxlog__" + str(self.new_temp_relation_idx)
        self.new_temp_relation_idx += 1
        temp_relation_terms = []
        for term in relation.terms:
            if isinstance(term, str) and term[0].isupper() and term[0] not in temp_relation_terms:
                # if the term is a free variable and is not in the temp relation terms already, add it as a term.
                temp_relation_terms.append(term)
        temp_relation = Relation(temp_relation_name, temp_relation_terms)
        # can_reach(X,Y) <= link(X,Y)
        pyDatalog.load(temp_relation.get_pydatalog_string() + " <= " + relation.get_pydatalog_string())
        print(temp_relation.get_pydatalog_string() + " <= " + relation.get_pydatalog_string())
        return temp_relation

    def remove_temp_result(self, relation: Relation):
        pass


class ExecutionBase(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def transform(self, term_graph, root_name):
        pass


class NetworkxExecution(ExecutionBase):

    def __init__(self, datalog_engine: DatalogEngineBase, regex_engine):
        super().__init__()
        self.datalog_engine = datalog_engine
        self.regex_engine = regex_engine

    def transform(self, term_graph: nx.OrderedDiGraph, root_name):
        for node in nx.dfs_postorder_nodes(term_graph, source=root_name):
            if 'state' not in term_graph.nodes[node] or term_graph.nodes[node]['state'] == EvalState.COMPUTED:
                continue
            successors = list(term_graph.successors(node))
            node_type = term_graph.nodes[node]['type']
            if node_type == "relation_declaration":
                self.datalog_engine.declare_relation(term_graph.nodes[node]['value'])
            if node_type == "add_fact":
                self.datalog_engine.add_fact(term_graph.nodes[node]['value'])
            elif node_type == "remove_fact":
                self.datalog_engine.remove_fact(term_graph.nodes[node]['value'])
            elif node_type == "query":
                self.datalog_engine.query(term_graph.nodes[node]['value'])
            if node_type == "rule":
                rule_head_node = successors[0]
                rule_body_node = successors[1]
                assert term_graph.nodes[rule_head_node]['type'] == 'rule_head'
                assert term_graph.nodes[rule_body_node]['type'] == 'rule_body'
                rule_body_relation_nodes = list(term_graph.successors(rule_body_node))
                temp_results = []
                for relation_node in rule_body_relation_nodes:
                    relation_value = term_graph.nodes[relation_node]['value']
                    term_graph.nodes[relation_node]['value'] = self.datalog_engine.get_temp_result(relation_value)
                    term_graph.nodes[relation_node]['state'] = EvalState.COMPUTED
                    temp_results.append(term_graph.nodes[relation_node]['value'])
                rule_head_value = term_graph.nodes[rule_head_node]['value']
                self.datalog_engine.add_rule(rule_head_value, temp_results)

            # TODO more accurate computed determination
            term_graph.nodes[node]['state'] = EvalState.COMPUTED
