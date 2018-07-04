# TODOs

In order of priority:

- Use the log rather than print statements to report fixture build errors.
- Prevent duplicate test suite names.
- Fix saving results for suites with duplicate test names.
- Refactor fixture building logic, lots of duplicate code in runners.
- Add some functional/unit tests for this library itself
- Add documentation
- Add `results` command to query/print previous test results
- Add `rerun` command to re-run failed tests
- Rework the Config
  - Initialization should be less "magic"
  - Add a plugin interface (so the library doesn't need to be modified)
- Add a multiprocessing TestSuite runner