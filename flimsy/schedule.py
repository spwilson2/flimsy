import itertools

class TestSchedule(object):
    def __init__(self, suites, global_fixtures=tuple()):
        # Query all fixtures that will be built
        # Query all suites and their tests
        self.suites = suites
        self.global_fixtures = global_fixtures
        self.name = 'Entire Test Collection'
    
    def all_fixtures(self):
        return itertools.chain(
            self.global_fixtures,
            *(self.suite_fixtures(suite) for suite in self.suites)
        )

    def suite_fixtures(self, suite):
        return itertools.chain(*(test.fixtures for test in suite))
    
    @property
    def fixtures(self):
        return self.all_fixtures()
    
    @property
    def metadata(self):
        return {
            'uid': self.name,
            'name': self.name,
        }