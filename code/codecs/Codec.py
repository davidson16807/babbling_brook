
from typing import Generic, Protocol, TypeVar

Content = TypeVar("Content")
Code = TypeVar("Code")

class Codec(Protocol, Generic[Content, Code]):
    def encode(self, content: Content) -> Code: ...
    def decode(self, code: Code) -> Content: ...
