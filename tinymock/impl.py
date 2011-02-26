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

    def __init__(self, fcn, args, kwargs):
        self.fcn = fcn
        self.args = args
        self.kwargs = kwargs
        self.return_value = None
        self.exception = None

class CallContext(object):

    """
    This provides a context in which mock function calls are tracked.
    Specifically, this tracks what calls are expected and provides ordering
    over all the mock functions and objects that use it.
    """

    def __init__(self):
        self._calls = []

    def add_call(self, fcn, *args, **kwargs):
        self._calls.append(ExpectedCall(fcn, args, kwargs))

    def set_last_return(self, fcn, return_value):
        self._check_last_call(fcn, "return value")
        self._calls[-1].return_value = return_value

    def set_last_exception(self, fcn, exception):
        self._check_last_call(fcn, "exception")
        self._calls[-1].exception = exception

    def call(self, fcn, *args, **kwargs):
        if len(self._calls) == 0:
            raise MockException("Unexpected call of '%s'" % fcn.name)
        call = self._calls.pop(0)
        if call.fcn != fcn:
            raise MockException(
                    "Unexpected call of '%s'; expected '%s'" %
                    (fcn.name, call.fcn.name)
                    )
        if call.args != args:
            message = (
                ("Argument mismatch for '%s':\n" % fcn.name) +
                ("Expected arguments: %s\n" % str(call.args)) +
                ("Actual arguments:   %s\n" % str(args))
                )
            raise MockException(message)
        if call.kwargs != kwargs:
            message = (
                ("Argument mismatch for '%s':\n" % fcn.name) +
                ("Expected keyword arguments: %s\n" % str(call.kwargs)) +
                ("Actual keyword arguments:   %s\n" % str(kwargs))
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
            raise MockException("Still expecting more function calls")

    def _check_last_call(self, fcn, reason):
        if len(self._calls) == 0:
            raise Exception("no call for which to set " + reason)
        if fcn != self._calls[-1].fcn:
            raise Exception(reason + " must be set immediately after add_call")

class MockFunction(object):

    """
    An object that mimics a function, checking the values passed in as
    arguments, and returning a value or raising an exception.
    """

    def __init__(self, context, name):
        """
        Creates a new MockFunction with the given name.
        """
        self._context = context
        self.name = name

    def add_call(self, *args, **kwargs):
        """
        Adds another expected call to this function, expecting the
        arguments and keyword argumentsgiven.

        Returns this MockFunction so that a return value can be added
        on.
        """
        self._context.add_call(self, *args, **kwargs)
        return self

    def returns(self, return_value):
        """
        Specifies the value to be returned.  Returns this MockFunction
        object so that another call can be chained on.
        """
        self._context.set_last_return(self, return_value)
        return self

    def raises(self, exception):
        """
        Specifies an exception to be raised in response to the current
        call.

        Returns this MockFunction so another call can be chained on.
        """
        self._context.set_last_exception(self, exception)
        return self

    def __call__(self, *args, **kwargs):
        return self._context.call(self, *args, **kwargs)

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
        self._context = CallContext()

    def tearDown(self):
        """
        Make sure that all of the expected things happened.
        """
        super(TestCase, self).tearDown()
        self._context.check_done()

    def mock_fcn(self, name):
        """
        Make a new MockFunction.  It's check_done method will be
        called at the end of the test.
        """
        return MockFunction(self._context, name)

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

    def patch_set(self, *patch_tuples):
        """
        Convenience method to make PatchSet objects.
        """
        return PatchSet(*patch_tuples)

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
        self._prev_value = self._object.__dict__.get(self._field)
        self._object.__dict__[self._field] = self._value

    def __exit__(self, *args):
        if self._prev_value is None:
            del self._object.__dict__[self._field]
        else:
            self._object.__dict__[self._field] = self._prev_value

class PatchSet(object):

    """
    A context for use in a with statement to apply multiple Patches (see above)
    at once.  Each patch is specified as a 3-tuple corresponding to the
    arguments of Patch.
    """

    def __init__(self, *patch_tuples):
        """
        Creates a new context.  Each patch_tuple should be a 3-tuple
        corresponding to the arguments of Patch.  For example:

            with PatchSet(
                    (time, 'sleep', sleep),
                    (time, 'clock', clock)
                    ):
                run_with_patched_time()

        is largely equivalent to:
        
            with Patch(time, 'sleep', sleep):
                with Patch(time, 'clock', clock):
                    run_with_patched_time()
        """
        self._patches = [
                Patch(patch_tuple[0], patch_tuple[1], patch_tuple[2])
                for patch_tuple in patch_tuples
                ]

    def __enter__(self):
        for patch in self._patches:
            patch.__enter__()

    def __exit__(self, *args):
        for patch in self._patches:
            patch.__exit__(*args)
        
class TestMock(TestCase):

    def test_function_return_value(self):
        f = self.mock_fcn('f').add_call().returns(2)
        self.assertEquals(2, f())

    def test_function_raises(self):
        f = self.mock_fcn('f').add_call(2).raises(Exception('kaboom'))
        def should_raise():
            f(2)
        self.assertRaises(Exception, should_raise)

    def test_function_arg_mismatch(self):
        f = self.mock_fcn('f').add_call(1)
        def should_raise():
            f(2)
        self.assertRaises(MockException, should_raise)

    def test_function_keyword(self):
        f = self.mock_fcn('f').add_call(a = 5)
        f(a = 5)

    def test_function_extra_keyword(self):
        f = self.mock_fcn('f').add_call()
        def should_raise():
            f(a = 5)
        self.assertRaises(MockException, should_raise)

    def test_function_not_called(self):
        f = self.mock_fcn('f').add_call()
        self.assertRaises(MockException, self.tearDown)
        self._context._calls = []

    def test_function_called_too_many_times(self):
        f = self.mock_fcn('f').add_call()
        f()
        def should_raise():
            f()
        self.assertRaises(MockException, should_raise)
    
    def test_function_called_twice(self):
        f = self.mock_fcn('f').add_call().returns(1)
        f.add_call().returns(2)
        self.assertEqual(1, f())
        self.assertEqual(2, f())

    def test_mock_object(self):
        x = self.mock_obj()
        x.foo = self.mock_fcn('f').add_call().returns(1)
        self.assertEquals(1, x.foo())
    
    def test_mock_object_with_kw_args(self):
        x = self.mock_obj(
            foo = self.mock_fcn('f').add_call().returns(1),
            bar = 2
            )
        self.assertEquals(1, x.foo())
        self.assertEquals(2, x.bar)

    def test_patch(self):
        with Patch(
                time,
                'sleep',
                self.mock_fcn('sleep').add_call(1).returns(2)
                ):
            self.assertEquals(2, time.sleep(1))

    def test_patch_method(self):
        with self.patch(
                time,
                'sleep',
                self.mock_fcn('sleep').add_call(1).returns(2)
                ):
            self.assertEquals(2, time.sleep(1))

    def test_patch_non_existent(self):
        with self.patch(
                time,
                'duerme',
                self.mock_fcn('duerme').add_call(1).returns(2)
                ):
            self.assertEquals(2, time.duerme(1))

    def test_patch_set(self):
        class Person():
            def __init__(self, name):
                self.name = name
        p1 = Person('Joe')
        p2 = Person('Fred')
        with PatchSet(
                (p1, 'name', 'Sally'),
                (p2, 'age', 37)
                ):
            self.assertEquals(dict(name = 'Sally'), p1.__dict__)
            self.assertEquals(dict(name = 'Fred', age = 37), p2.__dict__)
        self.assertEquals(dict(name = 'Joe'), p1.__dict__)
        self.assertEquals(dict(name = 'Fred'), p2.__dict__)

    def test_patch_set_method(self):
        class Person():
            def __init__(self, name):
                self.name = name
        p1 = Person('Joe')
        p2 = Person('Fred')
        with self.patch_set(
                (p1, 'name', 'Sally'),
                (p2, 'age', 37)
                ):
            self.assertEquals(dict(name = 'Sally'), p1.__dict__)
            self.assertEquals(dict(name = 'Fred', age = 37), p2.__dict__)
        self.assertEquals(dict(name = 'Joe'), p1.__dict__)
        self.assertEquals(dict(name = 'Fred'), p2.__dict__)

if __name__ == '__main__':
    unittest.main()
