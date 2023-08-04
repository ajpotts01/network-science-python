import networkx as nx
import numpy as np
import pandas as pd

from IPython.display import SVG
from sknetwork.visualization import svg_graph
from sknetwork.data import Bunch
from sknetwork.ranking import PageRank

def create_network_data(entities: list[list[str]]) -> pd.DataFrame:
    """
    It is assumed in this case that the first entity in a list of entities is the source, and all subsequent entities are targets.
    """

    # Sources needs to be the same length as targets - so duplicate items across the list comprehension
    # https://stackoverflow.com/a/38054158
    sources: list[str] = [row[0] for row in entities for _ in range(len(row) - 1)]

    # https://stackoverflow.com/questions/25674169/how-does-the-list-comprehension-to-flatten-a-python-list-work
    # To figure this out on your own:
    # Write a nested loop way of doing this
    # e.g.
    # targets = []
    # for ent in entities:
    #     for sub_ent in ent[1:]:
    #         targets.append(sub_ent)
    # Then write the corresponding list comprehension from left to right.
    # It starts with the thing you'd append to the list, then you write the two for loops in sequence.
    targets: list[str] = [sub_ent for ent in entities for sub_ent in ent[1:]]

    # Create the relationship from source -> target with Pandas
    df_network_data: pd.DataFrame = pd.DataFrame(
        data=dict(source=sources, target=targets)
    )

    return df_network_data

def draw_graph(G, show_names: bool=False, node_size: int=1, font_size: int=10, edge_width: float=0.5) -> SVG:
    adjacency = nx.to_scipy_sparse_matrix(G, nodelist=None, dtype=None, weight='weight', format="csr")
    names: np.array = np.array(list(G.nodes()))
    graph: Bunch = Bunch()
    graph.adjacency = adjacency
    graph.names = np.array(names)
    page_rank: PageRank = PageRank()
    scores: np.ndarray = page_rank.fit_transform(adjacency)
    if show_names:
        image: str = svg_graph(graph.adjacency, font_size=font_size, node_size=node_size, names=graph.names, width=700, height=500, scores=scores, edge_width=edge_width)
    else:
        image: str = svg_graph(graph.adjacency, font_size=font_size, node_size=node_size, width=700, height=500, scores=scores, edge_width=edge_width)

    return SVG(image)