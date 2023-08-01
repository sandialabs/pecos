import unittest
import pecos


class TestLogger(unittest.TestCase):

    def test_initialize(self):
        pecos.logger.initialize()
        
        self.assertEqual(0, 0)


if __name__ == '__main__':
    unittest.main()
