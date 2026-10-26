"""Service layer for Storm-Breaker (HANDOFF plan section P4).

Each module hosts business logic moved verbatim out of the blueprint
route bodies (P4.1-P4.6).  Blueprints remain thin HTTP adapters; the
frozen response contract (NR-2) is enforced by ``tests/char``.
"""
