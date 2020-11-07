from enum import Enum


class DataTypes(Enum):
    STRING = 0
    SPAN = 1
    INT = 2
    FREE_VAR = 3


def get_datatype_string(datatype_enum):
    if datatype_enum == DataTypes.STRING:
        return "string"
    elif datatype_enum == DataTypes.SPAN:
        return "span"
    elif datatype_enum == DataTypes.INT:
        return "integer"
    elif datatype_enum == DataTypes.FREE_VAR:
        return "free_var_name"
    else:
        raise Exception("invalid datatype enum")


def get_datatype_enum(datatype_string):
    if datatype_string == "string":
        return DataTypes.STRING
    elif datatype_string == "span":
        return DataTypes.SPAN
    elif datatype_string == "integer":
        return DataTypes.INT
    elif datatype_string == "free_var_name":
        return DataTypes.FREE_VAR
    else:
        raise Exception("invalid datatype string")
