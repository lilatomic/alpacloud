from __future__ import annotations

import re

from alpacloud.eztag.multidict import MultiDict
from alpacloud.eztag.tag import TagSet


class TestTagSetHas:
	"""Tests for TagSet.has() method"""

	def test_has_returns_true_when_key_exists(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod", "region": "us-east-1"}))
		assert tagset.has("env") is True

	def test_has_returns_false_when_key_does_not_exist(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.has("region") is False

	def test_has_returns_true_when_key_exists_with_none_value(self):
		tagset = TagSet(ts=MultiDict.create({"env": None}))
		assert tagset.has("env") is True

	def test_has_with_empty_tagset(self):
		tagset = TagSet(ts=MultiDict.create({}))
		assert tagset.has("any_key") is False

	def test_has_with_empty_string_key(self):
		tagset = TagSet(ts=MultiDict.create({"": "value"}))
		assert tagset.has("") is True

	def test_has_with_multiple_values_for_key(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["prod", "staging"]}))
		assert tagset.has("env") is True


class TestTagSetMatch:
	"""Tests for TagSet.match() method"""

	def test_match_returns_true_when_key_and_value_match(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.match("env", "prod") is True

	def test_match_returns_false_when_value_does_not_match(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.match("env", "dev") is False

	def test_match_returns_false_when_key_does_not_exist(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.match("region", "us-east-1") is False

	def test_match_with_none_value(self):
		tagset = TagSet(ts=MultiDict.create({"env": None}))
		assert tagset.match("env", None) is True

	def test_match_none_value_against_string_returns_false(self):
		tagset = TagSet(ts=MultiDict.create({"env": None}))
		assert tagset.match("env", "prod") is False

	def test_match_string_value_against_none_returns_false(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.match("env", None) is False

	def test_match_with_empty_string_value(self):
		tagset = TagSet(ts=MultiDict.create({"env": ""}))
		assert tagset.match("env", "") is True

	def test_match_case_sensitive(self):
		tagset = TagSet(ts=MultiDict.create({"env": "Prod"}))
		assert tagset.match("env", "prod") is False
		assert tagset.match("env", "Prod") is True

	def test_match_with_multiple_values_matches_any(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["prod", "staging", "dev"]}))
		assert tagset.match("env", "prod") is True
		assert tagset.match("env", "staging") is True
		assert tagset.match("env", "dev") is True
		assert tagset.match("env", "test") is False

	def test_match_with_multiple_values_including_none(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["prod", None]}))
		assert tagset.match("env", "prod") is True
		assert tagset.match("env", None) is True
		assert tagset.match("env", "dev") is False


class TestTagSetRematch:
	"""Tests for TagSet.rematch() method"""

	def test_rematch_with_string_pattern_matches(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.rematch("env", "prod") is True

	def test_rematch_with_string_pattern_does_not_match(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.rematch("env", "dev") is False

	def test_rematch_with_regex_pattern_matches(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod-01"}))
		assert tagset.rematch("env", r"prod-\d+") is True

	def test_rematch_with_regex_pattern_does_not_match(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.rematch("env", r"prod-\d+") is False

	def test_rematch_with_compiled_pattern_matches(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod-01"}))
		pattern = re.compile(r"prod-\d+")
		assert tagset.rematch("env", pattern) is True

	def test_rematch_with_compiled_pattern_does_not_match(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		pattern = re.compile(r"prod-\d+")
		assert tagset.rematch("env", pattern) is False

	def test_rematch_returns_false_when_key_does_not_exist(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.rematch("region", "us-.*") is False

	def test_rematch_with_wildcard_pattern(self):
		tagset = TagSet(ts=MultiDict.create({"env": "production"}))
		assert tagset.rematch("env", "prod.*") is True

	def test_rematch_with_alternation_pattern(self):
		tagset = TagSet(ts=MultiDict.create({"env": "staging"}))
		assert tagset.rematch("env", "prod|staging|dev") is True

	def test_rematch_requires_full_match(self):
		tagset = TagSet(ts=MultiDict.create({"env": "my-prod-env"}))
		# Should not match because rematch uses fullmatch (not partial match)
		assert tagset.rematch("env", "prod") is False
		assert tagset.rematch("env", ".*prod.*") is True

	def test_rematch_with_empty_string_pattern(self):
		tagset = TagSet(ts=MultiDict.create({"env": ""}))
		assert tagset.rematch("env", "") is True

	def test_rematch_with_special_regex_characters(self):
		tagset = TagSet(ts=MultiDict.create({"version": "1.2.3"}))
		# Without escaping, '.' matches any character
		assert tagset.rematch("version", r"1.2.3") is True
		# With proper escaping
		assert tagset.rematch("version", r"1\.2\.3") is True

	def test_rematch_case_sensitive_by_default(self):
		tagset = TagSet(ts=MultiDict.create({"env": "Prod"}))
		assert tagset.rematch("env", "prod") is False
		assert tagset.rematch("env", "Prod") is True

	def test_rematch_with_case_insensitive_pattern(self):
		tagset = TagSet(ts=MultiDict.create({"env": "Prod"}))
		pattern = re.compile("prod", re.IGNORECASE)
		assert tagset.rematch("env", pattern) is True

	def test_rematch_with_none_value_returns_false(self):
		tagset = TagSet(ts=MultiDict.create({"env": None}))
		# None values should be skipped
		assert tagset.rematch("env", "prod") is False

	def test_rematch_with_multiple_values_matches_any(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["prod-01", "staging-02", "dev-03"]}))
		assert tagset.rematch("env", r"prod-\d+") is True
		assert tagset.rematch("env", r"staging-\d+") is True
		assert tagset.rematch("env", r"dev-\d+") is True
		assert tagset.rematch("env", r"test-\d+") is False

	def test_rematch_with_multiple_values_one_matches(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["production", "prod-01", "my-env"]}))
		# Should match because at least one value matches
		assert tagset.rematch("env", r"prod-\d+") is True

	def test_rematch_with_multiple_values_including_none(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["prod-01", None, "staging"]}))
		# Should skip None and still find matches
		assert tagset.rematch("env", r"prod-\d+") is True
		assert tagset.rematch("env", "staging") is True


class TestTagSetContains:
	"""Tests for TagSet.contains() method"""

	def test_contains_returns_true_when_substring_exists(self):
		tagset = TagSet(ts=MultiDict.create({"env": "production"}))
		assert tagset.contains("env", "prod") is True

	def test_contains_returns_false_when_substring_does_not_exist(self):
		tagset = TagSet(ts=MultiDict.create({"env": "production"}))
		assert tagset.contains("env", "dev") is False

	def test_contains_returns_false_when_key_does_not_exist(self):
		tagset = TagSet(ts=MultiDict.create({"env": "production"}))
		assert tagset.contains("region", "us") is False

	def test_contains_with_exact_match(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		assert tagset.contains("env", "prod") is True

	def test_contains_with_empty_substring(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod"}))
		# Empty string is contained in any string
		assert tagset.contains("env", "") is True

	def test_contains_with_empty_string_value(self):
		tagset = TagSet(ts=MultiDict.create({"env": ""}))
		assert tagset.contains("env", "") is True
		assert tagset.contains("env", "anything") is False

	def test_contains_with_none_value_returns_false(self):
		tagset = TagSet(ts=MultiDict.create({"env": None}))
		assert tagset.contains("env", "prod") is False

	def test_contains_case_sensitive(self):
		tagset = TagSet(ts=MultiDict.create({"env": "Production"}))
		assert tagset.contains("env", "Prod") is True
		assert tagset.contains("env", "prod") is False

	def test_contains_with_substring_at_start(self):
		tagset = TagSet(ts=MultiDict.create({"env": "production-east"}))
		assert tagset.contains("env", "prod") is True

	def test_contains_with_substring_at_end(self):
		tagset = TagSet(ts=MultiDict.create({"env": "my-prod"}))
		assert tagset.contains("env", "prod") is True

	def test_contains_with_substring_in_middle(self):
		tagset = TagSet(ts=MultiDict.create({"env": "my-prod-env"}))
		assert tagset.contains("env", "prod") is True

	def test_contains_with_multiple_occurrences(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod-prod-prod"}))
		assert tagset.contains("env", "prod") is True

	def test_contains_with_special_characters(self):
		tagset = TagSet(ts=MultiDict.create({"version": "v1.2.3-beta"}))
		assert tagset.contains("version", "1.2") is True
		assert tagset.contains("version", "-beta") is True
		assert tagset.contains("version", ".") is True

	def test_contains_with_whitespace(self):
		tagset = TagSet(ts=MultiDict.create({"description": "prod environment"}))
		assert tagset.contains("description", "prod env") is True
		assert tagset.contains("description", " ") is True

	def test_contains_does_not_treat_substring_as_regex(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod123"}))
		# The substring is literal, not a regex pattern
		assert tagset.contains("env", r"\d+") is False
		assert tagset.contains("env", "prod") is True
		assert tagset.contains("env", "123") is True

	def test_contains_with_multiple_values_matches_any(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["production", "staging", "development"]}))
		assert tagset.contains("env", "prod") is True
		assert tagset.contains("env", "stag") is True
		assert tagset.contains("env", "dev") is True
		assert tagset.contains("env", "test") is False

	def test_contains_with_multiple_values_one_matches(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["my-env", "production", "other"]}))
		# Should match because at least one value contains the substring
		assert tagset.contains("env", "prod") is True

	def test_contains_with_multiple_values_including_none(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["production", None, "staging"]}))
		# Should skip None and still find matches
		assert tagset.contains("env", "prod") is True
		assert tagset.contains("env", "stag") is True


class TestTagSetIntegration:
	"""Integration tests for TagSet"""

	def test_tagset_with_multiple_operations(self):
		tagset = TagSet(ts=MultiDict.create({"env": "prod", "region": "us-east-1", "version": "1.2.3", "team": "platform"}))

		assert tagset.has("env")
		assert tagset.match("env", "prod")
		assert tagset.rematch("region", r"us-.*")
		assert tagset.rematch("version", r"\d+\.\d+\.\d+")
		assert tagset.contains("region", "east")
		assert tagset.contains("team", "plat")
		assert not tagset.has("missing_key")

	def test_tagset_empty_initialization(self):
		tagset = TagSet(ts=MultiDict.create({}))
		assert not tagset.has("any_key")

	def test_contains_vs_match_vs_rematch(self):
		tagset = TagSet(ts=MultiDict.create({"env": "my-prod-environment"}))

		# match requires exact equality
		assert not tagset.match("env", "prod")
		assert tagset.match("env", "my-prod-environment")

		# contains checks for substring
		assert tagset.contains("env", "prod")
		assert tagset.contains("env", "environment")

		# rematch requires full regex match
		assert not tagset.rematch("env", "prod")
		assert tagset.rematch("env", r".*prod.*")
		assert tagset.rematch("env", r"my-\w+-environment")

	def test_tagset_with_multiple_values_per_key(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["prod", "staging"], "region": ["us-east-1", "us-west-2"]}))

		# has() checks key existence
		assert tagset.has("env")
		assert tagset.has("region")

		# match() returns True if ANY value matches
		assert tagset.match("env", "prod")
		assert tagset.match("env", "staging")
		assert not tagset.match("env", "dev")

		# rematch() returns True if ANY value matches
		assert tagset.rematch("region", r"us-.*")
		assert tagset.rematch("region", r".*east.*")
		assert tagset.rematch("region", r".*west.*")

		# contains() returns True if ANY value contains substring
		assert tagset.contains("env", "prod")
		assert tagset.contains("env", "stag")
		assert tagset.contains("region", "east")
		assert tagset.contains("region", "west")

	def test_mixed_none_and_string_values(self):
		tagset = TagSet(ts=MultiDict.create({"env": ["prod", None, "staging"]}))

		assert tagset.has("env")
		assert tagset.match("env", "prod")
		assert tagset.match("env", None)
		assert tagset.match("env", "staging")

		# rematch and contains should skip None values
		assert tagset.rematch("env", "prod")
		assert tagset.contains("env", "prod")
