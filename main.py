from graph_converters import Converter
import graph_converters
import lark_passes
import netx_passes
from lark import Lark, Transformer, Visitor
from lark.visitors import Interpreter, Visitor_Recursive
import networkx as nx
from symbol_table import SymbolTable
from term_graph import NetxTermGraph
from networkx_viewer import Viewer
import execution

symbol_table = SymbolTable()
term_graph = NetxTermGraph()


def run_passes(tree, pass_list):
    """
    Runs the passes in pass_list on tree, one after another.
    """
    for cur_pass in pass_list:
        if issubclass(cur_pass, Visitor) or issubclass(cur_pass, Visitor_Recursive) or \
                issubclass(cur_pass, Interpreter):
            cur_pass(symbol_table=symbol_table, term_graph=term_graph).visit(tree)
        elif issubclass(cur_pass, Transformer):
            tree = cur_pass(symbol_table=symbol_table, term_graph=term_graph).transform(tree)
        elif issubclass(cur_pass, Converter):
            tree = cur_pass().convert(tree)
        else:
            assert 0
    return tree


def main():
    with open('grammar.lark', 'r') as grammar:
        # parser = Lark(grammar, parser='lalr', transformer=CalculateTree())
        # parser = Lark(grammar, parser='lalr', transformer=CalculateTree2())
        parser = Lark(grammar, parser='lalr', debug=True, propagate_positions=True)

        test_input = open("test_input2").read()
        test_input2 = open("test_input5").read()
        parse_tree = parser.parse(test_input)
        # parse_tree2 = parser.parse(test_input2)
        # test_tree = parse_tree.copy()

        passes = [
            lark_passes.RemoveTokensTransformer,
            lark_passes.StringVisitor,
            lark_passes.CheckReferencedVariablesInterpreter,
            lark_passes.CheckReservedRelationNames,
            lark_passes.CheckReferencedRelationsInterpreter,
            lark_passes.CheckRuleSafetyVisitor,
            lark_passes.TypeCheckingInterpreter,
            graph_converters.LarkTreeToNetxTreeConverter,
        ]
        parse_tree = run_passes(parse_tree, passes)
        # print(parse_tree.pretty_with_nodes())
        # for node in nx.dfs_preorder_nodes(parse_tree):
        #     print(node, end=" ")
        # print()
        # print("=========")
        netx_passes.ResolveVariablesPass().visit(parse_tree, term_graph, symbol_table)
        print(symbol_table)
        # print(parse_tree.pretty())
        netx_passes.SimplifyRelationsPass().visit(parse_tree)
        netx_passes.AddNetxTreeToTermGraphPass().visit(parse_tree, term_graph, symbol_table)

        execution_engine = execution.NetworkxExecution(execution.PydatalogEngine(), None)
        term_graph.transform_graph(execution_engine)

        # parse_tree2 = run_passes(parse_tree2, passes)
        # netx_passes.ResolveVariablesPass().visit(parse_tree2, term_graph, symbol_table)
        # netx_passes.SimplifyRelationsPass().visit(parse_tree2)
        # netx_passes.AddNetxTreeToTermGraphPass().visit(parse_tree2, term_graph, symbol_table)
        # term_graph.transform_graph(execution_engine)
        # ============================

        # print("=============\n", term_graph)
        # print(symbol_table)
        # print(parse_tree.pretty())
        # nx.draw(term_graph._g, with_labels=True, labels=labels)
        # app = Viewer(term_graph._g)
        # app.mainloop()
        # for node in term_graph._g:
        #     print(node, term_graph._g.nodes[node])
        # test_tree = lark_passes.RemoveTokensTransformer().transform(test_tree)
        # lark_passes.StringVisitor().visit(test_tree)
        # lark_passes.CheckReferencedVariablesInterpreter().visit(test_tree)
        # lark_passes.CheckReferencedRelationsInterpreter().visit(test_tree)
        # lark_passes.CheckRuleSafetyVisitor().visit(test_tree)
        # lark_passes.TypeCheckingInterpreter().visit(test_tree)
        # parse_tree = PyDatalogRepresentationVisitor().visit(parse_tree)
        # print("===================")
        # print(test_tree.pretty())
        # print(test_tree)
        # for child in test_tree.children:
        #     print(child)

        # non_empty_lines = (line for line in test_input.splitlines() if len(line))

        # for line in non_empty_lines:
        # print(line)
        # print(parser.parse(line))


if __name__ == "__main__":
    main()
