import re
from abc import abstractmethod, ABC
from datatypes import DataTypes


class IEFunctionData(ABC):
    """
    A class that contains all the functions that provide data
    needed for using a single information extraction function
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    @abstractmethod
    def ie_function(*args):
        """The actual ie function that will be used"""
        pass

    @staticmethod
    @abstractmethod
    def get_input_types():
        """returns an iterable of the input types to the function"""
        pass

    @staticmethod
    @abstractmethod
    def get_output_types(*args):
        """
        returns an iterable of the output types to the function.
        args are the same arguments that will be passed to ie_function
        """
        pass


class RGX(IEFunctionData):

    def __init__(self):
        super().__init__()

    @staticmethod
    def ie_function(text, regex_formula):
        compiled_rgx = re.compile(regex_formula)
        num_groups = compiled_rgx.groups
        ret = []
        for match in re.finditer(compiled_rgx, text):
            cur_tuple = []
            if num_groups == 0:
                cur_tuple.append(match.span())
            else:
                for i in range(1, num_groups + 1):
                    cur_tuple.append(match.span(i))
            ret.append(cur_tuple)
        return ret

    @staticmethod
    def get_input_types():
        return DataTypes.STRING, DataTypes.STRING

    @staticmethod
    def get_output_types(text, regex_formula):
        compiled_rgx = re.compile(regex_formula)
        num_spans = compiled_rgx.groups
        if num_spans == 0:
            num_spans = 1
        return tuple([DataTypes.SPAN] * num_spans)


class RGXString(IEFunctionData):

    def __init__(self):
        super().__init__()

    @staticmethod
    def ie_function(text, regex_formula):
        compiled_rgx = re.compile(regex_formula)
        num_groups = compiled_rgx.groups
        ret = []
        for match in re.finditer(compiled_rgx, text):
            cur_tuple = []
            if num_groups == 0:
                cur_tuple.append(match.group())
            else:
                for i in range(1, num_groups + 1):
                    cur_tuple.append(match.group(i))
            ret.append(cur_tuple)
        return ret

    @staticmethod
    def get_input_types():
        return DataTypes.STRING, DataTypes.STRING

    @staticmethod
    def get_output_types(text, regex_formula):
        compiled_rgx = re.compile(regex_formula)
        num_strings = compiled_rgx.groups
        if num_strings == 0:
            num_strings = 1
        return tuple([DataTypes.STRING] * num_strings)
