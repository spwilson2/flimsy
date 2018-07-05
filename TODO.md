# TODOs

In order of priority:

- Add test, suite, library timing
- Add some functional/unit tests for this library itself
- Add documentation
- Add `results` command to query/print previous test results
- Add JUnit/XML result formatter - should post apply to the internal result logger
- Add `rerun` command to re-run failed tests
- Rework the Config
  - Initialization should be less "magic"
  - Add a plugin interface (so the library doesn't need to be modified)
- Catch duplicate UIDs on instantiation rather than loading (so it's easier to debug the source of the issue.)
- Add a multiprocessing TestSuite runner