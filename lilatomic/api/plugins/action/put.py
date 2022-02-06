"""Execute HTTP PUT request in Ansible"""
from .http import ActionModule as Http


class ActionModule(Http):
	"""Execute HTTP PUT request in Ansible"""
	def run(self, tmp=None, task_vars=None):
		self._task.args["method"] = "PUT"

		return super().run(tmp=tmp, task_vars=task_vars)
