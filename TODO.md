# TODOs

BUG:

- If a fixture is added to a test, and that test is added to multiple suites then that same
  fixture object will be setup and torn down multiple times. This is not the intended function
  of fixtures and should be fixed.
  
  Suggested Solution:
  
  An additional step should be taken before .setup() to finalize the fixture version.
  This could be done as the default action for schedule_finalized method.

In order of priority:

- Remove explicit dependency on runner in testsuite and testcase definitins, use the config
  to set once loaded.
- Have the log pre-check that all submitted items are pickleable (or have the MP handler do so)

- Add `results` command to query/print previous test results

- Add test and suite timing
- Add complete support for JUnit output
  - Add test timing
  - Add Skip/Failure/Error reason
- Add documentation
- Add some functional/unit tests for this library itself

- Replace the summary handler with a parser of the internal result object.
- Formalize the record.type_id => handler interface with an additional handler base class.

- Rework the Config
  - Initialization should be less "magic"
  - Add a plugin interface (so the library doesn't need to be modified)
- Catch duplicate UIDs on instantiation rather than loading (so it's easier to debug the source of the issue.)