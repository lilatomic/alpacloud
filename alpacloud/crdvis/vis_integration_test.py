import pytest
from textual.widgets import Tree

from alpacloud.crdvis.vis import CRDVisApp, InfoBox, OpenDialog


class TestUI:
	@pytest.mark.asyncio
	async def test_ui_anything(self):
		app = CRDVisApp()
		async with app.run_test() as pilot:
			await pilot.press("greater_than")

			await pilot.press("ctrl+o")
			assert isinstance(pilot.app.screen, OpenDialog)
			await pilot.press(
				*"https://github.com/prometheus-operator/prometheus-operator/blob/main/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml", "enter"
			)
			info_box = pilot.app.screen.query_one(InfoBox)
			assert info_box.crd.spec.names.kind == "ServiceMonitor"

			await pilot.press("ctrl+g")
			assert pilot.app.screen.focused.id == "find-box"

			await pilot.press(*"pod", "enter", "enter")
			await pilot.press("tab")
			focused = pilot.app.screen.focused
			assert isinstance(focused, Tree)
			assert "pod" in focused.cursor_node.label
