import argparse
import sys
import os
import json
from analyzer import RepositoryAnalyzer
from graph import GraphEngine
from risk_engine import RiskEngine

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

        risk_engine = RiskEngine()
        risk_report = risk_engine.evaluate_risk(blast_radius)

        check_mark = "[+]" if sys.platform == "win32" and not sys.stdout.encoding or sys.stdout.encoding.lower().startswith("cp") else "✓"
        print("\nRipple Impact Analysis\n")

        print("Changed:")
        if blast_radius.directly_changed_files:
            for f in blast_radius.directly_changed_files:
                print(f"  {f}")
        else:
            print("  (No direct git changes detected)")

        print("\nAffected:")
        affected_items = risk_report.affected_services + risk_report.affected_endpoints
        if affected_items:
            for item in affected_items:
                print(f"  {item}")
        else:
            print("  (None)")

        dash = "-" if sys.platform == "win32" and not sys.stdout.encoding or sys.stdout.encoding.lower().startswith("cp") else "—"
        print(f"\nRisk:\n  {risk_report.risk_level.value} {dash} {risk_report.total_score}/100")

        if risk_report.factors:
            print("\nFactors:")
            for f in risk_report.factors:
                print(f"  +{f.score:<2} {f.name} ({f.description})")

        if risk_report.recommendations:
            print("\nRecommendations:")
            for rec in risk_report.recommendations:
                print(f"  -> {rec}")

        if args.json:
            output_data = {
                "impact": blast_radius.model_dump(),
                "risk_report": risk_report.model_dump()
            }
            print("\nCombined Analysis Output (JSON):")
            print(json.dumps(output_data, indent=2))

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
