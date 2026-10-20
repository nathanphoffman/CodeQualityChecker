def chain_from(name, graph, remembered, path):
    """The longest list of calls starting at name. A function already on the path is not followed, so loops end."""

    if name in remembered:
        return remembered[name]

    best = []

    for callee in sorted(graph[name] - path):
        chain = chain_from(callee, graph, remembered, path | {name})
        best = chain if len(chain) > len(best) else best

    remembered[name] = [name] + best

    return remembered[name]

def longest_chains(graph):
    """The longest chain from each entry point. When every function is called by another (a loop), all of them count as entry points."""
    called = set().union(*graph.values()) if graph else set()
    entry_points = [name for name in graph if name not in called] or list(graph)
    remembered = {}

    return [chain_from(name, graph, remembered, frozenset()) for name in sorted(entry_points)]
