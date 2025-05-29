from pydantic_core.core_schema import CoreSchema
from typing import Union, Any, TypedDict, Literal, Required, TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic_core.core_schema import ValidationInfo
else:
    from pydantic_core.core_schema import ValidationInfo


class SerSchema(TypedDict, total=False):
    type: Required[Literal['ser-serializer-function']]
    function: Any
    schema: CoreSchema


if TYPE_CHECKING:
    class InvalidSchema(TypedDict, total=False):
        type: Required[Literal['invalid']]
        ref: str
        metadata: dict[str, Any]
        serialization: SerSchema

JsonSchemaValue = dict[str, Any]
