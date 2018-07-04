import traceback

import log
import helper

global_fixtures = []

class TestScheduleUnknown(Exception):
    pass
class SkipException(Exception):
    def __init__(self, fixture, testitem):
        self.fixture = fixture
        self.testitem = testitem

        self.msg = 'Skipping "%s", fixture "%s" setup failed.' % (
               testitem.name, fixture.name
        ) 
        super(SkipException, self).__init__(self.msg)

class BrokenFixtureException(Exception):
    def __init__(self, fixture, testitem, exception):
        self.fixture = fixture
        self.testitem = testitem
        self.exception = exception
        super(BrokenFixtureException, self).__init__()

class Fixture(object):
    collector = helper.InstanceCollector()

    def __new__(klass, *args, **kwargs):
        obj = super(Fixture, klass).__new__(klass, *args, **kwargs)
        Fixture.collector.collect(obj)
        return obj

    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        if name is not None:
            self.name = name
        self.init(*args, **kwargs)
            
    def skip(self, testitem):
        raise SkipException(self, testitem)

    def schedule_finalized(self, schedule):
        pass

    def init(self, *args, **kwargs):
        pass
    
    def setup(self, testitem):
        pass
    
    def teardown(self, testitem):
        pass


def globalfixture(fixture):
    '''Store the given fixture as a global fixture. Its setup() method 
    will be called before the first test is executed.
    '''
    global_fixtures.append(fixture)

class FixtureBuilder(object):
    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.built_fixtures = []

    def setup(self, testitem):
        for fixture in self.fixtures:
            # Mark as built before, so if the build fails 
            # we still try to tear it down.
            self.built_fixtures.append(fixture)
            try:
                fixture.setup(testitem)
            except SkipException:
                raise
            except Exception as e:
                exc = traceback.format_exc()
                msg = 'Exception raised while setting up fixture for %s' % testitem
                log.test_log.warn('%s\n%s' % (exc, msg))
                raise BrokenFixtureException(self, testitem, e)
        
    def teardown(self, testitem):
        for fixture in self.built_fixtures:
            try:
                fixture.teardown(testitem)
            except Exception:
                # Log exception but keep cleaning up.
                exc = traceback.format_exc()
                msg = 'Exception raised while tearing down fixture for %s' % testitem
                log.test_log.warn('%s\n%s' % (exc, msg))