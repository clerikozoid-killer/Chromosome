"""L1.5 AFFINE TYPES — semantic type checking on top of L1 dimensions."""

from dbse.semantic.errors import SemanticTypeError
from dbse.semantic.operators import Operator
from dbse.semantic.tags import affine, ambiguous_tag, is_ambiguous

__all__ = [
    "Operator",
    "SemanticTypeError",
    "affine",
    "ambiguous_tag",
    "is_ambiguous",
]
