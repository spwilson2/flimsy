import flimsy

class BrokenFixtureException(Exception):
    pass

def create_fixture(method):
    class BrokenFixture(flimsy.Fixture):
        def setup(self, testitem):
            pass
        
        def teardown(self, testitem):
            pass

    fixture = BrokenFixture()
    setattr(fixture, method, _broken_method)
    return fixture


def _broken_method(*args, **kwargs):
    raise BrokenFixtureException()

class EmptyTestCase(flimsy.TestCase):
    def test(self, test_parameters):
        pass


broken_teardown = EmptyTestCase(name='Broken Fixture Teardown')
broken_teardown.fixtures.append(create_fixture('teardown'))

broken_setup = EmptyTestCase(name='Broken Fixture Setup')
broken_setup.fixtures.append(create_fixture('setup'))