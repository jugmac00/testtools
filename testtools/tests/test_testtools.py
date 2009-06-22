# Copyright (c) 2008 Jonathan M. Lange. See LICENSE for details.

"""Tests for extensions to the base test library."""

import unittest
from testtools import (
    TestCase,
    clone_test_with_new_id,
    skip,
    skipIf,
    skipUnless,
    )
from testtools.tests.helpers import LoggingResult


class TestEquality(TestCase):
    """Test `TestCase`'s equality implementation."""

    def test_identicalIsEqual(self):
        # TestCase's are equal if they are identical.
        self.assertEqual(self, self)

    def test_nonIdenticalInUnequal(self):
        # TestCase's are not equal if they are not identical.
        self.assertNotEqual(TestCase(), TestCase())


class TestAssertions(TestCase):
    """Test assertions in TestCase."""

    def raiseError(self, exceptionFactory, *args, **kwargs):
        raise exceptionFactory(*args, **kwargs)

    def test_formatTypes_single(self):
        # Given a single class, _formatTypes returns the name.
        class Foo:
            pass
        self.assertEqual('Foo', self._formatTypes(Foo))

    def test_formatTypes_multiple(self):
        # Given multiple types, _formatTypes returns the names joined by
        # commas.
        class Foo:
            pass
        class Bar:
            pass
        self.assertEqual('Foo, Bar', self._formatTypes([Foo, Bar]))

    def test_assertRaises(self):
        # assertRaises asserts that a callable raises a particular exception.
        self.assertRaises(RuntimeError, self.raiseError, RuntimeError)

    def test_assertRaises_fails_when_no_error_raised(self):
        # assertRaises raises self.failureException when it's passed a
        # callable that raises no error.
        ret = ('orange', 42)
        try:
            self.assertRaises(RuntimeError, lambda: ret)
        except self.failureException, e:
            # We expected assertRaises to raise this exception.
            self.assertEqual(
                '%s not raised, %r returned instead.'
                % (self._formatTypes(RuntimeError), ret), str(e))
        else:
            self.fail('Expected assertRaises to fail, but it did not.')

    def test_assertRaises_fails_when_different_error_raised(self):
        # assertRaises re-raises an exception that it didn't expect.
        self.assertRaises(
            ZeroDivisionError,
            self.assertRaises,
                RuntimeError, self.raiseError, ZeroDivisionError)

    def test_assertRaises_returns_the_raised_exception(self):
        # assertRaises returns the exception object that was raised. This is
        # useful for testing that exceptions have the right message.

        # This contraption stores the raised exception, so we can compare it
        # to the return value of assertRaises.
        raisedExceptions = []
        def raiseError():
            try:
                raise RuntimeError('Deliberate error')
            except RuntimeError, e:
                raisedExceptions.append(e)
                raise

        exception = self.assertRaises(RuntimeError, raiseError)
        self.assertEqual(1, len(raisedExceptions))
        self.assertTrue(
            exception is raisedExceptions[0],
            "%r is not %r" % (exception, raisedExceptions[0]))

    def test_assertRaises_with_multiple_exceptions(self):
        # assertRaises((ExceptionOne, ExceptionTwo), function) asserts that
        # function raises one of ExceptionTwo or ExceptionOne.
        expectedExceptions = (RuntimeError, ZeroDivisionError)
        self.assertRaises(
            expectedExceptions, self.raiseError, expectedExceptions[0])
        self.assertRaises(
            expectedExceptions, self.raiseError, expectedExceptions[1])

    def test_assertRaises_with_multiple_exceptions_failure_mode(self):
        # If assertRaises is called expecting one of a group of exceptions and
        # a callable that doesn't raise an exception, then fail with an
        # appropriate error message.
        expectedExceptions = (RuntimeError, ZeroDivisionError)
        failure = self.assertRaises(
            self.failureException,
            self.assertRaises, expectedExceptions, lambda: None)
        self.assertEqual(
            '%s not raised, None returned instead.'
            % self._formatTypes(expectedExceptions), str(failure))

    def assertFails(self, message, function, *args, **kwargs):
        """Assert that function raises a failure with the given message."""
        failure = self.assertRaises(
            self.failureException, function, *args, **kwargs)
        self.assertEqual(message, str(failure))

    def test_assertIn_success(self):
        # assertIn(needle, haystack) asserts that 'needle' is in 'haystack'.
        self.assertIn(3, range(10))
        self.assertIn('foo', 'foo bar baz')
        self.assertIn('foo', 'foo bar baz'.split())

    def test_assertIn_failure(self):
        # assertIn(needle, haystack) fails the test when 'needle' is not in
        # 'haystack'.
        self.assertFails('3 not in [0, 1, 2]', self.assertIn, 3, [0, 1, 2])
        self.assertFails(
            '%r not in %r' % ('qux', 'foo bar baz'),
            self.assertIn, 'qux', 'foo bar baz')

    def test_assertNotIn_success(self):
        # assertNotIn(needle, haystack) asserts that 'needle' is not in
        # 'haystack'.
        self.assertNotIn(3, [0, 1, 2])
        self.assertNotIn('qux', 'foo bar baz')

    def test_assertNotIn_failure(self):
        # assertNotIn(needle, haystack) fails the test when 'needle' is in
        # 'haystack'.
        self.assertFails('3 in [1, 2, 3]', self.assertNotIn, 3, [1, 2, 3])
        self.assertFails(
            '%r in %r' % ('foo', 'foo bar baz'),
            self.assertNotIn, 'foo', 'foo bar baz')

    def test_assertIsInstance(self):
        # assertIsInstance asserts that an object is an instance of a class.

        class Foo:
            """Simple class for testing assertIsInstance."""

        foo = Foo()
        self.assertIsInstance(foo, Foo)

    def test_assertIsInstance_multiple_classes(self):
        # assertIsInstance asserts that an object is an instance of one of a
        # group of classes.

        class Foo:
            """Simple class for testing assertIsInstance."""

        class Bar:
            """Another simple class for testing assertIsInstance."""

        foo = Foo()
        self.assertIsInstance(foo, (Foo, Bar))
        self.assertIsInstance(Bar(), (Foo, Bar))

    def test_assertIsInstance_failure(self):
        # assertIsInstance(obj, klass) fails the test when obj is not an
        # instance of klass.

        class Foo:
            """Simple class for testing assertIsInstance."""

        self.assertFails(
            '42 is not an instance of %s' % self._formatTypes(Foo),
            self.assertIsInstance, 42, Foo)

    def test_assertIsInstance_failure_multiple_classes(self):
        # assertIsInstance(obj, (klass1, klass2)) fails the test when obj is
        # not an instance of klass1 or klass2.

        class Foo:
            """Simple class for testing assertIsInstance."""

        class Bar:
            """Another simple class for testing assertIsInstance."""

        self.assertFails(
            '42 is not an instance of %s' % self._formatTypes([Foo, Bar]),
            self.assertIsInstance, 42, (Foo, Bar))

    def test_assertIs(self):
        # assertIs asserts that an object is identical to another object.
        self.assertIs(None, None)
        some_list = [42]
        self.assertIs(some_list, some_list)
        some_object = object()
        self.assertIs(some_object, some_object)

    def test_assertIs_fails(self):
        # assertIs raises assertion errors if one object is not identical to
        # another.
        self.assertFails('None is not 42', self.assertIs, None, 42)
        self.assertFails('[42] is not [42]', self.assertIs, [42], [42])

    def test_assertIsNot(self):
        # assertIsNot asserts that an object is not identical to another
        # object.
        self.assertIsNot(None, 42)
        self.assertIsNot([42], [42])
        self.assertIsNot(object(), object())

    def test_assertIsNot_fails(self):
        # assertIsNot raises assertion errors if one object is identical to
        # another.
        self.assertFails('None is None', self.assertIsNot, None, None)
        some_list = [42]
        self.assertFails(
            '[42] is [42]', self.assertIsNot, some_list, some_list)


class TestAddCleanup(TestCase):
    """Tests for TestCase.addCleanup."""

    class LoggingTest(TestCase):
        """A test that logs calls to setUp, runTest and tearDown."""

        def setUp(self):
            self._calls = ['setUp']

        def brokenSetUp(self):
            # A tearDown that deliberately fails.
            self._calls = ['brokenSetUp']
            raise RuntimeError('Deliberate Failure')

        def runTest(self):
            self._calls.append('runTest')

        def tearDown(self):
            self._calls.append('tearDown')

    def setUp(self):
        self._result_calls = []
        self.test = TestAddCleanup.LoggingTest('runTest')
        self.logging_result = LoggingResult(self._result_calls)

    def assertErrorLogEqual(self, messages):
        self.assertEqual(messages, [call[0] for call in self._result_calls])

    def assertTestLogEqual(self, messages):
        """Assert that the call log equals `messages`."""
        self.assertEqual(messages, self.test._calls)

    def logAppender(self, message):
        """Return a cleanup that appends `message` to the tests log.

        Cleanups are callables that are added to a test by addCleanup. To
        verify that our cleanups run in the right order, we add strings to a
        list that acts as a log. This method returns a cleanup that will add
        the given message to that log when run.
        """
        self.test._calls.append(message)

    def test_fixture(self):
        # A normal run of self.test logs 'setUp', 'runTest' and 'tearDown'.
        # This test doesn't test addCleanup itself, it just sanity checks the
        # fixture.
        self.test.run(self.logging_result)
        self.assertTestLogEqual(['setUp', 'runTest', 'tearDown'])

    def test_cleanup_run_before_tearDown(self):
        # Cleanup functions added with 'addCleanup' are called before tearDown
        # runs.
        self.test.addCleanup(self.logAppender, 'cleanup')
        self.test.run(self.logging_result)
        self.assertTestLogEqual(['setUp', 'runTest', 'cleanup', 'tearDown'])

    def test_add_cleanup_called_if_setUp_fails(self):
        # Cleanup functions added with 'addCleanup' are called even if setUp
        # fails. Note that tearDown has a different behavior: it is only
        # called when setUp succeeds.
        self.test.setUp = self.test.brokenSetUp
        self.test.addCleanup(self.logAppender, 'cleanup')
        self.test.run(self.logging_result)
        self.assertTestLogEqual(['brokenSetUp', 'cleanup'])

    def test_addCleanup_called_in_reverse_order(self):
        # Cleanup functions added with 'addCleanup' are called in reverse
        # order.
        #
        # One of the main uses of addCleanup is to dynamically create
        # resources that need some sort of explicit tearDown. Often one
        # resource will be created in terms of another, e.g.,
        #     self.first = self.makeFirst()
        #     self.second = self.makeSecond(self.first)
        #
        # When this happens, we generally want to clean up the second resource
        # before the first one, since the second depends on the first.
        self.test.addCleanup(self.logAppender, 'first')
        self.test.addCleanup(self.logAppender, 'second')
        self.test.run(self.logging_result)
        self.assertTestLogEqual(
            ['setUp', 'runTest', 'second', 'first', 'tearDown'])

    def test_tearDown_runs_after_cleanup_failure(self):
        # tearDown runs even if a cleanup function fails.
        self.test.addCleanup(lambda: 1/0)
        self.test.run(self.logging_result)
        self.assertTestLogEqual(['setUp', 'runTest', 'tearDown'])

    def test_cleanups_continue_running_after_error(self):
        # All cleanups are always run, even if one or two of them fail.
        self.test.addCleanup(self.logAppender, 'first')
        self.test.addCleanup(lambda: 1/0)
        self.test.addCleanup(self.logAppender, 'second')
        self.test.run(self.logging_result)
        self.assertTestLogEqual(
            ['setUp', 'runTest', 'second', 'first', 'tearDown'])

    def test_error_in_cleanups_are_captured(self):
        # If a cleanup raises an error, we want to record it and fail the the
        # test, even though we go on to run other cleanups.
        self.test.addCleanup(lambda: 1/0)
        self.test.run(self.logging_result)
        self.assertErrorLogEqual(['startTest', 'addError', 'stopTest'])

    def test_keyboard_interrupt_not_caught(self):
        # If a cleanup raises KeyboardInterrupt, it gets reraised.
        def raiseKeyboardInterrupt():
            raise KeyboardInterrupt()
        self.test.addCleanup(raiseKeyboardInterrupt)
        self.assertRaises(
            KeyboardInterrupt, self.test.run, self.logging_result)

    def test_multipleErrorsReported(self):
        # Errors from all failing cleanups are reported.
        self.test.addCleanup(lambda: 1/0)
        self.test.addCleanup(lambda: 1/0)
        self.test.run(self.logging_result)
        self.assertErrorLogEqual(
            ['startTest', 'addError', 'addError', 'stopTest'])


class TestUniqueFactories(TestCase):
    """Tests for getUniqueString and getUniqueInteger."""

    def test_getUniqueInteger(self):
        # getUniqueInteger returns an integer that increments each time you
        # call it.
        one = self.getUniqueInteger()
        self.assertEqual(1, one)
        two = self.getUniqueInteger()
        self.assertEqual(2, two)

    def test_getUniqueString(self):
        # getUniqueString returns the current test name followed by a unique
        # integer.
        name_one = self.getUniqueString()
        self.assertEqual('%s-%d' % (self._testMethodName, 1), name_one)
        name_two = self.getUniqueString()
        self.assertEqual('%s-%d' % (self._testMethodName, 2), name_two)


class TestCloneTestWithNewId(TestCase):
    """Tests for clone_test_with_new_id."""

    def test_clone_test_with_new_id(self):
        class FooTestCase(TestCase):
            def test_foo(self):
                pass
        test = FooTestCase('test_foo')
        oldName = test.id()
        newName = self.getUniqueString()
        newTest = clone_test_with_new_id(test, newName)
        self.assertEqual(newName, newTest.id())
        self.assertEqual(oldName, test.id(),
            "the original test instance should be unchanged.")


class TestSkipping(TestCase):
    """Tests for skipping of tests functionality."""

    def test_skip_causes_skipException(self):
        self.assertRaises(self.skipException, self.skip, "Skip this test")

    def test_skipException_in_setup_calls_result_addSkip(self):
        class TestThatRaisesInSetUp(TestCase):
            def setUp(self):
                self.skip("skipping this test")
            def test_that_passes(self):
                pass
        calls = []
        result = LoggingResult(calls)
        test = TestThatRaisesInSetUp("test_that_passes")
        test.run(result)
        self.assertEqual([('startTest', test),
            ('addSkip', test, "skipping this test"), ('stopTest', test)],
            calls)

    def test_skipException_in_test_method_calls_result_addSkip(self):
        class SkippingTest(TestCase):
            def test_that_raises_skipException(self):
                self.skip("skipping this test")
        calls = []
        result = LoggingResult(calls)
        test = SkippingTest("test_that_raises_skipException")
        test.run(result)
        self.assertEqual([('startTest', test),
            ('addSkip', test, "skipping this test"), ('stopTest', test)],
            calls)

    def test_skip__in_setup_with_old_result_object_calls_addError(self):
        class SkippingTest(TestCase):
            def setUp(self):
                raise self.skipException("skipping this test")
            def test_that_raises_skipException(self):
                pass
        result = unittest.TestResult()
        test = SkippingTest("test_that_raises_skipException")
        test.run(result)
        self.assertEqual(1, len(result.errors))

    def test_skip_with_old_result_object_calls_addError(self):
        class SkippingTest(TestCase):
            def test_that_raises_skipException(self):
                raise self.skipException("skipping this test")
        result = unittest.TestResult()
        test = SkippingTest("test_that_raises_skipException")
        test.run(result)
        self.assertEqual(1, len(result.errors))

    def test_skip_decorator(self):
        class SkippingTest(TestCase):
            @skip("skipping this test")
            def test_that_is_decorated_with_skip(self):
                self.fail()
        result = unittest.TestResult()
        test = SkippingTest("test_that_is_decorated_with_skip")
        test.run(result)
        self.assertEqual(1, len(result.errors))


    def test_skipIf_decorator(self):
        class SkippingTest(TestCase):
            @skipIf(True, "skipping this test")
            def test_that_is_decorated_with_skipIf(self):
                self.fail()
        result = unittest.TestResult()
        test = SkippingTest("test_that_is_decorated_with_skipIf")
        test.run(result)
        self.assertEqual(1, len(result.errors))


    def test_skipUnless_decorator(self):
        class SkippingTest(TestCase):
            @skipUnless(False, "skipping this test")
            def test_that_is_decorated_with_skipUnless(self):
                self.fail()
        result = unittest.TestResult()
        test = SkippingTest("test_that_is_decorated_with_skipUnless")
        test.run(result)
        self.assertEqual(1, len(result.errors))


def test_suite():
    from unittest import TestLoader
    return TestLoader().loadTestsFromName(__name__)