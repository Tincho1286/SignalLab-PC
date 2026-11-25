"""Record the application import graph, including imports inside functions."""

import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'signallab_pc'
QT = ('PySide6', 'shiboken6', 'matplotlib.backends.backend_qt')


def references(node, package):
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    module = node.module or ''
    if node.level:
        prefix = package[:len(package)-node.level+1]
        module = '.'.join((*prefix, module)) if module else '.'.join(prefix)
    return [module, *(f'{module}.{alias.name}' for alias in node.names)]


def cyclic_components(graph):
    """Use forward finishing order and traversal of reversed edges."""
    def visit(node, neighbors, visited, found):
        if node in visited:
            return
        visited.add(node)
        for child in sorted(neighbors[node]):
            visit(child, neighbors, visited, found)
        found.append(node)

    seen, order = set(), []
    reverse = {name: set() for name in graph}
    for source, destinations in graph.items():
        visit(source, graph, seen, order)
        for destination in destinations:
            reverse[destination].add(source)
    seen.clear()
    components = []
    for module in reversed(order):
        members = []
        visit(module, reverse, seen, members)
        if len(members) > 1:
            components.append(sorted(members))
    return sorted(components, key=lambda members: (-len(members), members))


def inventory():
    files = {'main': ROOT/'main.py'}
    for path in sorted((ROOT/PACKAGE).rglob('*.py')):
        parts = path.relative_to(ROOT).with_suffix('').parts
        files['.'.join(parts[:-1] if parts[-1] == '__init__' else parts)] = path

    qt_modules, edges, lines = set(), set(), 0
    for module, path in files.items():
        content = path.read_text(encoding='utf-8-sig')
        lines += len(content.splitlines())
        tree = ast.parse(content, filename=str(path.relative_to(ROOT)))
        top = set(tree.body)
        package = module.split('.') if path.name == '__init__.py' else module.split('.')[:-1]
        for node in ast.walk(tree):
            names = references(node, package)
            if any(name.startswith(QT) for name in names):
                qt_modules.add(module)
            for name in files.keys() & set(names) - {module}:
                edges.add((module, name, 'top' if node in top else 'nested'))

    full = {name: set() for name in files}
    top = {name: set() for name in files}
    for source, target, scope in sorted(edges):
        full[source].add(target)
        if scope == 'top':
            top[source].add(target)
    incoming = Counter(target for targets in full.values() for target in sorted(targets))
    summary = {
        'application_files': len(files),
        'lines': lines,
        'qt_modules': sorted(qt_modules),
        'edges': sum(map(len, full.values())),
        'top_level_edges': sum(map(len, top.values())),
        'cycles': cyclic_components(full),
        'top_level_cycles': cyclic_components(top),
        'top_importers': sorted(((name, len(targets)) for name, targets in full.items()),
                                key=lambda row: (-row[1], row[0]))[:10],
        'most_imported': sorted(incoming.items(), key=lambda row: (-row[1], row[0]))[:10],
    }
    return summary, sorted(edges)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--dot', type=Path, help='Optional complete graph')
    args = parser.parse_args()
    summary, edges = inventory()
    summary['sha'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    if args.dot:
        lines = [f'  "{source}" -> "{target}" [label="{scope}"];' for source, target, scope in edges]
        args.dot.write_text('digraph signallab {\n'+'\n'.join(lines)+'\n}\n', encoding='utf-8')


if __name__ == '__main__':
    main()
