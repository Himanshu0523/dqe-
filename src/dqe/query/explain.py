"""PS §3(c): Human-readable optimization diff + plan comparison."""
from dqe.contracts import OptimizedQuery


def render(original_sql: str, opt: OptimizedQuery, original_plan: str, final_plan: str) -> str:
    lines = []
    lines.append("Changes:")
    if not opt.changes:
        lines.append("  (none — query already optimal)")
    for c in opt.changes:
        lines.append(f"  • {c}")
    lines.append("")
    lines.append("Plan (original):")
    lines.append(original_plan or "  (n/a)")
    lines.append("")
    lines.append("Plan (optimized):")
    lines.append(final_plan or "  (n/a)")
    return "\n".join(lines)