from abc import ABC, abstractmethod
import networkx as nx
from term_graph import EvalState
from complex_values import Relation, RelationDeclaration, IERelation
from pyDatalog import pyDatalog
from datatypes import DataTypes
from symbol_table import SymbolTable


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
    def compute_rule_body_relation(self, relation):
        pass

    @abstractmethod
    def compute_rule_body_ie_relation(self, ie_relation, ie_func, bounding_relation):
        """
        since ie relations may have input free variables, we need to use another relation to determine the inputs
        for ie_relation. Each free variable that appears as an ie_relation input term must appear at least once in the
        bounding_relation terms.
        :param ie_relation: a relation that determines the input and output terms of the ie function
        :param ie_func: the ie function
        :param bounding_relation: a relation that contains the inputs for ie_funcs. the actual input needs to be
        extracted from it
        :return: resulting relation
        """
        pass

    @abstractmethod
    def remove_temp_result(self, relation):
        pass


class PydatalogEngine(DatalogEngineBase):

    def __init__(self):
        super().__init__()
        self.temp_relations = dict()
        self.new_temp_relation_idx = 0

    def __get_new_temp_relation_name(self):
        temp_relation_name = "__rgxlog__" + str(self.new_temp_relation_idx)
        self.new_temp_relation_idx += 1
        return temp_relation_name

    def __extract_temp_relation(self, relations: list) -> Relation:
        """
        creates a new temp relation where each free variable that appears in relations, appears once in the new
        relation.
        for example: for input relation A(X,Y,X), B("b",3,W) we'll get some_temp(X,Y,W)
        """
        temp_relation_name = self.__get_new_temp_relation_name()
        temp_relation_terms = []
        for relation in relations:
            for idx, term in enumerate(relation.terms):
                if relation.term_types[idx] == DataTypes.FREE_VAR and term not in temp_relation_terms:
                    # if the term is a free variable and is not in the temp relation terms already, add it as a term.
                    temp_relation_terms.append(term)
        temp_relation_types = [DataTypes.FREE_VAR] * len(temp_relation_terms)
        return Relation(temp_relation_name, temp_relation_terms, temp_relation_types)

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

    def compute_rule_body_relation(self, relation: Relation):
        temp_relation = self.__extract_temp_relation([relation])
        pyDatalog.load(temp_relation.get_pydatalog_string() + " <= " + relation.get_pydatalog_string())
        print(temp_relation.get_pydatalog_string() + " <= " + relation.get_pydatalog_string())
        return temp_relation

    def compute_rule_body_ie_relation(self, ie_relation: IERelation, ie_func, bounding_relation: Relation):
        input_relation = Relation(self.__get_new_temp_relation_name(), ie_relation.input_terms,
                                  ie_relation.input_term_types)
        output_relation = Relation(self.__get_new_temp_relation_name(), ie_relation.output_terms,
                                   ie_relation.output_term_types)
        # extract the input into a temp input relation.
        self.add_rule(input_relation, [bounding_relation])
        # get a list of input tuples. to get them we query pyDatalog using the input relation name, and all
        # of the terms will be free variables (so we get the whole tuple)
        query_str = input_relation.name + "("
        for i in range(len(input_relation.terms)):
            query_str += "X" + str(i)
            if i < len(input_relation.terms) - 1:
                query_str += ","
        query_str += ")"
        ie_inputs = pyDatalog.ask(query_str).answers
        # get all the outputs
        ie_outputs = []
        for ie_input in ie_inputs:
            ie_outputs.extend(ie_func(*ie_input))
        # add the outputs to the output relation
        for ie_output in ie_outputs:
            # TODO get output term types
            output_fact = Relation(output_relation.name, ie_output, [DataTypes.STRING, DataTypes.STRING])
            self.add_fact(output_fact)
        # create the result relation. it's a temp relation that takes the bounding relation, input relation and
        # output relation into account. therefore it must have the free variables of all of the previously mentioned
        # relations.
        temp_rule_body_relations = [bounding_relation, input_relation, output_relation]
        result_relation = self.__extract_temp_relation(temp_rule_body_relations)
        self.add_rule(result_relation, temp_rule_body_relations)
        return result_relation

    def remove_temp_result(self, relation: Relation):
        """
        pydatalog saves the rules that we give it and uses them to compute later queries. That means
        we can't delete temporary relations, since we will effectively delete the relations that were computed from
        rules.
        """
        pass


class ExecutionBase(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def transform(self, term_graph, root_name):
        pass


class NetworkxExecution(ExecutionBase):

    def __init__(self, datalog_engine: DatalogEngineBase, symbol_table: SymbolTable):
        super().__init__()
        self.datalog_engine = datalog_engine
        self.symbol_table = symbol_table

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
                temp_result = None
                for relation_node in rule_body_relation_nodes:
                    relation_value = term_graph.nodes[relation_node]['value']
                    if term_graph.nodes[relation_node]['type'] == 'relation':
                        term_graph.nodes[relation_node]['value'] = self.datalog_engine.compute_rule_body_relation(
                            relation_value)
                        term_graph.nodes[relation_node]['state'] = EvalState.COMPUTED
                        temp_result = term_graph.nodes[relation_node]['value']
                    elif term_graph.nodes[relation_node]['type'] == 'ie_relation':
                        assert temp_result is not None
                        ie_func = self.symbol_table.get_ie_function(relation_value.name)
                        term_graph.nodes[relation_node]['value'] = self.datalog_engine.compute_rule_body_ie_relation(
                            relation_value, ie_func, temp_result)
                        temp_result = term_graph.nodes[relation_node]['value']
                    else:
                        assert 0
                rule_head_value = term_graph.nodes[rule_head_node]['value']
                self.datalog_engine.add_rule(rule_head_value, [temp_result])

            # TODO more accurate computed determination
            term_graph.nodes[node]['state'] = EvalState.COMPUTED
