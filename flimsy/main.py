import itertools

import config
import loader as loader_mod
import fixture as fixture_mod
import log
import handlers

# Test Phases:
# * Test Collection
#   * Test Parameterization (TODO Should this be moved to a separate step or kept here?)
# * Fixture Parameterization
# * Global Fixture Setup
# * Iteratevely run suites:
#    * Suite Fixture Setup
#    * Iteratively run tests:
#       * Test Fixture Setup
#       * Run Test
#       * Test Fixture Teardown
#    * Suite Fixture Teardown
# * Global Fixture Teardown


class TestItem(object):
    pass

class EntireTestCollection(TestItem):
    name = 'Entire Test Collection'
    def __init__(self, suites):
        self.suites = suites
    def __iter__(self):
        return iter(self.suites)

def dorun():    
    testloader = loader_mod.Loader()
    testloader.load_root('example')

    # TODO First pass through all the suites to create the test schedule object.

    test_schedule = EntireTestCollection(testloader.suites)

    # Iterate through all fixtures parameterizing them in order.
    fixtures = tuple()
    def extend_chain(*items):
        global fixtures
        fixtures = itertools.chain(*items)

    for suite in test_schedule:
        extend_chain(suite.fixtures)
        for test in suite:
            extend_chain(test.fixtures)
    extend_chain(fixture_mod.global_fixtures)
    for fixture in fixtures:
        fixture.test_schedule = test_schedule

    try:
        for fixture in fixture_mod.global_fixtures:
            # TODO Make a base testitem object, and create suite version of it.
            fixture.setup(test_schedule)
    except fixture_mod.SkipException as e:
        print 'Skipping all tests.'
        print e.msg
    else:
        # Run all suites.
        for suite in test_schedule:
            suite.runner(suite).run()


def initialize_log(config):
    Log = log.Log = log._Log()

    term_handler = handlers.TerminalHandler(
        stream=config.stream,
        verbosity=config.verbose+log.Level.Info
    )
    summary_handler = handlers.SummaryHandler()
    
    Log.add_handler(handlers.MultiprocessingHandlerWrapper(term_handler, summary_handler))

def main():
    config.initialize_config()
    initialize_log(config.config)

    # 'do' the given command.
    globals()['do'+config.config.command]()
    log.Log.close()