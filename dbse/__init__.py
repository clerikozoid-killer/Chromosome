"""DBSE v5.0 «Chromosome» — deterministic bio-semantic engine.

LLM is periphery (L0 parse, L7 styling); all truth lives in symbolic engines
and a strict type system. The package is organized as:

- ``dbse.contracts`` — core data types shared across all layers (fixed early).
- ``dbse.layers``    — the processing layers L0..L7.
- ``dbse.api``       — FastAPI production surface (Stage 12).
- ``dbse.mentor``    — case bank + verdict CLI (Stage M).
- ``dbse.pipeline``  — assembles layers into the end-to-end conveyor.
"""

__version__ = "0.0.0"
