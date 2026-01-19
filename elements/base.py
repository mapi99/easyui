class BaseElement:
    def __init__(self, label=None):
        self.label = label
        self.widget = None

    def render(self, parent):
        raise NotImplementedError("render() must be implemented in subclass")
