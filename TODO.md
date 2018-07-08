# TODOs

In order of priority:

- Have the log pre-check that all submitted items are pickleable (or have the MP handler do so)

- Set Error/Skip status in suites on fixture fail/skip for global fixtures.
- Runner logic is now convoluted
  - the runner must be instantiated for each test/suite
  - no clear definition of states (building, running, errored)

- `list` command should also list tests under suites.
- Only init necessary loggers for other commands like `list`.
- Add `results` command to query/print previous test results
- Add `rerun` command to re-run failed tests

- Add test, suite, library timing
- Add complete support for JUnit output
  - Add test timing
  - Add Skip/Failure/Error reason
- Add documentation
- Add some functional/unit tests for this library itself

- Rework the Config
  - Initialization should be less "magic"
  - Add a plugin interface (so the library doesn't need to be modified)
- Catch duplicate UIDs on instantiation rather than loading (so it's easier to debug the source of the issue.)
- Add a multiprocessing TestSuite runner