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
        regular arguments args and keywords arguments kwargs.
        """
        self._calls = []
        self.add_call(*args, **kwargs)

    def add_call(self, *args, **kwargs):
        """
        Adds another expected call to this function, expecting the
        arguments and keyword argumentsgiven.

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

    """
    A class that can pretend to be an arbitrary object.

    This class has no methods (other than the constructor).  It is
    just a container for whatever attributes you assign to it.
    """

    def __init__(self, **kwargs):
        """
        Creates a new mock object with the attributes specified by the
        keyword arguments passed in.
        """
        for (key, value) in kwargs.items():
            self.__dict__[key] = value

class TestCase(unittest.TestCase):

    """
    Subclass of unittest.TestCase that checks to make sure that all
    expected function calls have happened.  If you use self.mock_fcn()
    and self.mock_obj() to make your mocks, then you don't have to
    worry about calling check_done on them.

    You do need to make sure that if you implement setUp() and
    tearDown() methods that you call super.
    """

    def setUp(self):
        """
        Get ready to make mock objects.
        """
        super(TestCase, self).setUp()
        self._functions = []

    def tearDown(self):
        """
        Make sure that all of the expected things happened.
        """
        super(TestCase, self).tearDown()
        for f in self._functions:
            f.check_done()

    def mock_fcn(self, *args, **kwargs):
        """
        Make a new MockFunction.  It's check_done method will be
        called at the end of the test.
        """
        f = MockFunction(*args, **kwargs)
        self._functions.append(f)
        return f

    def mock_obj(self, **kwargs):
        """
        Make a new MockObject.
        """
        return MockObject(**kwargs)

    def patch(self, obj, field, value):
        """
        Convenience method to make Patch objects.
        """
        return Patch(obj, field, value)

class Patch(object):

    """
    A context for use in a with statement to temporarily replace a
    member of a module or object with a new value.
    """

    def __init__(self, obj, field, value):
        """
        Creates a new context.  The named field of the module or
        object will be replaced with the given value just for the
        duration of the context.
        """
        self._object = obj
        self._field = field
        self._value = value

    def __enter__(self):
        self._prev_value = self._object.__dict__[self._field]
        self._object.__dict__[self._field] = self._value

    def __exit__(self, *args):
        self._object.__dict__[self._field] = self._prev_value
        
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
        with Patch(time, 'sleep', self.mock_fcn(1).returns(2)):
            self.assertEquals(2, time.sleep(1))

    def test_patch_method(self):
        with self.patch(time, 'sleep', self.mock_fcn(1).returns(2)):
            self.assertEquals(2, time.sleep(1))

if __name__ == '__main__':
    unittest.main()
