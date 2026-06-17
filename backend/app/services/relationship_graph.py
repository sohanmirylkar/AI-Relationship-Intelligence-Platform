from uuid import UUID

import networkx as nx

from backend.app.models.schemas import GraphResponse
from backend.app.services.storage import store


def graph_for_company(company_id: UUID | str | None = None) -> GraphResponse:
    state = store.read()
    graph = nx.MultiDiGraph()
    company_ids = {str(company_id)} if company_id else {c["id"] for c in state.get("companies", [])}

    for company in state.get("companies", []):
        if company["id"] in company_ids or not company_id:
            graph.add_node(company["id"], label=company["name"], type="Company", metadata=company)
    for person in state.get("people", []):
        if not company_id or person.get("company_id") in company_ids:
            graph.add_node(person["id"], label=person["full_name"], type="Person", metadata=person)
    for interaction in state.get("interactions", []):
        if not company_id or interaction.get("company_id") in company_ids:
            graph.add_node(
                interaction["id"],
                label=interaction.get("interaction_date") or "Interaction",
                type="Interaction",
                metadata=interaction,
            )
    for rel in state.get("relationships", []):
        if rel.get("source_id") in graph.nodes and rel.get("target_id") in graph.nodes:
            graph.add_edge(
                rel["source_id"],
                rel["target_id"],
                key=rel.get("relationship_type"),
                type=rel.get("relationship_type"),
                strength=rel.get("strength", 0.5),
            )

    nodes = [
        {"id": node_id, **data}
        for node_id, data in graph.nodes(data=True)
    ]
    edges = [
        {"source": source, "target": target, "key": key, **data}
        for source, target, key, data in graph.edges(keys=True, data=True)
    ]
    return GraphResponse(nodes=nodes, edges=edges)
