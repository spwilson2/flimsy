# TODOs

In order of priority:

- Improve tag filter logic by using ordered `--include-tags`, `--exclude-tags` flags with regex support
- Refactor Log into a more generic interface that allows filtering before reciept of data (to improve performance)
- Add guarunteed attempt at teardown for fixtures (currently if setup calls skip, teardown is never performed)
- Add `results` command to query/print previous test results
- Add `rerun` command to re-run failed tests
- Add a multiprocessing TestSuite runner