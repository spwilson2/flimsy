class TestSuite(object):
    def __init__(self, tests, name):
        self.name = name
        self.tests = tests
    
    def __iter__(self):
        return iter(self.tests)