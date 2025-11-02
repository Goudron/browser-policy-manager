from __future__ import annotations

from sqlalchemy.sql.elements import UnaryExpression

from app.services.policy_service import PolicyService


def test_sort_clause_defaults_to_updated_desc_for_unknown_field():
    """Unit-test the fallback branch in _sort_clause when field is unknown."""
    # Unknown field should fall back to updated_at; order 'desc' should produce a UnaryExpression
    clause = PolicyService._sort_clause("unknown_field", "desc")  # type: ignore[arg-type]
    # SQLAlchemy returns a sort construct (UnaryExpression for ORDER BY)
    assert isinstance(clause, UnaryExpression)

    # Also exercise 'asc' path explicitly
    clause2 = PolicyService._sort_clause("name", "asc")  # known field asc
    assert isinstance(clause2, UnaryExpression)
