from pathlib import Path
from textwrap import dedent

from alpacloud.lens.conftest import ResourceLoader
from alpacloud.promls.fetch import Parser


class TestParserDataline:
	def test_counter(self):
		l = r'http_request_count{method="post",code="200"} 1027 1395066363000'
		r = Parser.parse_data_line(l)
		assert r == Parser.DataLine(
			"http_request_count",
			{
				"method": "post",
				"code": "200",
			},
			"1027",
			1395066363000,
		)

	def test_no_labels(self):
		l = r"metric_without_timestamp_and_labels 12.47"
		r = Parser.parse_data_line(l)
		assert r == Parser.DataLine("metric_without_timestamp_and_labels", {}, "12.47")

	def test_histogram_quantile(self):
		l = r'telemetry_requests_metrics_latency_microseconds{quantile="0.05"} 3272'
		r = Parser.parse_data_line(l)
		assert r == Parser.DataLine(
			"telemetry_requests_metrics_latency_microseconds",
			{
				"quantile": "0.05",
			},
			"3272",
		)

	def test_histogram_sum(self):
		l = r"telemetry_requests_metrics_latency_microseconds_sum 1.7560473e+07"
		r = Parser.parse_data_line(l)
		assert r == Parser.DataLine("telemetry_requests_metrics_latency_microseconds_sum", {}, "1.7560473e+07")


class TestParserMetaLine:
	def test_help(self):
		l = "# HELP telemetry_requests_metrics_latency_microseconds A histogram of the response latency."
		r = Parser.parse_meta_line(l)
		assert r == Parser.MetaLine("telemetry_requests_metrics_latency_microseconds", Parser.MetaKind.HELP, "A histogram of the response latency.")

	def test_type(self):
		l = "# TYPE telemetry_requests_metrics_latency_microseconds summary"
		r = Parser.parse_meta_line(l)
		assert r == Parser.MetaLine("telemetry_requests_metrics_latency_microseconds", Parser.MetaKind.TYPE, "summary")

	def test_comment(self):
		l = "# Finally a summary, which has a pretty complex representation in the text format:"
		r = Parser.parse_meta_line(l)
		assert r == Parser.MetaLine("COMMENT", Parser.MetaKind.COMMENT, "Finally a summary, which has a pretty complex representation in the text format:")

class TestParseAll:
	def test_doc_sample(self):
		# TODO: support for escaped values
		# """
		# # Escaping in label values:
		# msdos_file_access_time_ms{path="C:\\DIR\\FILE.TXT",error="Cannot find file:\n\"FILE.TXT\""} 1.234e3
		# # A weird metric from before the epoch:
		# something_weird{problem="division by zero"} +Inf -3982045
		# """
		l = ("""\
# HELP api_http_request_count The total number of HTTP requests.
# TYPE api_http_request_count counter
http_request_count{method="post",code="200"} 1027 1395066363000
http_request_count{method="post",code="400"}    3 1395066363000
# Minimalistic line:
metric_without_timestamp_and_labels 12.47
# Finally a summary, which has a pretty complex representation in the text format:
# HELP telemetry_requests_metrics_latency_microseconds A histogram of the response latency.
# TYPE telemetry_requests_metrics_latency_microseconds summary
telemetry_requests_metrics_latency_microseconds{quantile="0.01"} 3102
telemetry_requests_metrics_latency_microseconds{quantile="0.05"} 3272
telemetry_requests_metrics_latency_microseconds{quantile="0.5"} 4773
telemetry_requests_metrics_latency_microseconds{quantile="0.9"} 9001
telemetry_requests_metrics_latency_microseconds{quantile="0.99"} 76656
telemetry_requests_metrics_latency_microseconds_sum 1.7560473e+07
telemetry_requests_metrics_latency_microseconds_count 2693
		""")
		r = Parser().parse(l.split("\n"))
		assert len(r) == 7

	def test_certmanager_sample(self):
		r = ResourceLoader(Path(__file__).parent / "test_resources").load_raw("certmanager.prom")
		assert len(Parser().parse(r.split("\n"))) == 48
