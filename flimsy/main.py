import runner
import config
import loader as loader_mod
import fixture as fixture_mod
import log
import handlers
import terminal
import query

def filter_with_config_tags(loaded_library):
    tags = getattr(config.config, config.StorePositionalTagsAction.position_kword)
    return filter_with_tags(loaded_library, tags)

def filter_with_tags(loaded_library, filters):
    '''
    Filter logic supports two filter types:
    --include-tags <regex>
    --exclude-tags <regex>

    The logic maintains a `set` of test suites. 

    If the regex provided with the `--include-tags` flag matches a tag of a suite, that suite will added to the set.
    If the regex provided with the `--exclude-tags` flag matches a tag of a suite, that suite will removed to the set.
    Suites can be added and removed multiple times.

    First Flag Special Case Logic:
    If include is the first flag, start with an empty set of suites.
    If exclude is the first flag, start with the set of all collected suites.


    Let's trace out the set as we go through the flags to clarify::

        # Say our collection of suites looks like this: set(suite_ARM64, suite_X86, suite_Other).
        # Additionally, we've passed the flags in the following order: --include-tags "ARM64"  --exclude-tags ".*" --include-tags "X86"
        
        # Process --include-tags "ARM64"
        set(suite_ARM64)    # Suite begins empty, but adds the ARM64 suite
        # Process --exclude-tags ".*"
        set()               # Removed all suites which have tags
        # Process --include-tags "X86"
        set(suite_X86)
    '''
    if not filters:
        return

    query_runner = query.QueryRunner(loaded_library)
    tags = query_runner.tags()

    if not filters[0].include:
        suites = set(query_runner.suites())
    else:
        suites = set()

    def exclude(excludes):
        return suites - excludes
    def include(includes):
        return suites | includes

    for tag_regex in filters:
        matched_tags = (tag for tag in tags if tag_regex.regex.search(tag))
        for tag in matched_tags:
            matched_suites = set(query_runner.suites_with_tag(tag))
            suites = include(matched_suites) if tag_regex.include else exclude(matched_suites)

    loaded_library.suites = list(suites)

# TODO Add results command for listing previous results.
# TODO Add rerun command to re-run failed tests.

def load_tests():
    '''
    Create a TestLoader and load tests for the directory given by the config.
    '''
    testloader = loader_mod.Loader()
    log.test_log.message(terminal.separator())
    log.test_log.message('Loading Tests', bold=True)
    testloader.load_root(config.config.directory)
    return testloader

def do_list():    
    term_handler = handlers.TerminalHandler(
        verbosity=config.config.verbose+log.LogLevel.Info
    )
    log.test_log.log_obj.add_handler(term_handler)

    test_schedule = load_tests().schedule
    filter_with_config_tags(test_schedule)

    qrunner = query.QueryRunner(test_schedule)

    if config.config.suites:
        qrunner.list_suites()
    elif config.config.tests:
        qrunner.list_tests()
    elif config.config.all_tags:
        qrunner.list_tags()
    else:
        qrunner.list_suites()
        qrunner.list_tests()
        qrunner.list_tags()


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

    test_schedule = load_tests().schedule

    # Filter tests based on tags
    filter_with_config_tags(test_schedule)

    result_path =config.config.result_path
    # Create the result handler object.
    result_handler = handlers.ResultHandler(test_schedule, result_path)
    mp_handler.add_handler(result_handler)

    # Iterate through all fixtures notifying them of the test schedule.
    for fixture in test_schedule.all_fixtures():
        fixture.schedule_finalized(test_schedule)

    log.test_log.message(terminal.separator())
    log.test_log.message('Running Tests from {} suites'
            .format(len(test_schedule.suites)), bold=True)
    log.test_log.message("Results will be stored in {}".format(result_path))
    log.test_log.message(terminal.separator())

    # Build global fixtures and exectute scheduled test suites.
    library_runner = runner.LibraryRunner(test_schedule)
    library_runner.run()


def main():
    config.initialize_config()

    # 'do' the given command.
    globals()['do_'+config.config.command]()
    log.test_log.close()


def entrypoint():
    main()


if __name__ == '__main__':
    entrypoint()