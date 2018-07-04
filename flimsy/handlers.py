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
import state
import uid


def test_results_output_path(test_case):
    '''
    Return the path which results for a specific test case should be
    stored.
    '''
    return os.path.join(config.result_path, test_case.uid.replace(os.path.pathsep,'-'))

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
            log.SuiteStatus.type_id: self.handle_suiteresult,
            log.TestStatus.type_id: self.handle_testresult,
            log.TestStderr.type_id: self.handle_stderr,
            log.TestStdout.type_id: self.handle_stdout,
        }

    def handle(self, record):
        self.mapping.get(record.type_id, lambda _:None)(record)

    def handle_suiteresult(self, record):
        if record.status != state.State.InProgress:
            self.suiteresults.append(record)

    def handle_stderr(self, record):
        self.testresults[record.uid].write_stderr(record.data)

    def handle_stdout(self, record):
        self.testresults[record.uid].write_stdout(record.data)

    def handle_testresult(self, record):
        if record.status == state.State.InProgress:
            # Create a new test result object for the test which is now in progress.
            self.testresults[record.uid] = TestResult(record)
        else:
            # Update the given test's status
            self.testresults[record.uid].result = record.data
    
    def _save_results(self):
        with open(config.previous_result_path, 'w') as f:
            pickle.dump(SavedResults(self.suiteresults), f, config.constants.pickle_protocol)

    def close(self):
        self._save_results()


class SummaryHandler(log.Handler):
    color = terminal.get_termcap()
    reset = color.Normal
    colormap = {
            state.State.Failed: color.Red,
            state.State.Passed: color.Green,
            state.State.Skipped: color.Cyan,
    }
    sep_fmtkey = 'separator'
    sep_fmtstr = '{%s}' % sep_fmtkey

    def __init__(self):
        self.mapping = {
            log.TestStatus.type_id: self.handle_testresult,
        }
        self.results = []

    def handle_testresult(self, record):
        if record.status != state.State.InProgress:
            self.results.append(record)

    def handle(self, record):
        self.mapping.get(record.type_id, lambda _:None)(record)

    def close(self):
        print(self._display_summary())

    def _display_summary(self):
        most_severe_outcome = None
        outcome_fmt = ' {count} {outcome}'
        strings = []

        outcome_count = [0] * len(state.State.enums)
        for result in self.results:
            outcome_count[result.status] += 1

        # Iterate over enums so they are in order of severity
        for outcome in state.State.enums:
            outcome = getattr(state.State, outcome)
            count  = outcome_count[outcome]
            if count:
                strings.append(outcome_fmt.format(count=count,
                                                  outcome=state.State.enums[outcome]))
                most_severe_outcome = outcome
        string = ','.join(strings)
        if most_severe_outcome is None:
            string = ' No testing done'
            most_severe_outcome = state.State.Passed
        #string += ' in {time:.2} seconds '.format(time=self.timer.runtime())
        string += ' '
        return terminal.insert_separator(
                string,
                color=self.colormap[most_severe_outcome] + self.color.Bold)

class TerminalHandler(log.Handler):
    color = terminal.get_termcap()
    verbosity_mapping = {
        log.LogLevel.Warn: color.Yellow,
        log.LogLevel.Error: color.Red,
    }
    default = color.Normal

    def __init__(self, stream, verbosity=log.LogLevel.Info):
        self.stream = stream
        self.verbosity = verbosity
        self.mapping = {
            log.SuiteStatus.type_id: self.handle_suitestatus,
            log.TestStatus.type_id: self.handle_teststatus,
            log.TestStderr.type_id: self.handle_stderr,
            log.TestStdout.type_id: self.handle_stdout,
            log.TestMessage.type_id: self.handle_testmessage,
            log.LibraryMessage.type_id: self.handle_librarymessage,
        }

    def _display_outcome(self, name, outcome, reason=None):
        print(SummaryHandler.colormap[outcome]
                 + name
                 + ' '
                 + state.State.enums[outcome]
                 + SummaryHandler.reset)

        if reason is not None:
            log.test_log.info('')
            log.test_log.info('Reason:')
            log.test_log.info(reason)
            log.test_log.info(terminal.separator('-'))
    
    def handle_teststatus(self, record):
        if record.status == state.State.InProgress:
            print('Running %s...' % record.name)
        else:
            self._display_outcome(record.uid, record.status)

    def handle_suitestatus(self, record):
        if record.status == state.State.InProgress:
            print('Running %s Test Suite...' % record.name)
        else:
            print(terminal.separator('-'))
    
    def handle_stderr(self, record):
        if self.stream: 
            print(record.data, file=sys.stderr, end='')
        
    def handle_stdout(self, record):
        if self.stream: 
            print(record.data, file=sys.stdout, end='')
    
    def handle_testmessage(self, record):
        if self.stream: 
            print(self._colorize(record.data, record.level))

    def handle_librarymessage(self, record):
        print(self._colorize(record.data, record.level))

    def _colorize(self, message, level):
        return self.verbosity_mapping.get(level, self.default) + \
                message + self.default

    def handle(self, record):
        if record.metadata.get('level', self.verbosity) > self.verbosity:
            return
        self.mapping.get(record.type_id, lambda _:None)(record)
    
    def set_verbosity(self, verbosity):
        self.verbosity = verbosity


class PrintHandler(log.Handler):
    def __init__(self):
        pass
    
    def handle(self, record):
        print(str(record).rstrip())
    
    def close(self):
        pass

class MultiprocessingHandlerWrapper(log.Handler):
    '''
    A class which wraps other handlers and to enable 
    logging across multiprocessing processes
    '''
    def __init__(self, *subhandlers):
        # Create thread to spin handing recipt of messages
        # Create queue to push onto
        self.queue = multiprocessing.Queue()
        self._shutdown = threading.Event()
        self.subhandlers = subhandlers
    
    def async_process(self):
        self.thread = threading.Thread(target=self.process)
        self.thread.daemon = True
        self.thread.start()

    def process(self):
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
    
    def _drain(self):
        while True:
            try:
                item = self.queue.get(block=False)
                self._handle(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                return
            except Queue.Empty:
                return
    
    def _handle(self, record):
        for handler in self.subhandlers:
            handler.handle(record)

    def handle(self, record):
        self.queue.put(record)
    
    def close(self):
        self._shutdown.set()
        if hasattr(self, 'thread'):
            self.thread.join()
        self._drain()

        for handler in self.subhandlers: 
            handler.close()