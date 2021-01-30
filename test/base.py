import os.path
import json

HERE = os.path.dirname(os.path.abspath(__file__))

class Expectation:

    def __init__(self, fname):
        self._name = os.path.join(HERE, "expectations", fname)

    @property
    def name(self):
        return os.path.normpath(self._name)

    @property
    def data(self):
        if os.path.isfile(self.name):
            with open(self.name, 'r+') as f:
                if self.name.endswith('.json'):  
                    return json.loads(f.read())
                return f.read()
        return None

    def write(self, actual):
        with open(self.name, 'w+') as f:
            if self.name.endswith('.json'):
                f.write(json.dumps(actual, indent=2, sort_keys=True))
            else:
                f.write(actual)
                