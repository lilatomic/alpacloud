import yaml

from alpacloud.crdvis.models import CustomResourceDefinition


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
		schema = version.schema["openAPIV3Schema"]
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
