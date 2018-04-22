from __future__ import print_function

import multiprocessing
import os
import pickle
import Queue
import sys
import threading
import time

from config import config
import helper
import log
import terminal
import test
import uid


def test_results_output_path(test_case):
    '''
    Return the path which results for a specific test case should be
    stored.
    '''
    return os.path.join(config.result_path, test_case.uid.replace('/','-'))

class TestResult(object):
    def __init__(self, test):
        self.test = test
        helper.mkdir_p(test_results_output_path(self.test))

        self.stdout_fname = os.path.join(test_results_output_path(self.test), 'stdout')
        self.stderr_fname = os.path.join(test_results_output_path(self.test), 'stderr')

        self.stdout = open(self.stdout_fname, 'w')
        self.stderr = open(self.stderr_fname, 'w')
    
    def write_stdout(self, buf):
        self.stdout.write(buf)
    
    def write_stderr(self, buf):
        self.stderr.write(buf)

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        self._result = value

class SavedResults():
    def __init__(self, results):
        self.results = results


class ResultHandler(log.Handler):
    def __init__(self):
        self.testresults = {}
        self.suiteresults = []
        self.mapping = {
            log.SuiteResult: self.handle_suiteresult,
            log.TestResult: self.handle_testresult,
            log.TestStderr: self.handle_stderr,
            log.TestStdout: self.handle_stdout,
        }

    def handle(self, record):
        self.mapping.get(type(record), lambda _:None)(record)

    def handle_suiteresult(self, record):
        if record.result != test.State.InProgress:
            self.suiteresults.append(record)

    def handle_stderr(self, record):
        self.testresults[record.test.uid].write_stderr(record.message)

    def handle_stdout(self, record):
        self.testresults[record.test.uid].write_stdout(record.message)

    def handle_testresult(self, record):
        if record.result == test.State.InProgress:
            # Create a new test result object for the test which is now in progress.
            self.testresults[record.test.uid] = TestResult(record.test)
        else:
            # Update the given test's status
            self.testresults[record.test.uid].result = record.result
    
    def _save_results(self):
        with open(config.previous_result_path, 'w') as f:
            pickle.dump(SavedResults(self.suiteresults), f, config.constants.pickle_protocol)

    def close(self):
        self._save_results()


class SummaryHandler(log.Handler):
    color = terminal.get_termcap()
    reset = color.Normal
    colormap = {
            test.State.Failed: color.Red,
            test.State.Passed: color.Green,
            test.State.Skipped: color.Cyan,
    }
    sep_fmtkey = 'separator'
    sep_fmtstr = '{%s}' % sep_fmtkey

    def __init__(self):
        self.mapping = {
            log.TestResult: self.handle_testresult,
        }
        self.results = []

    def handle_testresult(self, record):
        if record.result != test.State.InProgress:
            self.results.append(record)

    def handle(self, record):
        self.mapping.get(type(record), lambda _:None)(record)

    def close(self):
        print(self._display_summary())

    def _display_summary(self):
        most_severe_outcome = None
        outcome_fmt = ' {count} {outcome}'
        strings = []

        outcome_count = [0] * len(test.State.enums)
        for result in self.results:
            outcome_count[result.result] += 1

        # Iterate over enums so they are in order of severity
        for outcome in test.State.enums:
            outcome = getattr(test.State, outcome)
            count  = outcome_count[outcome]
            if count:
                strings.append(outcome_fmt.format(count=count,
                                                  outcome=test.State.enums[outcome]))
                most_severe_outcome = outcome
        string = ','.join(strings)
        if most_severe_outcome is None:
            string = ' No testing done'
            most_severe_outcome = test.State.Passed
        #string += ' in {time:.2} seconds '.format(time=self.timer.runtime())
        string += ' '
        return terminal.insert_separator(
                string,
                color=self.colormap[most_severe_outcome] + self.color.Bold)

class TerminalHandler(log.Handler):
    color = terminal.get_termcap()
    verbosity_mapping = {
        log.Level.Warn: color.Yellow,
        log.Level.Error: color.Red,
    }
    default = color.Normal

    def __init__(self, stream, verbosity=log.Level.Info):
        self.stream = stream
        self.verbosity = verbosity
        self.mapping = {
            log.SuiteResult: self.handle_suiteresult,
            log.TestResult: self.handle_testresult,
            log.TestStderr: self.handle_stderr,
            log.TestStdout: self.handle_stdout,
            log.TestMessage: self.handle_testmessage,
            log.LibraryMessage: self.handle_librarymessage,
        }

    def _display_outcome(self, name, outcome, reason=None):
        print(SummaryHandler.colormap[outcome]
                 + name
                 + ' '
                 + test.State.enums[outcome]
                 + SummaryHandler.reset)

        if reason is not None:
            log.info('')
            log.info('Reason:')
            log.info(reason)
            log.info(terminal.separator('-'))
    
    def handle_testresult(self, record):
        if record.result == test.State.InProgress:
            print('Running %s...' % record.test.name)
        else:
            self._display_outcome(record.test.name, record.result)

    def handle_suiteresult(self, record):
        if record.result == test.State.InProgress:
            print('Running %s Test Suite...' % record.suite.name)
        else:
            print(terminal.separator('-'))
    
    def handle_stderr(self, record):
        if self.stream: print(record.message, file=sys.stderr, end='')
        
    def handle_stdout(self, record):
        if self.stream: print(record.message, file=sys.stdout, end='')
    
    def handle_testmessage(self, record):
        if self.stream: 
            print(self._colorize(record.message + str(record.caller), record.level))

    def handle_librarymessage(self, record):
        print(self._colorize(record.message, record.level))

    def _colorize(self, message, level):
        return self.verbosity_mapping.get(level, self.default) + \
                message + self.default

    def handle(self, record):
        if hasattr(record, 'level'):
            if record.level > self.verbosity:
                return
        self.mapping.get(type(record), lambda _:None)(record)
    
    def set_verbosity(self, verbosity):
        self.verbosity = verbosity


class MultiprocessingHandlerWrapper(log.Handler):
    '''
    A class which wraps other handlers and to enable 
    logging across multiprocessing processes
    '''
    def __init__(self, *subhandlers):
        # Create thread to spin handing recipt of messages
        # Create queue to push onto
        self.queue = multiprocessing.Queue()
        self.thread = threading.Thread(target=self.receive)
        self._shutdown = threading.Event()
        self.thread.daemon = True
        self.thread.start()
        self.subhandlers = subhandlers

    def _handle(self, record):
        for handler in self.subhandlers:
            handler.handle(record)

    def receive(self):
        while not self._shutdown.is_set():
            try:
                item = self.queue.get(timeout=0.1)
                self._handle(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                return
            except Queue.Empty:
                continue
    
    def send(self, record):
        self.queue.put(record)

    def handle(self, record):
        self.send(record)

    def set_verbosity(self, verbosity):
        for handler in self.subhandlers:
            handler.set_verbosity(verbosity)
    
    def close(self):
        self._shutdown.set()
        self.thread.join()
        for handler in self.subhandlers: handler.close()