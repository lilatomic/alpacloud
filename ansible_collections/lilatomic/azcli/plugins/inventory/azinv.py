from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ansible.plugins.inventory import BaseInventoryPlugin
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

		# config = self._read_config_data(path)
		raw_subs = self.get_option("subscriptions")

		filters = self.parse_subscriptions_to_filters(raw_subs)
		query = self.render_filters(filters)

		credential = "???"
		graph = Graph.from_credential(credential)
		graph_result = graph.q(query)
		vms = self.graph_response_to_VMs(graph_result)

		nic_refs = self.get_nic_refs(vms)
		nics = self.get_nics(graph, nic_refs)

		hosts = self.choose_ips_for_vms(nics, vms)

		for host, ip in hosts:
			self.register_host(host, ip)

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
		query = f'Resources | where type=~"Microsoft.Compute/virtualMachines" | where {predicate_str}'

		return query

	@staticmethod
	def graph_response_to_VMs(raw: Res) -> List[AzureVM]:
		"""Deserialise the graph request"""
		return [AzureVM(**e) for e in raw.data]

	def register_host(self, vm: AzureVM, ip: str):
		"""Register a host in the Ansible inventory"""
		key = vm.id

		self.inventory.add_host(key)
		self.inventory.set_variable(key, "ansible_host", ip)

	@staticmethod
	def get_nic_refs(vms: List[AzureVM]) -> List[str]:
		"""Get the NIC references"""
		out = []
		for vm in vms:
			for nic in vm.properties.networkProfile.networkInterfaces:
				out.append(nic.id)
		return out

	@staticmethod
	def get_nics(graph: Graph, nic_refs: List[str]) -> Dict[str, AzureNIC]:
		"""Get all relevant Azure NIC"""
		predicate = " or ".join([f'(id=~"{nic}")' for nic in nic_refs])
		query = (
			f'Resources | where type=~"Microsoft.Network/networkInterfaces" | where {predicate}'
		)
		raw = graph.q(query)

		nics = [AzureNIC(**e) for e in raw.data]
		return {nic.id: nic for nic in nics}

	@staticmethod
	def choose_ip_for_vm(nics: Dict[str, AzureNIC], vm: AzureVM) -> str:
		"""Get the probable ip config for this VM (VMs can have multiple NICs"""
		target_nic_ref = next(
			e
			for e in vm.properties.networkProfile.networkInterfaces
			if e.properties.get("primary", False)
		)  # choose the primary NIC

		nic = nics[target_nic_ref.id]
		return next(
			e.properties.privateIPAddress
			for e in nic.properties.ipConfigurations
			if e.properties.primary
		)  # choose the primary IP config

	def choose_ips_for_vms(
		self, nics: Dict[str, AzureNIC], vms: List[AzureVM]
	) -> List[Tuple[AzureVM, str]]:
		"""Choose IPs for all VMs, ready for registration"""
		return [(e, self.choose_ip_for_vm(nics, e)) for e in vms]


class AzureVM(BaseModel, extra=Extra.allow):
	"""An Azure VM from the Azure Graph"""

	id: str
	name: str
	resourceGroup: str
	subscriptionId: str

	location: str
	properties: Properties
	tags: Dict[str, str] = {}
	zones: Optional[List[str]] = None

	class Properties(BaseModel, extra=Extra.allow):
		"""Properties"""

		hardwareProfile: dict
		networkProfile: AzureVM.NetworkProfile
		osProfile: Dict
		extended: dict = {}

	class NetworkProfile(BaseModel, extra=Extra.allow):
		"""Network Profile"""

		networkInterfaces: List[AzureVM.NetworkInterface]

	class NetworkInterface(BaseModel, extra=Extra.allow):
		"""Reference to the NIC"""

		id: str
		properties: Dict = {}


class AzureNIC(BaseModel, extra=Extra.allow):
	"""An Azure NIC from the Azure Graph"""

	id: str
	name: str
	resourceGroup: str
	subscriptionId: str

	location: str
	properties: Properties

	class Properties(BaseModel, extra=Extra.allow):
		"""Properties"""

		ipConfigurations: List[AzureNIC.IPConfiguration]
		macAddress: str

	class IPConfiguration(BaseModel, extra=Extra.allow):
		"""IPConfiguration for a NIC"""

		id: str
		name: str
		properties: Properties

		class Properties(BaseModel, extra=Extra.allow):
			privateIPAddress: str
			privateIPAddressVersion: str
			primary: bool = False
