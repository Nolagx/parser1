from abc import ABC, abstractmethod
import networkx as nx
from term_graph import NetxTermGraph



class ExecutionBase(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def execute(self, term_graph, engine):
        pass


class NetworkxGraphExecution(ExecutionBase):

    def __init__(self):
        super().__init__()

    def execute(self, term_graph : NetxTermGraph, engine):
