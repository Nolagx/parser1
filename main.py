from lark import Lark, Transformer, v_args

@v_args(inline=True)
class CalculateTree(Transformer):
    # noinspection PyUnresolvedReferences
    from operator import add, sub, mul, truediv as div, neg
    number = float

    def __init__(self):
        super().__init__()
        self.vars = {}

    def assign_var(self, name, value):
        self.vars[name] = value
        return value

    def var(self, name):
        return self.vars[name]


@v_args(inline=True)
class TestTransformer(Transformer):
    # get rid of "integer" in the tree
    integer = int
    # comment = lambda self: "comment"

def main():
    with open('grammar.lark', 'r') as grammar:
        # parser = Lark(grammar, parser='lalr', transformer=CalculateTree())
        # parser = Lark(grammar, parser='lalr', transformer=CalculateTree2())
        parser = Lark(grammar, parser='earley', debug=False)

        test_input = 'a = "some" # "dwqdwq" \n'
        test_input += 'a = b \n'
        test_input += 'b = read("path")\n'
        test_input += '#   b = #read("path")\n'
        test_input += 'b = read(c)\n'
        test_input += 'd = [1, 2)\n'
        test_input += 'new parent(str, spn, str, str)\n'
        test_input += 'cousin(x) <- parent("s", [1,2), x)\n'
        test_input += 'cousin(x, y, z) <- extract RGX<"regex">(x, y, z) from a\n'
        test_input += 'cousin(x, y, z) <- func<var>(x, y, z)\n'
        test_input += 'cousin(x, y, z) <- func<var>(x, y, z), parent("s", [1,2), x), ' \
                      'extract RGX<"regex">(x, y, z) from a\n'
        test_input += 'parent("bob", "greg")\n'
        test_input += 'parent(x, "greg", [10,13))\n'
        test_input += '?parent("bob", "greg")\n'
        test_input += '?parent(x, "greg", [10,13))\n'
        test_input += '?parent(x, "greg", [10,13))\n'

        # non_empty_lines = (line for line in test_input.splitlines() if len(line))

        # for line in non_empty_lines:
        #     # print(line)
        #     print(parser.parse(line))

        parse_tree = parser.parse(test_input)
        parse_tree = TestTransformer().transform(parse_tree)
        print(parse_tree.pretty())
        print(parse_tree)


if __name__ == "__main__":
    main()
