from unittest import TestLoader, TestSuite
import os

HERE = os.path.dirname(__file__)


def suite():
    test_modules = TestLoader().discover(HERE, "*_tests.py")
    return TestSuite(test_modules)
