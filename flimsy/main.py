import runner
import schedule
import config
import loader as loader_mod
import fixture as fixture_mod
import log
import handlers


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
    testloader.load_root(config.config.directory)
    for suite in filter_with_config_tags(testloader.suites):
        print(suite.uid)
        for test in suite:
            print('\t%s' % test.uid)

def do_run():
    '''
    Test Phases
    -----------
    * Test Collection
    * Fixture Parameterization
    * Global Fixture Setup
    * Iteratevely run suites:
       * Suite Fixture Setup
       * Iteratively run tests:
          * Test Fixture Setup
          * Run Test
          * Test Fixture Teardown
       * Suite Fixture Teardown
    * Global Fixture Teardown
    '''

    testloader = loader_mod.Loader()
    testloader.load_root(config.config.directory)

    # First pass through all the suites to create the test schedule object.
    test_schedule = filter_with_config_tags(testloader.suites)

    # Iterate through all fixtures notifying them of the test schedule.
    test_schedule = schedule.TestSchedule(test_schedule.suites, fixture_mod.global_fixtures)
    for fixture in test_schedule.all_fixtures():
        fixture.schedule_finalized(test_schedule)

    # Build global fixtures and exectute scheduled test suites.
    library_runner = runner.LibraryRunner(test_schedule)
    library_runner.execute()

def initialize_log(config):

    term_handler = handlers.TerminalHandler(
        stream=config.stream,
        verbosity=config.verbose+log.LogLevel.Info
    )
    result_handler = handlers.ResultHandler(config.result_path)
    summary_handler = handlers.SummaryHandler()
    mp_handler = handlers.MultiprocessingHandlerWrapper(result_handler, term_handler, summary_handler)
    mp_handler.async_process()
    log.test_log.log_obj.add_handler(mp_handler)

def main():
    config.initialize_config()
    initialize_log(config.config)

    # 'do' the given command.
    globals()['do_'+config.config.command]()
    log.test_log.close()