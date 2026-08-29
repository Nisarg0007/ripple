import argparse
import sys
import os
import json
from analyzer import RepositoryAnalyzer
from graph import GraphEngine

def handle_scan(args):
    path = args.path
    if not os.path.exists(path):
        print(f"Error: Path '{path}' does not exist.")
        sys.exit(1)

    try:
        analyzer = RepositoryAnalyzer(path)
        result = analyzer.analyze(base_ref=args.base)

        summary = result.summary
        check_mark = "[+]" if sys.platform == "win32" and not sys.stdout.encoding or sys.stdout.encoding.lower().startswith("cp") else "✓"
        print("\nRipple Repository Scan\n")
        print(f"{check_mark} Python files: {summary.get('python_files', 0)}")
        print(f"{check_mark} Functions: {summary.get('functions', 0)}")
        print(f"{check_mark} Classes: {summary.get('classes', 0)}")
        print(f"{check_mark} API endpoints: {summary.get('endpoints', 0)}")
        print(f"{check_mark} Imports: {summary.get('imports', 0)}")
        if result.git.is_git_repo:
            print(f"{check_mark} Git branch: {result.git.branch}")
            if summary.get('changed_files', 0) > 0:
                print(f"{check_mark} Changed files: {summary.get('changed_files', 0)}")

        subdirs = result.repository.subdirectories
        if subdirs:
            print("\nRepository:")
            for sd in subdirs[:10]:  # Print first top-level modules/subdirs
                print(f"  {sd}")

        if args.json:
            print("\nDetailed Result (JSON):")
            print(json.dumps(result.model_dump(), indent=2))

    except Exception as e:
        print(f"Error analyzing repository: {e}")
        sys.exit(1)

def handle_impact(args):
    path = args.path
    if not os.path.exists(path):
        print(f"Error: Path '{path}' does not exist.")
        sys.exit(1)

    try:
        analyzer = RepositoryAnalyzer(path)
        analysis = analyzer.analyze(base_ref=args.base)

        graph_engine = GraphEngine()
        blast_radius = graph_engine.analyze_repository_impact(analysis)

        check_mark = "[+]" if sys.platform == "win32" and not sys.stdout.encoding or sys.stdout.encoding.lower().startswith("cp") else "✓"
        print("\nRipple Impact Analysis (Blast Radius)\n")
        print(f"{check_mark} Directly changed files: {len(blast_radius.directly_changed_files)}")
        for f in blast_radius.directly_changed_files:
            print(f"    - {f}")

        print(f"\n{check_mark} Directly changed components: {len(blast_radius.directly_changed_nodes)}")
        for node in blast_radius.directly_changed_nodes:
            print(f"    - [{node.type.value}] {node.label}")

        print(f"\n{check_mark} Total impacted downstream components: {blast_radius.total_impacted_count}")
        print(f"{check_mark} Affected API endpoints: {len(blast_radius.impacted_endpoints)}")

        if blast_radius.impacted_endpoints:
            print("\nImpacted Endpoints:")
            for ep in blast_radius.impacted_endpoints:
                print(f"  * {ep.label} ({ep.file_path})")

        if blast_radius.impacted_nodes:
            print("\nDownstream Impact Chain:")
            for imp in blast_radius.impacted_nodes[:15]:
                indent = "  " * imp.distance
                print(f"{indent}-> [{imp.impact_type}] {imp.node.label} (dist: {imp.distance})")

        if args.json:
            print("\nBlast Radius (JSON):")
            print(json.dumps(blast_radius.model_dump(), indent=2))

    except Exception as e:
        print(f"Error computing impact: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Ripple CLI - Impact analysis for code changes")
    parser.add_argument("--version", action="version", version="Ripple CLI v0.1.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    scan_parser = subparsers.add_parser("scan", help="Scan a repository path and extract structured metrics")
    scan_parser.add_argument("path", nargs="?", default=".", help="Path to the repository (default: current directory)")
    scan_parser.add_argument("--base", help="Git base ref to compare against (e.g. main)")
    scan_parser.add_argument("--json", action="store_true", help="Output full analysis result as JSON")

    impact_parser = subparsers.add_parser("impact", help="Calculate change impact and blast radius for repository")
    impact_parser.add_argument("path", nargs="?", default=".", help="Path to the repository (default: current directory)")
    impact_parser.add_argument("--base", help="Git base ref to compare against (e.g. main)")
    impact_parser.add_argument("--json", action="store_true", help="Output blast radius result as JSON")

    args = parser.parse_args()

    if args.command == "scan":
        handle_scan(args)
    elif args.command == "impact":
        handle_impact(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
