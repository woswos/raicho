class MockState:
    def __init__(self, mode):
        self.mode = mode
        self.events = []

    def setting(self, _name):
        return self.mode

    def record(self, event):
        self.events.append(event)
