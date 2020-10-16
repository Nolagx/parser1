from graph_converters import Converter
import graph_converters
import lark_passes
from lark import Lark, Transformer, Visitor
from lark.visitors import Interpreter, Visitor_Recursive


def run_passes(tree, pass_list):
    for cur_pass in pass_list:
        if issubclass(cur_pass, Visitor) or issubclass(cur_pass, Visitor_Recursive) or \
                issubclass(cur_pass, Interpreter):
            cur_pass().visit(tree)
        elif issubclass(cur_pass, Transformer):
            tree = cur_pass().transform(tree)
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
        parse_tree = parser.parse(test_input)
        test_tree = parse_tree.copy()

        passes = [
            lark_passes.RemoveTokensTransformer,
            lark_passes.StringVisitor,
            lark_passes.CheckReferencedVariablesInterpreter,
            lark_passes.CheckReferencedRelationsInterpreter,
            lark_passes.CheckRuleSafetyVisitor,
            lark_passes.TypeCheckingInterpreter,
            graph_converters.LarkTreeToNetxTreeConverter
        ]
        parse_tree = run_passes(parse_tree, passes)

        test_tree = lark_passes.RemoveTokensTransformer().transform(test_tree)
        lark_passes.StringVisitor().visit(test_tree)
        lark_passes.CheckReferencedVariablesInterpreter().visit(test_tree)
        lark_passes.CheckReferencedRelationsInterpreter().visit(test_tree)
        lark_passes.CheckRuleSafetyVisitor().visit(test_tree)
        lark_passes.TypeCheckingInterpreter().visit(test_tree)
        # parse_tree = PyDatalogRepresentationVisitor().visit(parse_tree)
        print("===================")
        print(test_tree.pretty())
        print(test_tree)
        for child in test_tree.children:
            print(child)

        non_empty_lines = (line for line in test_input.splitlines() if len(line))

        for line in non_empty_lines:
            # print(line)
            print(parser.parse(line))

        # TODO  =========== delete ============
        print("==========")
        test_tree = graph_converters.LarkTreeToNetxTreeConverter().convert(test_tree)
        print(test_tree.pretty())
        test_tree = graph_converters.NetxTreeToLarkTreeConverter().convert(test_tree)
        print(parse_tree)
        for child in parse_tree.children:
            print(child)
        print(test_tree.pretty())
        assert test_tree == parse_tree
        # TODO  =========== /delete ============
        print(parse_tree.pretty())


if __name__ == "__main__":
    main()
