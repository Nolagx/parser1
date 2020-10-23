from abc import abstractmethod
import networkx as nx
from enum import Enum


class EvalState(Enum):
    NOT_COMPUTED = 0
    COMPUTED = 1
    DIRTY = 2


# TODO add nx to package deps


# TODO: i assume some optimizations would not occur on a single node but rather,
# TODO: they would happen on the entire term graph (global optimizations)
# TODO: what interface would be comfy for this purpose?
class TermGraphBase:
    @abstractmethod
    def add_term(self, data):
        pass

    @abstractmethod
    def remove_term(self, name):
        pass

    @abstractmethod
    def add_dependency(self, name1, name2, data):
        pass

    @abstractmethod
    def get_term_list(self):
        pass

    @abstractmethod
    def get_term_state(self, name):
        # for now, computed / not computed / dirty (?)
        pass

    @abstractmethod
    def get_term_data(self, name):
        # will be called to get an AST and send it to the execution engine
        # or get the result of a node's computation
        pass

    @abstractmethod
    def transform_term_data(self, name, transformer):
        pass

    @abstractmethod
    def transform_graph(self, transformer):
        pass

    # TODO
    def __repr__(self):
        pass

    # TODO
    def __str__(self):
        pass


class TermGraph(TermGraphBase):  # , MemoryHeap):
    def __init__(self):
        self._g = nx.Graph()
        self._new_node_id = 0
        self._roots = []

    def add_root(self, **attr):
        if 'status' not in attr:
            attr['status'] = EvalState.NOT_COMPUTED
        self._roots.append(self._new_node_id)
        self._g.add_node(node_for_adding=self._new_node_id, **attr)
        self._new_node_id += 1
        return self._new_node_id - 1

    def add_term(self, **attr):  # attr[state / data]
        if 'status' not in attr:
            attr['status'] = EvalState.NOT_COMPUTED
        self._g.add_node(node_for_adding=self._new_node_id, **attr)
        self._new_node_id += 1
        return self._new_node_id - 1

    def remove_term(self, name):
        self._g.remove_node(name)

    def add_dependency(self, name1, name2, **attr):
        assert name1 in self._g.nodes
        assert name2 in self._g.nodes
        self._g.add_edge(name1, name2, **attr)

    def get_term_list(self):
        # TODO
        pass

    def get_term_state(self, name):
        return self._g.nodes[name]['state']

    def get_term_data(self, name):
        return self._g.nodes[name]['data']

    def transform_term_data(self, name, transformer):
        return transformer(self._g.nodes[name])

    def transform_graph(self, transformer):
        return transformer(self._g)
