######################################################################
# 
# File: impl.py
# 
# Copyright (c) 2011 by Brian Beach
# 
# This software is licensed under the MIT license.
# 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
######################################################################

"""
This is a library for building simple mock objects.  Things are kept
as simple as possible.  The goal is to easily make mock functions and
objects that can be used to stub out calls when doing unit tests.

The simplest object to mock up is a function.  If we're testing a
wrapper that doubles a value before calling a function, it can be done
like this::

    def double_arg(fcn, value):
        fcn(value * 2)

    class TestIt(tinymock.TestCase):
        def test_double_arg(self):
            fcn = tinymock.MockFunction(2)
            double_arg(fcn, 1)

The MockFunction constructor creates a new mock function, and takes as
arguments the values that you are expecting the function to be called
with.   In the case above, the mock fuction is expecting a 2 to be
passed in.

A return value can be specified by calling the returns method on the
newly created MockFunction object.  Here is an example that tests a
function that doubles the return value of a function that it calls::

    def double_result(fcn):
        return 2 * fcn()

    class TestIt(tinymock.TestCase):
        def test_double_result(self):
            fcn = tinymock.MockFunction().returns(1)
            self.assertEquals(2, double_result(fcn))

By default, a MockFunction expects to be called just once.  You can
use the add_call method.  Here is a test case that directly calls a
mock function three times::

    class TestIt(tinymock.TestCase):
        def test_calls(self):
            fcn = (tinymock.MockFuntion().returns(1)
                   .add_call("a").returns(2)
                   .add_call("b", "c").returns(3))
            self.assertEquals(1, fcn())
            self.assertEquals(2, fcn("a"))
            self.assertEquals(3, fcn("b", "c"))
                     

"""

import time
import unittest

class ExpectedCall(object):

    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs
        self.return_value = None
        self.exception = None

class MockFunction(object):

    """
    An object that mimics a function, checking the values passed in as
    arguments, and returning a value or raising an exception.
    """

    def __init__(self, *args, **kwargs):
        """
        Creates a new MockFunction that is expecting to be called with
        args.
        """
        self._calls = []
        self.add_call(*args, **kwargs)

    def add_call(self, *args, **kwargs):
        """
        Adds another expected call to this function, expecting the
        arguments given.

        Returns this MockFunction so that a return value can be added
        on.
        """
        self._calls.append(ExpectedCall(args, kwargs))
        return self

    def returns(self, return_value):
        """
        Specifies the value to be returned.  Returns this MockFunction
        object so that another call can be chained on.
        """
        self._calls[-1].return_value = return_value
        return self

    def raises(self, exception):
        """
        Specifies an exception to be raised in response to the current
        call.

        Returns this MockFunction so another call can be chained on.
        """
        self._calls[-1].exception = exception
        return self

    def __call__(self, *args, **kwargs):
        if len(self._calls) == 0:
            raise "Unexpected call"
        call = self._calls.pop(0)
        if call.args != args:
            print "Expected arguments:", call.args
            print "Actual arguments:  ", args
            raise Exception("Argument mismatch")
        if call.kwargs != kwargs:
            print "Expected keyword arguments:", call.kwargs
            print "Actual keyword arguments:  ", kwargs
            raise Exception("Keyword argument mismatch")
        if call.exception is not None:
            raise call.exception
        else:
            return call.return_value

    def check_done(self):
        """
        Makes sure that all of the calls that were expected have
        happened.  Raises an exception if not.
        """
        if len(self._calls) != 0:
            raise Exception("Function not called enough")

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
            f.check_done()

    def mock_fcn(self, *args, **kwargs):
        f = MockFunction(*args, **kwargs)
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

    def test_function_keyword(self):
        f = self.mock_fcn(a = 5)
        f(a = 5)

    def test_function_extra_keyword(self):
        f = self.mock_fcn()
        def should_raise():
            f(a = 5)
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
