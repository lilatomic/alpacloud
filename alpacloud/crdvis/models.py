from __future__ import annotations

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class OpenAPIV3Schema(BaseModel):
	type: str
	description: Optional[str] = None
	properties: Optional[Dict[str, OpenAPIV3]] = None
	format: Optional[str] = None
	pattern: Optional[str] = None


class OpenAPIV3Union(BaseModel):
	anyOf: List[OpenAPIV3]
	description: Optional[str] = None


class OpenAPIV3Array(BaseModel):
	type: str = "array"
	items: OpenAPIV3
	description: Optional[str] = None


class OpenAPIV3Enum(BaseModel):
	type: str = "string"
	enum: List[str]
	description: Optional[str] = None


class OpenAPIV3Dict(BaseModel):
	type: str = "object"
	additionalProperties: OpenAPIV3
	description: Optional[str] = None


OpenAPIV3 = Union[OpenAPIV3Array, OpenAPIV3Enum, OpenAPIV3Union, OpenAPIV3Dict, OpenAPIV3Schema]


def is_simple(openapi_node: OpenAPIV3) -> bool:
	"""Whether the given OpenAPI node is a simple (primitive) type whose representation we should inline"""
	match openapi_node:
		case OpenAPIV3Schema():
			return openapi_node.type in ("string", "integer", "number", "boolean")
		case OpenAPIV3Union():
			return all(is_simple(e) for e in openapi_node.anyOf)
		case OpenAPIV3Enum():
			return False
		case OpenAPIV3Array():
			return is_simple(openapi_node.items)
		case OpenAPIV3Dict():
			return is_simple(openapi_node.additionalProperties)
		case _:
			raise TypeError(f"Unexpected type: {type(openapi_node)}")


class Schema(BaseModel):
	openAPIV3Schema: OpenAPIV3Schema


class SelectableField(BaseModel):
	jsonPath: str


class AdditionalPrinterColumn(BaseModel):
	jsonPath: str
	name: str
	type: str


class CRDVersion(BaseModel):
	name: str
	served: bool
	storage: bool
	openAPIV3Schema: Optional[Schema] = Field(alias="schema", default=None)
	selectableFields: Optional[List[SelectableField]] = None
	additionalPrinterColumns: Optional[List[AdditionalPrinterColumn]] = None


class CRDNames(BaseModel):
	plural: str
	singular: str
	kind: str


class CRDSpec(BaseModel):
	group: str
	scope: str
	names: CRDNames
	versions: List[CRDVersion]


class CRDMetadata(BaseModel):
	name: str


class CustomResourceDefinition(BaseModel):
	apiVersion: str
	kind: str
	metadata: CRDMetadata
	spec: CRDSpec
