from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class OpenAPIV3Schema(BaseModel):
	type: str
	description: Optional[str] = None
	properties: Optional[Dict[str, OpenAPIV3Schema | OpenAPIV3Union]] = None


class OpenAPIV3Union(BaseModel):
	anyOf: List[OpenAPIV3Schema | OpenAPIV3Union]
	description: Optional[str] = None


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
