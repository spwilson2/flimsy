class State():
    enums = '''
    NotRun
    InProgress
    Skipped
    Passed
    Failed
    '''.split()

    for idx, enum in enumerate(enums):
        locals()[enum] = idx
