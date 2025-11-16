from dataclasses import dataclass
from typing import List, Literal, Optional, Union

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
			result.append(self.consume())
		return "".join(result)


@dataclass
class StringLiteral:
	value: str


@dataclass
class FunctionCall:
	name: str
	args: List[Union[str, StringLiteral, "FunctionCall"]]


@dataclass
class StringLiteral:
	value: str


@dataclass
class RegexLiteral:
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

	def _parse_arguments(self) -> List[Union[str, StringLiteral, FunctionCall]]:
		args = []
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

	def _parse_argument(self) -> Union[str, StringLiteral, FunctionCall]:
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
			# It's a plain argument - reset and parse as string
			self.state.pos = start_pos
			return self._parse_plain_argument()

	def _parse_plain_argument(self) -> str:
		depth = 0
		result = []
		has_content = False

		while self.state.peek():
			char = self.state.peek()

			if char == "(":
				depth += 1
			elif char == ")":
				if depth == 0:
					break
				depth -= 1
			elif char == "," and depth == 0:
				break
			elif str.isspace(char) and depth == 0 and has_content:
				# Check if there's more non-whitespace content after this space
				# Save position to potentially restore
				space_start = self.state.pos
				self.state.consume_while(str.isspace)

				# If we hit a comma or closing paren, the spaces are trailing - OK
				if self.state.peek() in (",", ")", None):
					break

				# Otherwise, there's more content after spaces without a comma - ERROR
				# But we need to check if it's another identifier (which would be invalid)
				next_char = self.state.peek()
				if next_char and (next_char.isalnum() or next_char == "_"):
					raise ValueError("Expected comma or closing parenthesis")

				# Reset and continue consuming (for special chars in args)
				self.state.pos = space_start

			if not str.isspace(char):
				has_content = True

			result.append(self.state.consume())

		return "".join(result).strip()


@dataclass
class TokenTransformation:
	name: str
	function: type[Exp]
	args: list[str] | Literal["variadic"]


@dataclass
class TokenTransformer:
	transformations: dict[str, TokenTransformation]

	def transform(self, token: FunctionCall | StringLiteral) -> Exp | str:
		if isinstance(token, StringLiteral):
			return token.value

		transformer = self.transformations[token.name]
		if transformer.args == "variadic":
			return transformer.function([self.transform(e) for e in token.args])
		else:
			raw_kwargs = dict(zip(transformer.args, token.args))
			kwargs = {k: self.transform(v) for k, v in raw_kwargs.items()}
			return transformer.function(**kwargs)


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
