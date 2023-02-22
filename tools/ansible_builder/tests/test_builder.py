"""Tests for alpacloud-ansible-builder"""
from ansible_builder.alpacloud_ansible_builder import collect_mappings


def test_find_multiple_collections():
	collections = [{"a": {}, "b": {}}, {"c": {}}]

	a = collect_mappings(collections)

	assert len(a) == 3
