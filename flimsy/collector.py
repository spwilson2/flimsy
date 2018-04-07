if __name__ == '__main__':
    class Ex(InstanceCollector):
        pass

    class Der(Ex):
        pass

    class Ex2(InstanceCollector):
        pass

    Ex()
    Ex()
    Der()
    Ex2()
    print(Ex.instances)