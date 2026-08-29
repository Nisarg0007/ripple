import argparse
import sys
import os
import json
from analyzer import RepositoryAnalyzer
from graph import GraphEngine
from risk_engine import RiskEngine, RiskLevel
from runtime import RuntimeEngine

RISK_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4
}

def get_check_mark():
    return "[+]" if sys.platform == "win32" and not sys.stdout.encoding or sys.stdout.encoding.lower().startswith("cp") else "✓"

def get_dash():
    return "-" if sys.platform == "win32" and not sys.stdout.encoding or sys.stdout.encoding.lower().startswith("cp") else "—"

def handle_scan(args):
    path = args.path
    if not os.path.exists(path):
        print(f"Error: repository path '{path}' does not exist.")
        sys.exit(2)

    try:
        analyzer = RepositoryAnalyzer(path)
        result = analyzer.analyze(base_ref=args.base)

        summary = result.summary
        print("\nRipple Repository Scan\n")
        print(f"Files             {summary.get('python_files', 0):>5}")
        print(f"Functions         {summary.get('functions', 0):>5}")
        print(f"Classes           {summary.get('classes', 0):>5}")
        print(f"API endpoints     {summary.get('endpoints', 0):>5}")
        print(f"Imports           {summary.get('imports', 0):>5}")

        subdirs = result.repository.subdirectories
        if subdirs:
            print("\nServices:")
            for sd in subdirs[:10]:
                print(f"  {sd}")

        if args.json:
            print("\nDetailed Result (JSON):")
            print(json.dumps(result.model_dump(), indent=2))

    except Exception as e:
        print(f"Error analyzing repository: {e}")
        sys.exit(2)

from ai import AIService

def handle_impact(args):
    path = args.path
    if not os.path.exists(path):
        print(f"Error: repository path '{path}' does not exist.")
        sys.exit(2)

    try:
        analyzer = RepositoryAnalyzer(path)
        analysis = analyzer.analyze(base_ref=args.base)

        graph_engine = GraphEngine()
        blast_radius = graph_engine.analyze_repository_impact(analysis)

        risk_engine = RiskEngine()
        risk_report = risk_engine.evaluate_risk(blast_radius)

        dash = get_dash()
        print("\nRipple Impact Analysis\n")
        print(f"Risk: {risk_report.risk_level.value} {dash} {risk_report.total_score}/100\n")

        print("Directly changed:")
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

        if risk_report.factors:
            print("\nRisk Factors:")
            for f in risk_report.factors:
                print(f"  +{f.score:<2} {f.name}")

        if risk_report.recommendations:
            print("\nRecommendations:")
            for rec in risk_report.recommendations:
                print(f"  -> {rec}")

        explanation_data = None
        if getattr(args, "explain", False):
            ai_service = AIService()
            explanation_data = ai_service.generate_explanation(risk_report.model_dump())
            print("\n" + "="*50)
            print("Why This Matters (AI Explanation):")
            print(f"[{'Fallback Mode' if explanation_data.is_fallback else 'AI Powered - ' + explanation_data.provider_used}]")
            print("="*50)
            print(f"\n{explanation_data.summary}\n")
            print(explanation_data.why_risky)
            if explanation_data.recommended_actions:
                print("\nRecommended Actions:")
                for act in explanation_data.recommended_actions:
                    print(f"  * {act}")

        if args.json:
            output_data = {
                "impact": blast_radius.model_dump(),
                "risk_report": risk_report.model_dump()
            }
            if explanation_data:
                output_data["explanation"] = explanation_data.model_dump()
            print("\nCombined Analysis Output (JSON):")
            print(json.dumps(output_data, indent=2))

    except Exception as e:
        print(f"Error computing impact: {e}")
        sys.exit(2)

def handle_runtime(args):
    path = args.path
    try:
        runtime_engine = RuntimeEngine()
        runtime_graph = runtime_engine.get_runtime_graph()

        print("\nRipple Runtime Analysis\n")
        if runtime_graph.edges:
            for edge in runtime_graph.edges:
                print(f"{edge.source_service} -> {edge.destination_service}")
                print(f"  calls: {edge.request_count}")
                print(f"  avg latency: {edge.average_latency_ms}ms")
                print()
        else:
            print("No runtime telemetry captured yet.")

        if args.drift and os.path.exists(path):
            handle_drift(args)

        if args.json:
            print("\nRuntime Output (JSON):")
            print(json.dumps(runtime_graph.model_dump(), indent=2))

    except Exception as e:
        print(f"Error executing runtime analysis: {e}")
        sys.exit(2)

def handle_drift(args):
    path = args.path
    if not os.path.exists(path):
        print(f"Error: repository path '{path}' does not exist.")
        sys.exit(2)

    try:
        analyzer = RepositoryAnalyzer(path)
        analysis = analyzer.analyze()

        graph_engine = GraphEngine()
        static_export = graph_engine.get_graph_export(analysis)

        runtime_engine = RuntimeEngine()
        drift_report = runtime_engine.detect_architecture_drift(static_export)

        print("\nRipple Architecture Drift\n")

        if drift_report.runtime_only_dependencies:
            print("[!] Runtime-only dependency (Drift):\n")
            for item in drift_report.runtime_only_dependencies:
                print(f"  {item.source} -> {item.target}")
                print(f"  {item.description}\n")
        else:
            print("[+] No runtime architecture drift detected.\n")

        if drift_report.verified_dependencies:
            print("Verified dependencies (Static + Runtime):")
            for item in drift_report.verified_dependencies:
                print(f"  * {item.source} -> {item.target}")

        if args.json:
            print("\nDrift Report (JSON):")
            print(json.dumps(drift_report.model_dump(), indent=2))

    except Exception as e:
        print(f"Error computing drift: {e}")
        sys.exit(2)

def handle_check(args):
    path = args.path
    if not os.path.exists(path):
        print(f"Error: repository path '{path}' does not exist.")
        sys.exit(2)

    try:
        fail_threshold_str = args.fail_on.upper()
        try:
            threshold_level = RiskLevel(fail_threshold_str)
        except ValueError:
            print(f"Error: Invalid fail-on threshold '{args.fail_on}'. Valid options: low, medium, high, critical.")
            sys.exit(2)

        analyzer = RepositoryAnalyzer(path)
        analysis = analyzer.analyze(base_ref=args.base)

        graph_engine = GraphEngine()
        blast_radius = graph_engine.analyze_repository_impact(analysis)

        risk_engine = RiskEngine()
        risk_report = risk_engine.evaluate_risk(blast_radius)

        dash = get_dash()
        print("\nRipple CI Check\n")
        print(f"Change Risk: {risk_report.risk_level.value} {dash} {risk_report.total_score}/100")

        print("\nImpact:")
        print(f"  {len(blast_radius.directly_changed_nodes) + blast_radius.total_impacted_count} components")
        print(f"  {len(blast_radius.impacted_endpoints)} API endpoints")
        print(f"  {blast_radius.max_depth} dependency levels")

        if risk_report.factors:
            print("\nWarnings / Risk Factors:")
            for f in risk_report.factors:
                print(f"  - {f.name}: {f.description}")

        is_failure = RISK_ORDER[risk_report.risk_level] >= RISK_ORDER[threshold_level]
        result_text = "FAILED" if is_failure else "PASSED"

        print(f"\nPolicy Check (Threshold: {threshold_level.value}): {result_text}\n")

        # Save Markdown artifact if requested for GitHub PR comment
        if args.output_markdown:
            md_content = f"""## Ripple Change Impact Analysis

**Change Risk:** `{risk_report.risk_level.value}` ({risk_report.total_score}/100)
**Policy Threshold:** `{threshold_level.value}` — **Result:** `{result_text}`

### Impact Summary
- **Directly Changed Files:** {len(blast_radius.directly_changed_files)}
- **Downstream Impacted Components:** {blast_radius.total_impacted_count}
- **Affected API Endpoints:** {len(blast_radius.impacted_endpoints)}

### Risk Factors
{"".join(f"- **+{f.score} {f.name}**: {f.description}\n" for f in risk_report.factors) if risk_report.factors else "No elevated risk factors detected."}

### Recommendations
{"".join(f"- {rec}\n" for rec in risk_report.recommendations) if risk_report.recommendations else "Standard review process."}
"""
            try:
                with open(args.output_markdown, "w", encoding="utf-8") as f:
                    f.write(md_content)
                print(f"[+] Saved Markdown report artifact to {args.output_markdown}")
            except Exception as e:
                print(f"[!] Warning: Could not write markdown report: {e}")

        if args.json:
            out = {
                "risk_report": risk_report.model_dump(),
                "impact": blast_radius.model_dump(),
                "policy_result": result_text,
                "threshold": threshold_level.value
            }
            print("\nCI Check Output (JSON):")
            print(json.dumps(out, indent=2))

        sys.exit(1 if is_failure else 0)

    except SystemExit:
        raise
    except Exception as e:
        print(f"Error performing CI check: {e}")
        sys.exit(2)

def main():
    parser = argparse.ArgumentParser(description="Ripple CLI - Impact analysis for code changes")
    parser.add_argument("--version", action="version", version="Ripple CLI v0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    scan_parser = subparsers.add_parser("scan", help="Scan a repository path and extract structured metrics")
    scan_parser.add_argument("path", nargs="?", default=".", help="Path to repository")
    scan_parser.add_argument("--base", help="Git base ref")
    scan_parser.add_argument("--json", action="store_true", help="Output JSON")

    impact_parser = subparsers.add_parser("impact", help="Calculate change impact and blast radius")
    impact_parser.add_argument("path", nargs="?", default=".", help="Path to repository")
    impact_parser.add_argument("--base", help="Git base ref")
    impact_parser.add_argument("--explain", action="store_true", help="Generate natural language AI/Fallback explanation")
    impact_parser.add_argument("--json", action="store_true", help="Output JSON")

    runtime_parser = subparsers.add_parser("runtime", help="Analyze live OpenTelemetry runtime service dependencies")
    runtime_parser.add_argument("path", nargs="?", default=".", help="Path to repository")
    runtime_parser.add_argument("--drift", action="store_true", help="Include drift comparison")
    runtime_parser.add_argument("--json", action="store_true", help="Output JSON")

    drift_parser = subparsers.add_parser("drift", help="Compare static AST graph vs OpenTelemetry runtime telemetry")
    drift_parser.add_argument("path", nargs="?", default=".", help="Path to repository")
    drift_parser.add_argument("--json", action="store_true", help="Output JSON")

    check_parser = subparsers.add_parser("check", help="CI/CD policy check assessing change risk and exit codes")
    check_parser.add_argument("path", nargs="?", default=".", help="Path to repository")
    check_parser.add_argument("--base", help="Git base ref")
    check_parser.add_argument("--fail-on", default="high", choices=["low", "medium", "high", "critical"], help="Risk threshold level to trigger exit code 1 (default: high)")
    check_parser.add_argument("--output-markdown", help="Path to save Markdown PR comment report artifact")
    check_parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    if args.command == "scan":
        handle_scan(args)
    elif args.command == "impact":
        handle_impact(args)
    elif args.command == "runtime":
        handle_runtime(args)
    elif args.command == "drift":
        handle_drift(args)
    elif args.command == "check":
        handle_check(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
