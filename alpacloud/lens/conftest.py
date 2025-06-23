from dataclasses import dataclass


@dataclass
class StrStartsWith:
	tgt: str
	s: str

	def check(self) -> bool:
		status = self.s.startswith(self.tgt)
		if not status:
			print(f"{self.tgt} is not {self.s}")

		return status
