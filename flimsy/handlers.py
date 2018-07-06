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
import result
import state
import uid

class _TestStreamManager(object):
    def __init__(self):
        self._writers = {}
    
    def open_writer(self, test_result):
        if test_result in self._writers:
            raise ValueError('Cannot have multiple writters on a single test.')
        self._writers[test_result] = _TestStreams(test_result.stdout, test_result.stderr)
    
    def get_writer(self, test_result):
        if test_result not in self._writers:
            self.open_writer(test_result)
        return self._writers[test_result]

    def close(self):
        for writer in self._writers.values():
            writer.close()
        self._writers.clear()

class _TestStreams(object):
    def __init__(self, stdout, stderr):
        helper.mkdir_p(os.path.dirname(stdout))
        helper.mkdir_p(os.path.dirname(stderr))
        self.stdout = open(stdout, 'w')
        self.stderr = open(stderr, 'w')

    def close(self):
        self.stdout.close()
        self.stderr.close()

class ResultHandler(log.Handler):
    def __init__(self, directory):
        self.directory = directory
        self.internal_results = None
        self.test_stream_manager = _TestStreamManager()

        self.mapping = {
            log.LibraryStatus.type_id: self.handle_library_status,
            log.SuiteStatus.type_id: self.handle_suite_status,
            log.TestStatus.type_id: self.handle_test_status,

            log.TestStderr.type_id: self.handle_stderr,
            log.TestStdout.type_id: self.handle_stdout,
        }

    def handle(self, record):
        self.mapping.get(record.type_id, lambda _:None)(record)

    def handle_library_status(self, record):
        if record.data == state.State.InProgress:
            assert self.internal_results is None   # The library should only be set to in progress once.
            self.internal_results = result.InternalLibraryResults(
                    record.metadata['metadata'],
                    self.directory
            )
        self.internal_results.result = record.data

    def handle_suite_status(self, record):
        self.internal_results.get_suite_result(record.uid).result = record.data

    def handle_test_status(self, record):
        self._get_test_result(record).result = record.data

    def handle_stderr(self, record):
        self.test_stream_manager.get_writer(
            self._get_test_result(record)
        ).stderr.write(record.data)

    def handle_stdout(self, record):
        self.test_stream_manager.get_writer(
            self._get_test_result(record)
        ).stdout.write(record.data)

    def _get_test_result(self, test_record):
        return self.internal_results.get_test_result(
                    test_record.metadata['test_uid'], 
                    test_record.metadata['suite_uid'])

    def _save(self):
        #FIXME Hardcoded path name
        result.InternalSavedResults.save(
            self.internal_results, 
            os.path.join(self.directory, 'results.pickle'))

    def close(self):
        self._save()


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
            log.LibraryStatus.type_id: self.handle_library_result,
        }
        self.results = []
    
    def handle_library_result(self, record):
        pass

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
            self._display_outcome(record.test_uid, record.status)

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