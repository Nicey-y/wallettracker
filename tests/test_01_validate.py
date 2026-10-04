# import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.validate import *

# pytest tests/test_01_validate.py

class TestValidateAmount:
    def test_positive_amount_pass(self):
        assert validate_amount(5) is None
        assert validate_amount(5.0) is None
        assert validate_amount('5') is None
        assert validate_amount('5.05') is None

    def test_negative_amount_fail(self):
        assert validate_amount(-5) is not None
        assert validate_amount(-5.0) is not None
        assert validate_amount('-5') is not None
        assert validate_amount('-5.05') is not None

    def test_zero_amount_fail(self):
        assert validate_amount(0) is not None
        assert validate_amount('0') is not None
        assert validate_amount('0.0') is not None

    def test_none_amount_fail(self):
        assert validate_amount(None) is not None

    def test_string_amount_fail(self):
        assert validate_amount('jehfbsjdhbf') is not None
        assert validate_amount('') is not None

    def test_very_large_amount_pass(self):
        assert validate_amount(723846) is None
        assert validate_amount('723846') is None
        assert validate_amount(723846.8726) is None
        assert validate_amount('723846.8726') is None

    def test_very_smal_amount_pass(self):
        assert validate_amount(0.723846) is None
        assert validate_amount('0.723846') is None

class TestValidateEdit:
    def test_edit_single_option_pass(self):
        assert validate_edit(20, None, None) is None
        assert validate_edit(None, 'Grocery', None) is None
        assert validate_edit(None, None, 'random note') is None

    def test_no_edit_fail(self):
        assert validate_edit(None, None, None) is not None

class TestValidateQueryLimit:
    def test_smaller_than_1_limit_fail(self):
        assert validate_entry_query_limit(-1) is not None
        assert validate_entry_query_limit(0) is not None

    def test_between_1_and_10_limit_pass(self):
        assert validate_entry_query_limit(1) is None
        assert validate_entry_query_limit(5) is None
        assert validate_entry_query_limit(10) is None

    def test_larger_than_10_limit_fail(self):
        assert validate_entry_query_limit(11) is not None
        assert validate_entry_query_limit(110) is not None

class TestValidatePeriod:
    def test_correct_period_pass(self):
        assert validate_period('daily') is None
        assert validate_period('weekly') is None
        assert validate_period('monthly') is None

    def test_incorrect_period_pass(self):
        assert validate_period('fortnightly') is not None
        assert validate_period('easfsdfse') is not None
        assert validate_period('') is not None

    def test_case_insensitive_fail(self):
        assert validate_period('Daily') is not None
        assert validate_period('WEEKLY') is not None
        assert validate_period('mOnthly') is not None

class TestValidateTimezone:
    def test_valid_timezone_pass(self):
        assert validate_timezone("Australia/Melbourne") is None

    def test_valid_utc_pass(self):
        assert validate_timezone("UTC") is None

    def test_invalid_timezone_fail(self):
        assert validate_timezone("Sydney") is not None

    def test_empty_timezone_fail(self):
        assert validate_timezone("") is not None

    def test_invalid_format_fail(self):
        assert validate_timezone("AEST") is not None