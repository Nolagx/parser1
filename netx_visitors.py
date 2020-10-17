import networkx as nx

class VisitorBase:
    def _call_userfunc(self, tree):
        return getattr(self, tree.data, self.__default__)(tree)

    def __default__(self, tree):
        "Default operation on tree (for override)"
        return tree

    def __class_getitem__(cls, _):
        return cls


class Visitor(VisitorBase):
    """Bottom-up visitor, non-recursive

    Visits the tree, starting with the leaves and finally the root (bottom-up)
    Calls its methods (provided by user via inheritance) according to tree.data
    """

    def visit(self, tree):
        for subtree in tree.iter_subtrees():
            self._call_userfunc(subtree)
        return tree

    def visit_topdown(self,tree):
        for subtree in tree.iter_subtrees_topdown():
            self._call_userfunc(subtree)
        return tree

class Visitor_Recursive(VisitorBase):
    """Bottom-up visitor, recursive

    Visits the tree, starting with the leaves and finally the root (bottom-up)
    Calls its methods (provided by user via inheritance) according to tree.data
    """

    def visit(self, tree):
        for child in tree.children:
            # if isinstance(child, Tree):
            #     self.visit(child)
            pass

        self._call_userfunc(tree)
        return tree

    def visit_topdown(self,tree):
        self._call_userfunc(tree)

        for child in tree.children:
            # if isinstance(child, Tree):
            #     self.visit_topdown(child)
            pass

        return tree