instances = []
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

class Fixture(object):
    def __new__(klass, *args, **kwargs):
        obj = super(Fixture, klass).__new__(klass, *args, **kwargs)
        instances.append(obj)
        return obj

    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        if name is not None:
            self.name = name
        self.__args = args
        self.__kwargs = kwargs
    
    def __parameterize(self):
        self.init(*self.__args, **self.__kwargs)
    
    @property
    def test_schedule(self):
        if self._test_schedule is None:
            raise TestScheduleUnknown('The test schedule is not avaiable yet.')
        return self._test_schedule

    @test_schedule.setter
    def test_schedule(self, schedule):
        self._test_schedule = schedule
        self.__parameterize()
    def skip(self, testitem):
        raise SkipException(self, testitem)

    def init(self):
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