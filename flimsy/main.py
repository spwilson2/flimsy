import runner
import config
import loader as loader_mod
import fixture as fixture_mod
import log
import handlers

def filter_with_config_tags(loaded_library):
    tags = getattr(config.config, config.StorePositionalTagsAction.position_kword)
    return filter_with_tags(loaded_library, tags)

def filter_with_tags(loaded_library, filters):
    if not filters:
        return
    #FIXME logic seems to be broken.
    def apply_tag_filter(include, regex, suite):
        for tag in suite.tags:
            if regex.search(tag):
                return include
        return not include
    
    remaining_suites = iter(loaded_library)
    for include, regex in filters:
        remaining_suites = (suite for suite in remaining_suites 
                            if apply_tag_filter(include, regex, suite))

    loaded_library.suites = list(remaining_suites)

# TODO Add results command for listing previous results.
# TODO Add rerun command to re-run failed tests.

def do_list():
    testloader = loader_mod.Loader()
    testloader.load_root(config.config.directory)
    test_schedule = testloader.schedule
    filter_with_config_tags(test_schedule)
    for suite in test_schedule:
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

    # Initialize early parts of the log.
    term_handler = handlers.TerminalHandler(
        stream=config.config.stream,
        verbosity=config.config.verbose+log.LogLevel.Info
    )
    summary_handler = handlers.SummaryHandler()
    mp_handler = handlers.MultiprocessingHandlerWrapper(summary_handler, term_handler)
    mp_handler.async_process()
    log.test_log.log_obj.add_handler(mp_handler)

    testloader = loader_mod.Loader()
    testloader.load_root(config.config.directory)
    test_schedule = testloader.schedule

    # Filter tests based on tags
    # FIXME
    filter_with_config_tags(test_schedule)

    # Create the result handler object.
    result_handler = handlers.ResultHandler(test_schedule, config.config.result_path)
    mp_handler.add_handler(result_handler)

    # Iterate through all fixtures notifying them of the test schedule.
    for fixture in test_schedule.all_fixtures():
        fixture.schedule_finalized(test_schedule)

    # Build global fixtures and exectute scheduled test suites.
    library_runner = runner.LibraryRunner(test_schedule)
    library_runner.run()

def main():
    config.initialize_config()

    # 'do' the given command.
    globals()['do_'+config.config.command]()
    log.test_log.close()