import terminal
import log

# TODO Refactor print logic out of this so the objects
# created are separate from print logic.
class QueryRunner(object):
    def __init__(self, test_schedule):
        self.schedule = test_schedule

    def list_tests(self):
        log.test_log.message(terminal.separator())
        log.test_log.message('Listing all Test Cases.', bold=True)
        log.test_log.message(terminal.separator())
        for suite in self.schedule:
            for test in suite:
                log.test_log.message(test.uid)

    def list_suites(self):
        log.test_log.message(terminal.separator())
        log.test_log.message('Listing all Test Suites.', bold=True)
        log.test_log.message(terminal.separator())
        for suite in self.schedule:
            log.test_log.message(suite.uid)

    def list_tags(self):
        #TODO In Gem5 override this with tag types (isa,variant,length)

        log.test_log.message(terminal.separator())
        log.test_log.message('Listing all Test Tags.', bold=True)
        log.test_log.message(terminal.separator())
        tags = set()
        for suite in self.schedule:
            tags = tags | set(suite.tags)
        for tag in tags:
            log.test_log.message(tag)