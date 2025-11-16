from dataclasses import dataclass

import pytest

from alpacloud.eztag import logic
from alpacloud.eztag.parser import Parser, FunctionCall, ParseState, StringLiteral, transformer, TokenTransformation, TokenTransformer, RegexLiteral


class TestParseState:
	"""Tests for ParseState helper class."""

	def test_peek_at_beginning(self):
		state = ParseState("hello")
		assert state.peek() == 'h'
		assert state.pos == 0  # peek doesn't advance

	def test_peek_at_end(self):
		state = ParseState("hi", pos=2)
		assert state.peek() is None

	def test_consume_advances_position(self):
		state = ParseState("hello")
		assert state.consume() == 'h'
		assert state.pos == 1
		assert state.consume() == 'e'
		assert state.pos == 2

	def test_consume_at_end_returns_none(self):
		state = ParseState("a", pos=1)
		assert state.consume() is None

	def test_consume_while_with_predicate(self):
		state = ParseState("abc123")
		result = state.consume_while(str.isalpha)
		assert result == "abc"
		assert state.pos == 3

	def test_consume_while_returns_empty_on_no_match(self):
		state = ParseState("123")
		result = state.consume_while(str.isalpha)
		assert result == ""
		assert state.pos == 0


class TestStringLiteral:
	"""Tests for StringLiteral parsing."""

	def test_single_string_literal(self):
		parser = Parser("func(arg1)")
		result = parser.parse()
		assert result == FunctionCall("func", [StringLiteral("arg1")])

	def test_multiple_string_literals(self):
		parser = Parser("func(arg1, arg2, arg3)")
		result = parser.parse()
		assert result == FunctionCall("func", [
			StringLiteral("arg1"),
			StringLiteral("arg2"),
			StringLiteral("arg3")
		])

	def test_string_literal_with_numbers(self):
		parser = Parser("func(arg123)")
		result = parser.parse()
		assert result == FunctionCall("func", [StringLiteral("arg123")])

	def test_string_literal_with_underscore(self):
		parser = Parser("func(my_arg)")
		result = parser.parse()
		assert result == FunctionCall("func", [StringLiteral("my_arg")])

	def test_string_literal_with_spaces(self):
		parser = Parser("func( arg1 )")
		result = parser.parse()
		assert result == FunctionCall("func", [StringLiteral("arg1")])

	def test_mixed_string_literals_and_function_calls(self):
		parser = Parser("func(arg1, nested(), arg2)")
		result = parser.parse()
		assert result == FunctionCall("func", [
			StringLiteral("arg1"),
			FunctionCall("nested", []),
			StringLiteral("arg2")
		])

	def test_string_literal_in_nested_function(self):
		parser = Parser("outer(inner(literal))")
		result = parser.parse()
		assert result == FunctionCall("outer", [
			FunctionCall("inner", [StringLiteral("literal")])
		])

	def test_multiple_string_literals_nested(self):
		parser = Parser("func(a, b(c, d), e)")
		result = parser.parse()
		assert result == FunctionCall("func", [
			StringLiteral("a"),
			FunctionCall("b", [StringLiteral("c"), StringLiteral("d")]),
			StringLiteral("e")
		])


class TestParser:
	"""Tests for Parser class."""

	def test_simple_function_no_args(self):
		parser = Parser("func()")
		result = parser.parse()
		assert result == FunctionCall("func", [])

	def test_function_with_single_arg(self):
		parser = Parser("func(arg1)")
		result = parser.parse()
		assert result == FunctionCall("func", [StringLiteral("arg1")])

	def test_function_with_multiple_args(self):
		parser = Parser("func(arg1, arg2, arg3)")
		result = parser.parse()
		assert result == FunctionCall("func", [
			StringLiteral("arg1"),
			StringLiteral("arg2"),
			StringLiteral("arg3")
		])

	def test_function_with_numeric_args(self):
		parser = Parser("add(123, 456)")
		result = parser.parse()
		assert result == FunctionCall("add", [StringLiteral("123"), StringLiteral("456")])

	def test_function_with_nested_function_call(self):
		parser = Parser("func(nested(inner), arg2)")
		result = parser.parse()
		expected = FunctionCall("func", [
			FunctionCall("nested", [StringLiteral("inner")]),
			StringLiteral("arg2")
		])
		assert result == expected

	def test_function_with_deeply_nested_function_calls(self):
		parser = Parser("func(a(b(c)), d)")
		result = parser.parse()
		expected = FunctionCall("func", [
			FunctionCall("a", [FunctionCall("b", [StringLiteral("c")])]),
			StringLiteral("d")
		])
		assert result == expected

	def test_function_with_spaces(self):
		parser = Parser("func( arg1 , arg2 )")
		result = parser.parse()
		assert result == FunctionCall("func", [
			StringLiteral("arg1"),
			StringLiteral("arg2")
		])

	def test_function_with_leading_trailing_spaces(self):
		parser = Parser("  func(arg)  ")
		result = parser.parse()
		assert result == FunctionCall("func", [StringLiteral("arg")])

	def test_function_with_underscore_in_name(self):
		parser = Parser("my_func(arg)")
		result = parser.parse()
		assert result == FunctionCall("my_func", [StringLiteral("arg")])

	def test_function_with_numbers_in_name(self):
		parser = Parser("func123(arg)")
		result = parser.parse()
		assert result == FunctionCall("func123", [StringLiteral("arg")])

	def test_empty_string_raises_error(self):
		parser = Parser("")
		with pytest.raises(ValueError, match="Expected function name"):
			parser.parse()

	def test_missing_opening_paren_raises_error(self):
		parser = Parser("func")
		with pytest.raises(ValueError, match="Expected opening parenthesis"):
			parser.parse()

	def test_missing_closing_paren_raises_error(self):
		parser = Parser("func(arg")
		with pytest.raises(ValueError, match="Expected.*closing parenthesis"):
			parser.parse()

	def test_missing_comma_between_args_raises_error(self):
		parser = Parser("func(arg1 arg2)")
		with pytest.raises(ValueError, match="Expected comma or closing parenthesis"):
			parser.parse()

	def test_function_with_empty_arg_between_commas(self):
		parser = Parser("func(arg1, , arg2)")
		result = parser.parse()
		# Empty string is a valid argument
		assert result == FunctionCall("func", [
			StringLiteral("arg1"),
			"",
			StringLiteral("arg2")
		])

	def test_complex_nested_example(self):
		parser = Parser("outer(inner1(a, b), inner2(c), d)")
		result = parser.parse()
		expected = FunctionCall("outer", [
			FunctionCall("inner1", [StringLiteral("a"), StringLiteral("b")]),
			FunctionCall("inner2", [StringLiteral("c")]),
			StringLiteral("d")
		])
		assert result == expected

	def test_function_with_special_chars_in_args(self):
		parser = Parser("func(arg-1, arg.2, arg@3)")
		result = parser.parse()
		assert result == FunctionCall("func", [StringLiteral(value='arg-1'), StringLiteral(value='arg.2'), StringLiteral(value='arg@3')])

	def test_multiple_nested_levels(self):
		parser = Parser("f1(f2(f3(f4())), x)")
		result = parser.parse()
		expected = FunctionCall("f1", [
			FunctionCall("f2", [
				FunctionCall("f3", [
					FunctionCall("f4", [])
				])
			]),
			StringLiteral("x")
		])
		assert result == expected

	def test_nested_function_with_no_args(self):
		parser = Parser("outer(inner())")
		result = parser.parse()
		expected = FunctionCall("outer", [FunctionCall("inner", [])])
		assert result == expected

	def test_multiple_nested_functions_as_args(self):
		parser = Parser("func(a(), b(), c())")
		result = parser.parse()
		expected = FunctionCall("func", [
			FunctionCall("a", []),
			FunctionCall("b", []),
			FunctionCall("c", [])
		])
		assert result == expected

	def test_nested_with_mixed_args(self):
		parser = Parser("outer(x, inner(y), z)")
		result = parser.parse()
		expected = FunctionCall("outer", [
			StringLiteral("x"),
			FunctionCall("inner", [StringLiteral("y")]),
			StringLiteral("z")
		])
		assert result == expected

	def test_deeply_nested_with_multiple_args(self):
		parser = Parser("a(b(c(d, e), f), g)")
		result = parser.parse()
		expected = FunctionCall("a", [
			FunctionCall("b", [
				FunctionCall("c", [StringLiteral("d"), StringLiteral("e")]),
				StringLiteral("f")
			]),
			StringLiteral("g")
		])
		assert result == expected

	def test_string_literal_starts_with_number(self):
		# Numbers at start mean it's not a valid identifier, so it's a plain arg
		parser = Parser("func(123abc)")
		result = parser.parse()
		assert result == FunctionCall("func", [StringLiteral("123abc")])

	def test_all_string_literals_in_complex_expr(self):
		parser = Parser("and(or(a, b), not(c))")
		result = parser.parse()
		expected = FunctionCall("and", [
			FunctionCall("or", [StringLiteral("a"), StringLiteral("b")]),
			FunctionCall("not", [StringLiteral("c")])
		])
		assert result == expected

	def test_regex_literal(self):
		parser = Parser("match(k, /v/)")
		result = parser.parse()
		assert result == FunctionCall("match", [StringLiteral("k"), RegexLiteral("v")])

	def test_regex_literal_with_nesting(self):
		parser = Parser("match(k, /match(k, v)/)")
		result = parser.parse()
		assert result == FunctionCall("match", [StringLiteral("k"), RegexLiteral("match(k, v)")])


@dataclass
class FakeItem:
	k: str
	v: str = "default"


class TestTransformer:
	"""Tests for Transformer class."""

	def test_simple_function(self):
		assert transformer.transform(FunctionCall("NOT", [StringLiteral("x")])) == logic.Not_("x")

	def test_variadic_function(self):
		assert transformer.transform(FunctionCall("AND", [StringLiteral("a"), StringLiteral("b"), StringLiteral("c")])) == logic.And_(["a", "b", "c"])

	def test_multiple_args(self):
		assert transformer.transform(FunctionCall("MATCH", [StringLiteral("k"), StringLiteral("v")])) == logic.TagMatch("k", "v")

	def test_multiple_with_default(self):
		assert TokenTransformer({
			"TEST": TokenTransformation("TEST", FakeItem, ["k", "v"])
		}).transform(FunctionCall("TEST", [StringLiteral("k")])) == FakeItem("k")

	def test_recursive(self):
		assert transformer.transform(FunctionCall("AND", [FunctionCall("NOT", [StringLiteral("x")])])) == logic.And_([logic.Not_("x")])