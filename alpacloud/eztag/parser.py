"""
Parse filter expressions into predicates for filtering tags.

The grammar is as follows:
regex_literal := "/" regex "/"
string_literal := any characters except "(),/" and spaces
expr := identifier(expr [, expr])* | regex_literal | string_literal
identifier := "and" | "or" | "not" | "has" | "match" | "re" | "contains"
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import List, Literal, Optional

from alpacloud.eztag import logic
from alpacloud.eztag.logic import Expr


@dataclass
class ParseState:
	"""State of the parser"""

	text: str
	pos: int = 0

	def peek(self) -> Optional[str]:
		"""Look at the next character in the input text without consuming it"""
		return self.text[self.pos] if self.pos < len(self.text) else None

	def consume(self) -> Optional[str]:
		"""Consume the next character from the input text"""
		if self.pos >= len(self.text):
			return None
		char = self.text[self.pos]
		self.pos += 1
		return char

	def consume_while(self, predicate) -> str:
		"""
		Consume characters from the input text while the predicate is True
		"""
		result = []
		while self.peek() and predicate(self.peek()):
			next_result = self.consume()
			if next_result is not None:
				result.append(next_result)
		return "".join(result)


class ASTNode(abc.ABC):
	"""Abstract base class for AST nodes"""


@dataclass
class StringLiteral(ASTNode):
	"""AST node representing a string literal"""

	value: str


@dataclass
class FunctionCall(ASTNode):
	"""AST node representing a function call. Everything that isn't a literal is a function call."""

	name: str
	args: list[ASTNode]


@dataclass
class RegexLiteral(ASTNode):
	"""AST node representing a regex literal"""

	value: str


class Parser:
	"""Parses a filter expression into an AST"""

	reserved_chars = set("(),/")

	def __init__(self, text: str):
		self.state = ParseState(text.strip())

	def parse(self) -> FunctionCall:
		"""
		Parse a filter expression into an AST
		"""
		return self._parse_function_call()

	def _parse_function_call(self) -> FunctionCall:
		name = self._parse_identifier()
		if not name:
			raise ValueError("Expected function name")

		if self.state.peek() != "(":
			raise ValueError("Expected opening parenthesis")
		self.state.consume()  # consume '('

		args = self._parse_arguments()

		if self.state.peek() != ")":
			raise ValueError("Expected closing parenthesis")
		self.state.consume()  # consume ')'

		return FunctionCall(name, args)

	def _parse_identifier(self) -> str:
		return self.state.consume_while(lambda c: c not in self.reserved_chars and not c.isspace())

	def _parse_arguments(self) -> List[ASTNode]:
		args: List[ASTNode] = []
		while True:
			self.state.consume_while(str.isspace)

			if self.state.peek() == ")":
				break

			if self.state.peek() == "/":
				args.append(self._parse_regex())
			else:
				args.append(self._parse_argument())

			self.state.consume_while(str.isspace)
			if self.state.peek() == ",":
				self.state.consume()
			elif self.state.peek() != ")":
				raise ValueError("Expected comma or closing parenthesis")

		return args

	def _parse_regex(self) -> RegexLiteral:
		self.state.consume()
		v = RegexLiteral(self.state.consume_while(lambda c: c != "/"))
		self.state.consume()
		return v

	def _parse_argument(self) -> ASTNode:
		self.state.consume_while(str.isspace)

		# Check if this argument is a function call or string literal
		start_pos = self.state.pos
		identifier = self._parse_identifier()

		if identifier and self.state.peek() == "(":
			# It's a nested function call - parse it recursively
			self.state.pos = start_pos  # Reset position
			return self._parse_function_call()
		elif identifier:
			# It's a string literal (identifier not followed by '(')
			# Check that we're at a valid stopping point
			self.state.consume_while(str.isspace)
			next_char = self.state.peek()
			if next_char not in (",", ")", None):
				raise ValueError("Expected comma or closing parenthesis")
			return StringLiteral(identifier)
		else:
			raise ValueError("Expected identifier")


@dataclass
class TokenTransformation:
	"""
	Associates the name of a function with the Expr implementing functionality.

	The `args` field associates positional arguments in the raw filter expression with the function's keyword arguments.
	For example, MATCH takes a key (k) and a value (v), so `args = ["k", "v"]`.
	For functions that take a variable number of arguments, such as AND and OR, `args = "variadic"`.
	"""

	name: str
	function: type[Expr]
	args: list[str] | Literal["variadic"]


class TokenTransformer:
	"""Transforms AST nodes into Exprs"""

	def __init__(self, transformations: dict[str, TokenTransformation], case_sensitive_tokens: bool = False):
		self.case_sensitive_tokens = case_sensitive_tokens
		if case_sensitive_tokens:
			self.transformations = transformations
		else:
			self.transformations = {k.lower(): v for k, v in transformations.items()}

	def transform(self, token: ASTNode) -> Expr | str:
		"""Transform an AST node into an Expr"""
		match token:
			case StringLiteral():
				return token.value
			case RegexLiteral():
				return token.value
			case FunctionCall():
				if self.case_sensitive_tokens:
					transformation = self.transformations[token.name]
				else:
					transformation = self.transformations[token.name.lower()]

				if transformation.args == "variadic":
					return transformation.function([self.transform(e) for e in token.args])  # type: ignore # the typesafety is done by the TokenTransformation
				else:
					raw_kwargs = dict(zip(transformation.args, token.args))
					kwargs = {k: self.transform(v) for k, v in raw_kwargs.items()}
					return transformation.function(**kwargs)
			case _:
				raise ValueError(f"Unexpected token: {token} of type {type(token)}")

	def extended(self, more_transformers: dict[str, TokenTransformation]) -> TokenTransformer:
		"""Make a new TokenTransformer with additional transformations. New transformations take precedence over existing ones."""
		return TokenTransformer({**self.transformations, **more_transformers}, self.case_sensitive_tokens)


transformer = TokenTransformer(
	{
		e.name: e
		for e in [
			TokenTransformation("NOT", logic.Not_, ["cond"]),
			TokenTransformation("AND", logic.And_, "variadic"),
			TokenTransformation("OR", logic.Or_, "variadic"),
			TokenTransformation("HAS", logic.TagHas, ["k"]),
			TokenTransformation("MATCH", logic.TagMatch, ["k", "v"]),
			TokenTransformation("RE", logic.TagRematch, ["k", "v"]),
			TokenTransformation("CONTAINS", logic.TagContains, ["k", "v"]),
		]
	}
)
