"""Data models for Logseq entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Block:
    """Represents a Logseq block."""
    
    id: str
    content: str
    page: str
    parent_id: str | None = None
    properties: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    children: list["Block"] | None = None


@dataclass
class Page:
    """Represents a Logseq page."""
    
    name: str
    properties: dict[str, Any] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    blocks: list[Block] | None = None


@dataclass
class QueryResult:
    """Represents a query result."""
    
    query: str
    results: list[dict[str, Any]]
    execution_time: float | None = None