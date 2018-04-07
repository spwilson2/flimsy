# TODO: Enum of test states
NotRun, Passed, Failed, Skipped = range(4)


class TestCase(object):
    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        self.name = name
        self.parameterize(*args, **kwargs)
        self.status = NotRun
    
    def parameterize(self):
        pass