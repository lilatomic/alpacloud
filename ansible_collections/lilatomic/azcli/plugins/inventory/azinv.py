from dataclasses import dataclass, field
from typing import List, Optional

from ansible.plugins.inventory import BaseInventoryPlugin
from llamazure.azgraph.azgraph import Graph


@dataclass
class Subscription:
	uuid: str
	rgs: field(default_factory=list)


@dataclass
class ResourceGroup:
	name: str
	vms: field(default_factory=list)


@dataclass
class VM:
	name: str
	info: field(default_factory=dict)


@dataclass
class Filter:
	sub: Optional[str] = None
	rg: Optional[str] = None
	vm: Optional[str] = None

	def to_kusto(self) -> Optional[str]:
		qb = []  # query builder
		if self.sub:
			qb.append(f'subscriptionId == "{self.sub}')
		if self.rg:
			qb.append(f'resourceGroup == "{self.rg}"')
		if self.vm:
			qb.append(f'name == "{self.vm}"')

		if not qb:
			return None
		return "(" + " and ".join(qb) + ")"


class InventoryModule(BaseInventoryPlugin):
	NAME = "lilatomic.azcli.azinv"

	def parse(self, inventory, loader, path, cache=True):
		super(InventoryModule, self).parse(inventory, loader, path, cache)

		config = self._read_config_data(path)
		raw_subs = self.get_option("subscriptions")

		filters = self.parse_subscriptions_to_filters(raw_subs)
		rendered_filters = list(filter(None, [f.to_kusto() for f in filters]))

		predicate_str = " or ".join(rendered_filters)
		query = f"Resources | where {predicate_str}"

		credential = "???"
		graph = Graph.from_credential(credential)
		graph.q(query)

	@staticmethod
	def parse_subscriptions_to_filters(raw_subs) -> List[Optional[Filter]]:
		"""Parse the raw option into the representation of the filters"""
		filters: List[Filter] = []
		for sub_name, sub_targets in raw_subs.items():
			if sub_targets is None or sub_targets == "*":
				filters.append(Filter(sub_name))
			else:
				for rg_name, rg_targets in sub_targets.items():
					if rg_targets is None or rg_targets == "*":
						filters.append(Filter(sub_name, rg_name))
					else:
						for vm_name in rg_targets:
							filters.append(Filter(sub_name, rg_name, vm_name))

		return filters
