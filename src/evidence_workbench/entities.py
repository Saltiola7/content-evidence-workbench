"""Deterministic entity co-occurrence graph."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations

from .domain import ChunkCorpus, EntityEdge, EntityGraph


def build_entity_graph(chunks: ChunkCorpus) -> EntityGraph:
    """Build an immutable graph from declared entities present in each chunk."""
    nodes: set[str] = set()
    edge_chunks: dict[tuple[str, str], set[str]] = defaultdict(set)
    chunk_entities: list[tuple[str, tuple[str, ...]]] = []
    for chunk in chunks.chunks:
        entities = tuple(sorted(set(chunk.entities)))
        nodes.update(entities)
        chunk_entities.append((chunk.chunk_id, entities))
        for source, target in combinations(entities, 2):
            edge_chunks[(source, target)].add(chunk.chunk_id)
    edges = tuple(
        EntityEdge(
            source=source,
            target=target,
            weight=len(chunk_ids),
            chunk_ids=tuple(sorted(chunk_ids)),
        )
        for (source, target), chunk_ids in sorted(edge_chunks.items())
    )
    return EntityGraph(
        nodes=tuple(sorted(nodes)),
        edges=edges,
        chunk_entities=tuple(chunk_entities),
    )
