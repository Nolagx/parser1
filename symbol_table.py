from abc import ABC, abstractmethod


class SymbolTableBase(ABC):
    @abstractmethod
    def add_variable(self, name, value):
        pass

    @abstractmethod
    def remove_variable(self, name):
        pass

    @abstractmethod
    def get_all_variables(self):
        pass

    @abstractmethod
    def get_variable_value(self, name):
        pass

    def __repr__(self):
        print(self.get_all_variables())

    def __str__(self):
        print('Variable\tValue')
        for name, value in self.get_all_variables():
            print(f'{name}\t{value}')


class SymbolTable(SymbolTableBase):
    def __init__(self):
        self._var_to_value = {}

    def add_variable(self, name, value):
        self._var_to_value[name] = value

    def remove_variable(self, name):
        del self._var_to_value[name]

    def get_variable_value(self, name):
        return self._var_to_value[name]

    def get_all_variables(self):
        return ((var, data) for var, data in self._var_to_value.items())
