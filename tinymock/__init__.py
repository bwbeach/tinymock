######################################################################
# 
# File: __init__.py
# 
# Copyright 2011 TiVo Inc. All Rights Reserved. by Brian Beach and Jaran Charumilind
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

The module provides a TestCase class that your test cases should
inherit from, instead of inheriting from unittest.TestCase.  The
tinymock.TestCase class provides methods to create mock objects and
mock functions, and checks at the end of each test that all of the
expected calls were made to mock functions.

The simplest object to mock up is a function.  Here is an example of
calling a mock function that expects a single argument whose value is
1::

    class TestIt(tinymock.TestCase):
        def test_call_function(self):
            fcn = self.mock_fcn("fcn").expect(1)
            fcn(1)

The mock_fcn method in tinymock.TestCase creates a new mock function,
and takes as its argument the name of the function.  The expect
tells the mock function to expect a call with the values that you are
expecting the function to be called with.  In the case above, the mock
fuction is expecting a 1 to be passed in.

A return value can be specified by calling the returns method on the
mock function object after a call.  Here is an example that calls a
function that expects no arguments and returns 2::

    class TestIt(tinymock.TestCase):
        def test_function_return(self):
            fcn = self.mock_fcn('fcn').expect().returns(2)
            self.assertEquals(2, fcn())

Upon creation, a MockFunction does not expect any calls.  You use the
expect method for each time you expect the method to be called.
Here is a test case that directly calls a mock function three times,
each time with different arguments and a different return value::

    class TestIt(tinymock.TestCase):
        def test_calls(self):
            fcn = self.mock_fcn("fcn")
            fcn..expect().returns(1)
            fcn.expect("a").returns(2)
            fcn.expect("b", "c").returns(3))
            self.assertEquals(1, fcn())
            self.assertEquals(2, fcn("a"))
            self.assertEquals(3, fcn("b", "c"))
                     
Making mock objects is straightforward.  The MockObject class is
simply a container for the members of the object, which can be set
manually, or by passing in keyword arguments to the constructor.  The
mock_obj method in tinymock.TestCase creates new mock objects.

Here is an example that has an attribute a holding 1, and a mocked
method b that returns 2::

    class TestIt(tinymock.TestCase):
        def test_object(self):
            obj = self.mock_obj(
                "my_object",
                a = 1,
                b = self.mock_fcn("obj.b").expect().returns(2)
                )
            self.assertEquals(1, obj.a)
            self.assertEquals(2, obj.b())

A patch can be used to replace a field in another module or object for
the duration of a test.  The patch method returns an object used as
the context for a with statement to make the replacement, and then to
restore things when the with statement is done.  In this example, the
sleep function is replaced with a mock function.  This way the test
can verfy that sleep was called, without having to wait::

    class TestIt(tinymock.TestCase):
        def test_sleeper(self):
            sleep = self.mock_fcn("sleep").expect(10)
            with self.patch(time, "sleep", sleep)
                function_that_should_sleep_10_seconds()

If you have multiple calls to patch, you can use a PatchSet::

    class TestIt(tinymock.TestCase):
        def test_sleeper(self):
            sleep = self.mock_fcn("sleep")
            getpid = self.mock_fcn("getpid")
            sleep.expect(10)
            getpid.expect().returns(1)
            patch_set = self.patch_set(
                (time, "sleep", sleep),
                (os, "getpid", getpid)
                )
            with patch_set:
                function_that_should_sleep_10_seconds_and_getpid()
"""

from .impl import TestCase
