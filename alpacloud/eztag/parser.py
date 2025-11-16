import abc
from dataclasses import dataclass
from typing import List, Literal, Optional

from alpacloud.eztag import logic
from alpacloud.eztag.logic import Exp


@dataclass
class ParseState:
	text: str
	pos: int = 0

	def peek(self) -> Optional[str]:
		return self.text[self.pos] if self.pos < len(self.text) else None

	def consume(self) -> Optional[str]:
		if self.pos >= len(self.text):
			return None
		char = self.text[self.pos]
		self.pos += 1
		return char

	def consume_while(self, predicate) -> str:
		result = []
		while self.peek() and predicate(self.peek()):
			next_result = self.consume()
			if next_result is not None:
				result.append(next_result)
		return "".join(result)


class ASTNode(abc.ABC):
	pass


@dataclass
class StringLiteral(ASTNode):
	value: str


@dataclass
class FunctionCall(ASTNode):
	name: str
	args: List[ASTNode]


@dataclass
class RegexLiteral(ASTNode):
	value: str


class Parser:
	reserved_chars = set("(),/")

	def __init__(self, text: str):
		self.state = ParseState(text.strip())

	def parse(self) -> FunctionCall:
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
	name: str
	function: type[Exp]
	args: list[str] | Literal["variadic"]


@dataclass
class TokenTransformer:
	transformations: dict[str, TokenTransformation]

	def transform(self, token: ASTNode) -> Exp | str:
		match token:
			case StringLiteral():
				return token.value
			case RegexLiteral():
				return token.value
			case FunctionCall():
				transformer = self.transformations[token.name]
				if transformer.args == "variadic":
					return transformer.function([self.transform(e) for e in token.args])  # type: ignore # the typesafety is done by the TokenTransformation
				else:
					raw_kwargs = dict(zip(transformer.args, token.args))
					kwargs = {k: self.transform(v) for k, v in raw_kwargs.items()}
					return transformer.function(**kwargs)
			case _:
				raise ValueError(f"Unexpected token: {token} of type {type(token)}")


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
