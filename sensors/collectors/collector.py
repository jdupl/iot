class Collector():
    """Wrapper interface for all sensors.
    GPIO imports should not be in implementations of Collector subclasses,
    but inside an external library."""

    def __init__(self, pin_num):
        self.pin_num = pin_num

    def collect_data(self):
        raise Exception('Not implemented')
