# TODOs

In order of priority:

- Log failed fixture build errors.
- Refactor Log into a more generic interface that allows filtering before reciept of data (to improve performance)
- Refactor fixture building logic, lots of duplicate code in runners.
- Add some functional/unit tests for this library itself
- Add documentation
- Add `results` command to query/print previous test results
- Add `rerun` command to re-run failed tests
- Add a multiprocessing TestSuite runner