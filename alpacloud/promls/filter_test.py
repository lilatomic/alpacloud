import re

from alpacloud.promls.filter import filter_name
from alpacloud.promls.metrics import Metric


class TestFilterName:
	def test_matches_when_pattern_in_name(self):
		predicate = filter_name(re.compile("foo"))
		metric = Metric("my_foo_metric", "", "counter")
		assert predicate(metric) is True

	def test_does_not_match_when_not_in_name(self):
		predicate = filter_name(re.compile("foo"))
		metric = Metric("bar_baz", "", "gauge")
		assert predicate(metric) is False

	def test_case_sensitive_by_default(self):
		predicate = filter_name(re.compile("FOO"))
		metric = Metric("foo_metric", "", "counter")
		assert predicate(metric) is False

	def test_case_insensitive_with_flag(self):
		predicate = filter_name(re.compile("FOO", re.IGNORECASE))
		metric = Metric("foo_metric", "", "counter")
		assert predicate(metric) is True

	def test_regex_special_characters(self):
		# unescaped dot matches any char
		predicate_any = filter_name(re.compile(r"foo.bar"))
		assert predicate_any(Metric("fooXbar", "", "counter")) is True
		assert predicate_any(Metric("foobar", "", "counter")) is False

		# escaped dot matches literal dot
		predicate_literal = filter_name(re.compile(r"foo\.bar"))
		assert predicate_literal(Metric("foo.bar", "", "counter")) is True
		assert predicate_literal(Metric("fooXbar", "", "counter")) is False

	def test_empty_pattern_matches_everything(self):
		predicate = filter_name(re.compile(""))
		assert predicate(Metric("anything_goes", "", "counter")) is True

	def test_search_ignores_helptext(self):
		predicate = filter_name(re.compile("foo"))
		metric = Metric("no", "foo", "counter")
		assert predicate(metric) is False


class TestFilterAny:
	def test_matches_when_pattern_in_name(self):
		from filter import filter_any

		predicate = filter_any(re.compile("latency"))
		assert predicate(Metric("http_latency_seconds", "HTTP request latency", "histogram")) is True

	def test_matches_when_pattern_in_help(self):
		from filter import filter_any

		predicate = filter_any(re.compile(r"request latency"))
		assert predicate(Metric("http_seconds", "HTTP request latency", "histogram")) is True

	def test_does_not_match_when_neither_name_nor_help_match(self):
		from filter import filter_any

		predicate = filter_any(re.compile("throughput"))
		assert predicate(Metric("http_latency_seconds", "HTTP request latency", "histogram")) is False

	def test_case_insensitive_with_flag(self):
		from filter import filter_any

		predicate = filter_any(re.compile("LATENCY", re.IGNORECASE))
		assert predicate(Metric("http_latency_seconds", "HTTP request latency", "histogram")) is True

	def test_empty_pattern_matches_everything(self):
		from filter import filter_any

		predicate = filter_any(re.compile(""))
		assert predicate(Metric("anything", "and everything", "counter")) is True


class TestFilterPath:
	def test_matches_prefix_path(self):
		from filter import filter_path

		predicate = filter_path(["http", "server"])
		assert predicate(Metric("http_server_requests_total", "Total HTTP server requests", "counter")) is True

	def test_does_not_match_when_prefix_not_at_start(self):
		from filter import filter_path

		predicate = filter_path(["http", "server"])
		assert predicate(Metric("xhttp_server_requests_total", "prefixed with x", "counter")) is False

	def test_does_not_match_different_prefix(self):
		from filter import filter_path

		predicate = filter_path(["http", "server"])
		assert predicate(Metric("http_client_requests_total", "client metric", "counter")) is False

	def test_exact_match(self):
		from filter import filter_path

		predicate = filter_path(["http", "server"])
		assert predicate(Metric("http_server", "exact match", "gauge")) is True

	def test_longer_path_matches(self):
		from filter import filter_path

		predicate = filter_path(["a", "b", "c"])
		assert predicate(Metric("a_b_c_d", "longer metric name", "counter")) is True

	def test_case_sensitive_by_default(self):
		from filter import filter_path

		predicate = filter_path(["HTTP", "server"])
		assert predicate(Metric("http_server_requests_total", "lowercase name", "counter")) is False
