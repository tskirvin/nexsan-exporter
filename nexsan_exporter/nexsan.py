def probe(target):
    '''
    Returns a collector populated with metrics from the target array.
    '''
    return Collector(target)

class Collector:
    def __init__(self, target):
        self.__target = target

    def collect(self):
        raise StopIteration
