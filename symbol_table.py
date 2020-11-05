from abc import ABC, abstractmethod


class SymbolTableBase(ABC):
    @abstractmethod
    def set_var_type_and_value(self, var_name, var_type, var_value):
        pass

    @abstractmethod
    def get_variable_value(self, name):
        pass

    @abstractmethod
    def get_variable_type(self, name):
        pass

    @abstractmethod
    def remove_variable(self, name):
        pass

    @abstractmethod
    def get_all_variables(self):
        pass

    @abstractmethod
    def contains_var(self, var_name):
        pass

    def __repr__(self):
        print(self.get_all_variables())

    def __str__(self):
        ret = 'Variable\tType\tValue'
        for name, var_type, var_value in self.get_all_variables():
            ret += f'\n{name}\t{var_type}\t{var_value}'
        return ret


class SymbolTable(SymbolTableBase):
    def __init__(self):
        self._var_to_value = {}
        self._var_to_type = {}

    def set_var_type_and_value(self, var_name, var_type, var_value):
        self._var_to_type[var_name] = var_type
        self._var_to_value[var_name] = var_value

    def remove_variable(self, name):
        del self._var_to_type[name]
        del self._var_to_value[name]

    def get_variable_type(self, name):
        return self._var_to_type[name]

    def get_variable_value(self, name):
        return self._var_to_value[name]

    def get_all_variables(self):
        ret = []
        for var_name in self._var_to_type.keys():
            var_type = self._var_to_type[var_name]
            var_value = self._var_to_value[var_name]
            ret.append((var_name, var_type, var_value))
        return ret

    def contains_var(self, var_name):
        return var_name in self._var_to_value
