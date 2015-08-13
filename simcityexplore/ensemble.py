import picas


class Ensemble(picas.Document):

    def __init__(self, name, parameter_specs):
        self.name = name
        self.specs = parameter_specs

    