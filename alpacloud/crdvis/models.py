from typing import Dict, List, Optional

from pydantic import BaseModel


class SchemaProperty(BaseModel):
	type: str
	properties: Optional[Dict[str, "SchemaProperty"]] = None


class OpenAPIV3Schema(BaseModel):
	type: str
	properties: Dict[str, SchemaProperty]


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
	schema: Dict[str, OpenAPIV3Schema]
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
