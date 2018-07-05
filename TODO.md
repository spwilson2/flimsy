# TODOs

In order of priority:

- Add JUnit/XML result formatter - should post apply to the internal result logger
- Add `results` command to query/print previous test results
- Add `rerun` command to re-run failed tests
- `list` command should also list tests under suites.
- Add test, suite, library timing
- Add some functional/unit tests for this library itself
- Add documentation
- Rework the Config
  - Initialization should be less "magic"
  - Add a plugin interface (so the library doesn't need to be modified)
- Only init necessary loggers for other commands like `list`.
- Catch duplicate UIDs on instantiation rather than loading (so it's easier to debug the source of the issue.)
- Add a multiprocessing TestSuite runner