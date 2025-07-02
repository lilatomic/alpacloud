from __future__ import annotations

_registry: dict[str, Sentinel] = {}


class Sentinel:
	"""Unique sentinel values."""

	def __new__(cls, name, module_name=None):
		name = str(name)

		registry_key = f"{module_name}-{name}"

		sentinel = _registry.get(registry_key, None)
		if sentinel is not None:
			return sentinel

		sentinel = super().__new__(cls)
		sentinel._name = name
		sentinel._module_name = module_name

		return _registry.setdefault(registry_key, sentinel)

	def __repr__(self):
		return self._name

	def __reduce__(self):
		return (
			self.__class__,
			(
				self._name,
				self._module_name,
			),
		)
