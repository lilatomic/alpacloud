import pytest
import yaml

from alpacloud.crdvis.models import CustomResourceDefinition, OpenAPIV3Array, OpenAPIV3Dict, OpenAPIV3Enum, OpenAPIV3Schema, OpenAPIV3Union, is_simple


class TestCustomResourceDefinition:
	def test_deserialize_crd(self):
		"""Test that the CustomResourceDefinition model can deserialize a sample CRD."""
		# Sample CRD YAML as provided in the issue description
		crd_yaml = """
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: shirts.stable.example.com
spec:
  group: stable.example.com
  scope: Namespaced
  names:
    plural: shirts
    singular: shirt
    kind: Shirt
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              color:
                type: string
              size:
                type: string
    selectableFields:
    - jsonPath: .spec.color
    - jsonPath: .spec.size
    additionalPrinterColumns:
    - jsonPath: .spec.color
      name: Color
      type: string
    - jsonPath: .spec.size
      name: Size
      type: string
"""
		# Parse the YAML into a dictionary
		crd_dict = yaml.safe_load(crd_yaml)

		# Deserialize the dictionary into a CustomResourceDefinition model
		crd = CustomResourceDefinition.model_validate(crd_dict)

		# Verify that the deserialization works correctly by checking key fields
		assert crd.apiVersion == "apiextensions.k8s.io/v1"
		assert crd.kind == "CustomResourceDefinition"
		assert crd.metadata.name == "shirts.stable.example.com"
		assert crd.spec.group == "stable.example.com"
		assert crd.spec.scope == "Namespaced"
		assert crd.spec.names.plural == "shirts"
		assert crd.spec.names.singular == "shirt"
		assert crd.spec.names.kind == "Shirt"

		# Check the first version
		version = crd.spec.versions[0]
		assert version.name == "v1"
		assert version.served is True
		assert version.storage is True

		# Check the schema
		schema = version.openAPIV3Schema.openAPIV3Schema
		assert schema.type == "object"
		assert "spec" in schema.properties

		# Check the selectable fields
		assert len(version.selectableFields) == 2
		assert version.selectableFields[0].jsonPath == ".spec.color"
		assert version.selectableFields[1].jsonPath == ".spec.size"

		# Check the additional printer columns
		assert len(version.additionalPrinterColumns) == 2
		assert version.additionalPrinterColumns[0].jsonPath == ".spec.color"
		assert version.additionalPrinterColumns[0].name == "Color"
		assert version.additionalPrinterColumns[0].type == "string"
		assert version.additionalPrinterColumns[1].jsonPath == ".spec.size"
		assert version.additionalPrinterColumns[1].name == "Size"
		assert version.additionalPrinterColumns[1].type == "string"


class TestIsSimple:
	"""Test cases for the is_simple function."""

	def test_schema_simple_types(self):
		"""Test that OpenAPIV3Schema with simple types returns True."""
		for simple_type in ["string", "integer", "number", "boolean"]:
			schema = OpenAPIV3Schema(type=simple_type)
			assert is_simple(schema) is True

	def test_schema_non_simple_types(self):
		"""Test that OpenAPIV3Schema with non-simple types returns False."""
		for non_simple_type in ["object", "array"]:
			schema = OpenAPIV3Schema(type=non_simple_type)
			assert is_simple(schema) is False

	def test_union_all_simple(self):
		"""Test that OpenAPIV3Union with all simple elements returns True."""
		union = OpenAPIV3Union(anyOf=[OpenAPIV3Schema(type="string"), OpenAPIV3Schema(type="integer")])
		assert is_simple(union) is True

	def test_union_some_non_simple(self):
		"""Test that OpenAPIV3Union with some non-simple elements returns False."""
		union = OpenAPIV3Union(anyOf=[OpenAPIV3Schema(type="string"), OpenAPIV3Schema(type="object")])
		assert is_simple(union) is False

	def test_enum_always_false(self):
		"""Test that OpenAPIV3Enum always returns False."""
		enum = OpenAPIV3Enum(enum=["value1", "value2"])
		assert is_simple(enum) is False

	def test_array_simple_items(self):
		"""Test that OpenAPIV3Array with simple items returns True."""
		array = OpenAPIV3Array(items=OpenAPIV3Schema(type="string"))
		assert is_simple(array) is True

	def test_array_non_simple_items(self):
		"""Test that OpenAPIV3Array with non-simple items returns False."""
		array = OpenAPIV3Array(items=OpenAPIV3Schema(type="object"))
		assert is_simple(array) is False

	def test_dict_simple_properties(self):
		"""Test that OpenAPIV3Dict with simple additionalProperties returns True."""
		dict_obj = OpenAPIV3Dict(additionalProperties=OpenAPIV3Schema(type="string"))
		assert is_simple(dict_obj) is True

	def test_dict_non_simple_properties(self):
		"""Test that OpenAPIV3Dict with non-simple additionalProperties returns False."""
		dict_obj = OpenAPIV3Dict(additionalProperties=OpenAPIV3Schema(type="object"))
		assert is_simple(dict_obj) is False

	def test_invalid_type(self):
		"""Test that an invalid type raises TypeError."""
		with pytest.raises(TypeError):
			is_simple("not a valid OpenAPIV3 type")
