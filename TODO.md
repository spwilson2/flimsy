# TODOs

In order of priority:

- Pass suite to test cases (so they can access suite level fixtures)
- Prevent duplicate test suite names.
- Fix saving results for suites with duplicate test names.
- Add test, suite, library timing
- Add some functional/unit tests for this library itself
- Add documentation
- Add `results` command to query/print previous test results
- Add JUnit/XML result formatter - should post apply to the internal result logger
- Add `rerun` command to re-run failed tests
- Rework the Config
  - Initialization should be less "magic"
  - Add a plugin interface (so the library doesn't need to be modified)
- Add a multiprocessing TestSuite runner