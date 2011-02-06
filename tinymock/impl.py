######################################################################
# 
# File: impl.py
# 
# Copyright (c) 2011 by Brian Beach
# 
# This software is licensed under the MIT license.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
######################################################################

'''
This is a library for building simple mock objects.
'''

import time
import unittest

class MockFunction(object):

    def __init__(self, *args):
        self._calls = []
        self.add_call(*args)

    def add_call(self, *args):
        self._calls.append([args, None, None])
        return self

    def returns(self, return_value):
        self._calls[-1][1] = return_value
        return self

    def raises(self, exception):
        self._calls[-1][2] = exception
        return self

    def __call__(self, *args):
        if len(self._calls) == 0:
            raise "Unexpected call"
        (expected_args, return_value, exception) = self._calls.pop(0)
        if expected_args != args:
            print "Expected arguments:", expected_args
            print "Actual arguments:  ", args
            raise Exception("Argument mismatch")
        if exception is not None:
            raise exception
        else:
            return return_value

class MockObject(object):

    def __init__(self, **kwargs):
        for (key, value) in kwargs.items():
            self.__dict__[key] = value

class TestCase(unittest.TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self._functions = []

    def tearDown(self):
        '''
        Make sure that all of the expected things happened.
        '''
        super(TestCase, self).tearDown()
        for f in self._functions:
            if len(f._calls) != 0:
                raise Exception("Function not called enough")

    def mock_fcn(self, *args):
        f = MockFunction(*args)
        self._functions.append(f)
        return f

    def mock_obj(self, **kwargs):
        return MockObject(**kwargs)

class Patcher(object):
    def __init__(self, object, field, value):
        self._object = object
        self._field = field
        self._value = value

    def __enter__(self):
        self._prev_value = self._object.__dict__[self._field]
        self._object.__dict__[self._field] = self._value

    def __exit__(self, *args):
        self._object.__dict__[self._field] = self._prev_value
        
def patch(object, field, value):
    return Patcher(object, field, value)

class TestMock(TestCase):

    def test_function_return_value(self):
        f = self.mock_fcn().returns(2)
        self.assertEquals(2, f())

    def test_function_arg_mismatch(self):
        f = self.mock_fcn(1)
        def should_raise():
            f(2)
        self.assertRaises(Exception, should_raise)

    def test_function_not_called(self):
        f = self.mock_fcn()
        self.assertRaises(Exception, self.tearDown)
        self._functions = []

    def test_function_called_too_many_times(self):
        f = self.mock_fcn()
        f()
        def should_raise():
            f()
        self.assertRaises(Exception, should_raise)
    
    def test_function_called_twice(self):
        f = self.mock_fcn().returns(1)
        f.add_call().returns(2)
        self.assertEqual(1, f())
        self.assertEqual(2, f())

    def test_mock_object(self):
        x = self.mock_obj()
        x.foo = self.mock_fcn().returns(1)
        self.assertEquals(1, x.foo())
    
    def test_mock_object_with_kw_args(self):
        x = self.mock_obj(
            foo = self.mock_fcn().returns(1),
            bar = 2
            )
        self.assertEquals(1, x.foo())
        self.assertEquals(2, x.bar)

    def test_patch(self):
        with patch(time, 'sleep', self.mock_fcn(1).returns(2)):
            self.assertEquals(2, time.sleep(1))

if __name__ == '__main__':
    unittest.main()
