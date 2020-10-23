class Span:
    """a representation of a span"""

    def __init__(self, left_num, right_num):
        self.left_num = left_num
        self.right_num = right_num

    def __repr__(self):
        print(self.__str__())

    def __str__(self):
        """for now we print it as a tuple because of pydatalog's limitations"""
        return "(" + str(self.left_num) + ", " + str(self.right_num) + ")"
