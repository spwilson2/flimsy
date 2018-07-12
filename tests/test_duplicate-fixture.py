import whimsy


class DetectDuplicateFixture(whimsy.Fixture):
    def init(self, *args, **kwargs):
        self.__setup = False

    def setup(self, testitem):
        if self.__setup:
            raise Exception("Fixture has already been setup, the instance wasn't duplicated.")
        self.__setup = True

fixtures = [DetectDuplicateFixture()]

whimsy.TestFunction(lambda params: None, fixtures=fixtures)
whimsy.TestFunction(lambda params: None, name='test1', fixtures=fixtures)