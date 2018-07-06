import itertools

import state

class TestScheduleMetadata(object):
    def __init__(self, uid, name, suites):
        self.uid = uid
        self.name = name
        self.suites = suites

class TestSchedule(object):
    def __init__(self, suites, global_fixtures=tuple()):
        # Query all fixtures that will be built
        # Query all suites and their tests
        self.suites = suites
        self.global_fixtures = global_fixtures
        self.name = 'Entire Test Collection'
        self.status = state.State.NotRun
    
    def all_fixtures(self):
        return itertools.chain(
            self.global_fixtures,
            *(self.suite_fixtures(suite) for suite in self.suites)
        )

    def suite_fixtures(self, suite):
        return itertools.chain(*(test.fixtures for test in suite))
    
    @property
    def fixtures(self):
        return self.global_fixtures
    
    @property
    def metadata(self):
        return TestScheduleMetadata( **{
            'uid': self.name,
            'name': self.name,
            'suites': [suite.metadata for suite in self]
        })
    
    def __iter__(self):
        return iter(self.suites)