######################################################################
# 
# File: impl.py
# 
# Copyright 2011 TiVo Inc. All Rights Reserved. by Brian Beach
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

class MockException(Exception):
    pass

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
            raise MockException("Unexpected call")
        call = self._calls.pop(0)
        if call.args != args:
            message = (
                "Argument mismatch:\n" +
                ("Expected arguments: %s\n" % call.args) +
                ("Actual arguments:   %s\n" % args)
                )
            raise MockException(message)
        if call.kwargs != kwargs:
            message = (
                "Keyword argument mismatch:\n" +
                ("Expected keyword arguments: %s\n" % call.kwargs) +
                ("Actual keyword arguments:   %s\n" % kwargs)
                )
            raise MockException(message)
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
            raise MockException("Function not called enough")

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

    def patch(self, obj = None, field = None, value = None, triples = None):
        """
        Convenience method to make Patch objects.
        """
        return Patch(obj, field, value, triples)

class Patch(object):

    """
    A context for use in a with statement to temporarily replace a
    member of a module or object with a new value.
    """

    def __init__(self, obj = None, field = None, value = None, triples = None):
        """
        Creates a new context.  The named field of the module or
        object will be replaced with the given value just for the
        duration of the context.

        Each patch requires three things: (1) the object to patch, (2)
        a string that is the name of the field to patch, and (3) the
        value to put in that field.

        This constructor can be called in two different ways.  You can
        pass in three arguments that are the object, field, and value::

            Patch(my_object, 'name', 'Fred')

        Or, you can call it with a list of patches to make, using the
        'triples' keyword argument:

            triples = [
                (my_object, name, 'Fred'),
                (my_object, age, 37),
                (my_other_object, name, 'Joe')
                ]
            Patch(triples = patches)

        The value of None is special; it means that the field of the
        object should be removed.
        """
        if triples is not None:
            if (obj is not None) or (field is not None) or (value is not None):
                raise ValueError(
                    "Do not pass in an object, field, or value " +
                    "when using the keyword 'triples'"
                    )
            self._triples = triples
        else:
            self._triples = [(obj, field, value)]

    def __enter__(self):
        self.swap()

    def __exit__(self, *args):
        self.swap()

    def swap(self):
        """
        Swap the values in self._triples with the values out in the
        wild.
        """
        self._triples = [
            (obj, field, self.swap_value(obj, field, value))
            for (obj, field, value) in self._triples
            ]

    def swap_value(self, obj, field, value):
        """
        Stores the given value in the object and returns the old
        value.
        """
        old_value = obj.__dict__.get(field)
        if value is None:
            if old_value is not None:
                del obj.__dict__[field]
        else:
            obj.__dict__[field] = value
        return old_value
        
class TestMock(TestCase):

    def test_function_return_value(self):
        f = self.mock_fcn().returns(2)
        self.assertEquals(2, f())

    def test_function_arg_mismatch(self):
        f = self.mock_fcn(1)
        def should_raise():
            f(2)
        self.assertRaises(MockException, should_raise)

    def test_function_keyword(self):
        f = self.mock_fcn(a = 5)
        f(a = 5)

    def test_function_extra_keyword(self):
        f = self.mock_fcn()
        def should_raise():
            f(a = 5)
        self.assertRaises(MockException, should_raise)

    def test_function_not_called(self):
        f = self.mock_fcn()
        self.assertRaises(MockException, self.tearDown)
        self._functions = []

    def test_function_called_too_many_times(self):
        f = self.mock_fcn()
        f()
        def should_raise():
            f()
        self.assertRaises(MockException, should_raise)
    
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

    def test_patch_non_existant(self):
        with self.patch(time, 'duerme', self.mock_fcn(1).returns(2)):
            self.assertEquals(2, time.duerme(1))

    def test_patch_multiple(self):
        class Person():
            def __init__(self, name):
                self.name = name
        p1 = Person('Joe')
        p2 = Person('Fred')
        with self.patch(triples = [(p1, 'name', 'Sally'), (p2, 'age', 37)]):
            self.assertEquals(dict(name = 'Sally'), p1.__dict__)
            self.assertEquals(dict(name = 'Fred', age = 37), p2.__dict__)
        self.assertEquals(dict(name = 'Joe'), p1.__dict__)
        self.assertEquals(dict(name = 'Fred'), p2.__dict__)

if __name__ == '__main__':
    unittest.main()
