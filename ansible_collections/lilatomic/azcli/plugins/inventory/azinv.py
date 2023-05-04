from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from llamazure.azgraph.azgraph import Graph
from llamazure.azgraph.models import Res
from pydantic import BaseModel, Extra


@dataclass
class VMReq:
	name: str


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
		query = self.render_filters(filters)

		credential = "???"
		graph = Graph.from_credential(credential)
		graph_result = graph.q(query)


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
						for raw_vm in rg_targets:
							vm = VMReq(**raw_vm)
							filters.append(Filter(sub_name, rg_name, vm.name))

		return filters

	@staticmethod
	def render_filters(filters: List[Filter]) -> str:
		"""Turn filters into the query string"""
		rendered_filters = list(filter(None, [f.to_kusto() for f in filters]))

		predicate_str = " or ".join(rendered_filters)
		query = f"Resources | where type=~\"Microsoft.Compute/virtualMachines\" | where {predicate_str}"

		return query

	@staticmethod
	def graph_response_to_VMs(raw: Res) -> List[AzureVM]:
		"""Deserialise the graph request"""
		return [AzureVM(**e) for e in raw.data]


class AzureVM(BaseModel, extra=Extra.allow):
	id: str
	name: str
	resourceGroup: str
	subscriptionId: str

	location: str
	properties: Dict
	tags: Dict[str, str] = {}
	zones: Optional[List[str]] = None

	class Properties(BaseModel, extra=Extra.allow):
		hardwareProfile: dict
		networkProfile: AzureVM.NetworkProfile
		osProfile: Dict
		extended: dict = {}

	class NetworkProfile(BaseModel, extra=Extra.allow):
		networkInterfaces: List[AzureVM.NetworkInterface]

	class NetworkInterface(BaseModel, extra=Extra.allow):
		id: str
		properties: Dict = {}