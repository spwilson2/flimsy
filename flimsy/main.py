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

class EntireTestCollection(object):
    name = 'Entire Test Collection'
    def __init__(self, suites):
        self.suites = suites
    def __iter__(self):
        return iter(self.suites)

def filter_with_config_tags(test_collection):
    tags = getattr(config.config, config.StorePositionalTagsAction.position_kword)
    return filter_with_tags(test_collection, tags)

def filter_with_tags(test_collection, filters):
    if not filters:
        return EntireTestCollection(test_collection)

    def apply_tag_filter(include, regex, suite):
        for tag in suite.tags:
            print tag
            if regex.search(tag):
                return include
        return not include
    
    remaining_suites = iter(test_collection)
    for include, regex in filters:
        remaining_suites = (suite for suite in remaining_suites 
                            if apply_tag_filter(include, regex, suite))

    return EntireTestCollection(list(remaining_suites))

# TODO Add results command for listing previous results.
# TODO Add rerun command to re-run failed tests.

def do_list():
    testloader = loader_mod.Loader()
    testloader.load_root('example')
    for suite in filter_with_tags(testloader.suites, config.config.tags):
        print(suite)

def do_run():    
    testloader = loader_mod.Loader()
    testloader.load_root('example')

    # First pass through all the suites to create the test schedule object.
    test_schedule = filter_with_config_tags(testloader.suites)

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
            fixture.setup(test_schedule)
    except fixture_mod.SkipException as e:
        print 'Skipping all suites, a global fixture raised a SkipException.'
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
    result_handler = handlers.ResultHandler()
    Log.add_handler(handlers.MultiprocessingHandlerWrapper(term_handler, result_handler, summary_handler))

def main():
    config.initialize_config()
    initialize_log(config.config)

    # 'do' the given command.
    globals()['do_'+config.config.command]()
    log.Log.close()