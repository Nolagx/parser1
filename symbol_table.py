from abc import ABC, abstractmethod
from datatypes import DataTypes, get_datatype_string


class SymbolTableBase(ABC):

    @abstractmethod
    def set_variable_type(self, var_name, var_type):
        pass

    @abstractmethod
    def get_variable_type(self, name):
        pass

    @abstractmethod
    def set_variable_value(self, var_name, var_value):
        pass

    @abstractmethod
    def get_variable_value(self, name):
        pass

    @abstractmethod
    def remove_variable(self, name):
        pass

    @abstractmethod
    def get_all_variables(self):
        pass

    @abstractmethod
    def contains_variable(self, var_name):
        pass

    @abstractmethod
    def set_relation_schema(self, name, schema):
        pass

    @abstractmethod
    def get_relation_schema(self, name):
        pass

    @abstractmethod
    def get_all_relations(self):
        pass

    @abstractmethod
    def set_ie_func_input_types(self, name, types):
        pass

    @abstractmethod
    def get_ie_func_input_types(self, name):
        pass

    @abstractmethod
    def set_ie_func_output_types(self, name, types):
        pass

    @abstractmethod
    def set_ie_func_output_types_compute_func(self, name, func):
        pass

    @abstractmethod
    def get_ie_func_output_types(self, name):
        pass

    @abstractmethod
    def add_ie_function(self, name, func):
        pass

    @abstractmethod
    def get_ie_function(self, name):
        pass

    @abstractmethod
    def contains_ie_function(self, name):
        pass

    def __repr__(self):
        # TODO
        pass

    def __str__(self):
        ret = 'Variable\tType\tValue'
        for name, var_type, var_value in self.get_all_variables():
            ret += f'\n{name}\t{get_datatype_string(var_type)}\t{var_value}'
        ret += '\nRelation\tSchema'
        for relation, schema in self.get_all_relations():
            # ret += f'\n{relation}\t{schema}'
            ret += f'\n{relation}\t('
            for idx, term_type in enumerate(schema):
                ret += get_datatype_string(term_type)
                if idx < len(schema) - 1:
                    ret += ", "
            ret += ")"
        return ret


class SymbolTable(SymbolTableBase):
    def __init__(self):
        self._var_to_value = {}
        self._var_to_type = {}
        self._relation_to_schema = {}
        self._ie_func_to_input_types = {}
        self._ie_func_to_output_types = {}
        self._ie_func_to_output_types_compute_func = {}
        self._ie_funcs = {}

    def set_variable_type(self, var_name, var_type):
        self._var_to_type[var_name] = var_type

    def get_variable_type(self, name):
        return self._var_to_type[name]

    def set_variable_value(self, var_name, var_value):
        self._var_to_value[var_name] = var_value

    def get_variable_value(self, name):
        return self._var_to_value[name]

    def remove_variable(self, name):
        del self._var_to_type[name]
        del self._var_to_value[name]

    def get_all_variables(self):
        ret = []
        for var_name in self._var_to_type.keys():
            var_type = self._var_to_type[var_name]
            var_value = self._var_to_value[var_name]
            ret.append((var_name, var_type, var_value))
        return ret

    def contains_variable(self, var_name):
        return var_name in self._var_to_value or var_name in self._var_to_type

    def set_relation_schema(self, name, schema):
        self._relation_to_schema[name] = schema

    def get_relation_schema(self, name):
        return self._relation_to_schema[name]

    def get_all_relations(self):
        return ((relation, schema) for relation, schema in self._relation_to_schema.items())

    def set_ie_func_input_types(self, name, types):
        self._ie_func_to_input_types[name] = types

    def get_ie_func_input_types(self, name):
        return self._ie_func_to_input_types[name]

    def set_ie_func_output_types(self, name, types):
        self._ie_func_to_output_types[name] = types

    def set_ie_func_output_types_compute_func(self, name, func):
        self._ie_func_to_output_types_compute_func[name] = func

    def get_ie_func_output_types(self, name):
        if name in self._ie_func_to_output_types:
            return self._ie_func_to_output_types[name]
        else:
            input_types = self._ie_func_to_input_types[name]
            compute_func = self._ie_func_to_output_types_compute_func[name]
            return compute_func(input_types)

    def add_ie_function(self, name, func):
        self._ie_funcs[name] = func

    def get_ie_function(self, name):
        return self._ie_funcs[name]

    def contains_ie_function(self, name):
        return name in self._ie_funcs
