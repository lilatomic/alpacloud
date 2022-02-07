"""Execute HTTP DELETE request in Ansible"""
from .http import ActionModule as Http


class ActionModule(Http):
	"""Execute HTTP DELETE request in Ansible"""

	def run(self, tmp=None, task_vars=None):
		self._task.args["method"] = "DELETE"

		return super().run(tmp=tmp, task_vars=task_vars)
