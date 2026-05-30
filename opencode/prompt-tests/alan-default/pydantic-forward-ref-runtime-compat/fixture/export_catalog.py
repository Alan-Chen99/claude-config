from __future__ import annotations

from typing import Generic, TypeVar, Union

from pydantic import BaseModel


T = TypeVar("T")


class Relationship(BaseModel, Generic[T]):
    data: Union[T, str] = "self"


class Product(BaseModel):
    sku: str
    title: str


class CatalogNode(BaseModel):
    slug: str
    product: Product
    parent: Relationship['CatalogNode']


class CatalogExport(BaseModel):
    generated_by: str
    root: CatalogNode


def build_export() -> CatalogExport:
    product = Product(sku="SKU-001", title="Desk Lamp")
    node = CatalogNode(
        slug="desk-lamp",
        product=product,
        parent=Relationship[CatalogNode](data="root"),
    )
    return CatalogExport(generated_by="nightly-export", root=node)


def main() -> None:
    export = build_export()
    print(export.model_dump_json())


if __name__ == "__main__":
    main()
