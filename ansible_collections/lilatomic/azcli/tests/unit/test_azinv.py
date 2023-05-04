from lilatomic.azcli.plugins.inventory import azinv
from lilatomic.azcli.plugins.inventory.azinv import Filter


class TestFilterParse:
	inv = azinv.InventoryModule()

	def test_subscription_wildcard(self):
		r = self.inv.parse_subscriptions_to_filters({"sub0": "*"})
		assert r == [Filter(sub="sub0")]

	def test_full(self):
		r = self.inv.parse_subscriptions_to_filters(
			{
				"sub0": "*",
				"sub1": None,
				"sub2": {
					"rg0": "*",
					"rg1": None,
					"rg2": [{"name": "vm0"}, {"name": "vm1"}],
				},
			}
		)
		assert r == [
			Filter(sub="sub0", rg=None, vm=None),
			Filter(sub="sub1", rg=None, vm=None),
			Filter(sub="sub2", rg="rg0", vm=None),
			Filter(sub="sub2", rg="rg1", vm=None),
			Filter(sub="sub2", rg="rg2", vm="vm0"),
			Filter(sub="sub2", rg="rg2", vm="vm1"),
		]
