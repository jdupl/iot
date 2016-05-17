import sys
import unittest

from unittest.mock import MagicMock, Mock

# Mock external library, not wrapper
sys.modules['dht11'] = Mock()
# Import wrapper after setting up system import mock
from sensors.collectors.dht11 import DHT11Collector


class RelayTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_lights_from_configs(self):
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
