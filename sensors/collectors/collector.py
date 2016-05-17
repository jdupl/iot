class Collector():
    """Wrapper interface for all sensors.
    GPIO imports should not be in implementations of Collector subclasses,
    but inside an external library."""

    def __init__(self, pin_num, csv_path):
        self.pin_num = pin_num
        self.csv_path = csv_path

    def collect_data(self):
        raise Exception('Not implemented')

    def get_csv_headers(self):
        raise Exception('Not implemented')
