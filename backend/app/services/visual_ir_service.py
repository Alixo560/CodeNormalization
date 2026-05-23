import re

from backend.app.schemas.style_check import StructureDetection, VisualIR, VisualRole


def build_visual_ir(code: str, structure_detection: StructureDetection) -> VisualIR:
    structure = structure_detection.primary_structure
    if not structure:
        return VisualIR()

    if structure == "linked_list":
        roles = _extract_linked_list_roles(code)
        tags = ["LIST_TRAVERSAL"] if "->next" in code else []
        operation = "traversal" if tags else None
        return VisualIR(structure=structure, operation=operation, roles=roles, visual_tags=tags)

    if structure == "stack":
        tags = []
        if re.search(r"\bPush\s*\(|\.push\s*\(", code):
            tags.append("STACK_PUSH")
        if re.search(r"\bPop\s*\(|\.pop\s*\(", code):
            tags.append("STACK_POP")
        return VisualIR(structure=structure, operation=None, roles=[], visual_tags=tags)

    if structure == "queue":
        tags = []
        if re.search(r"\bfront\b", code):
            tags.append("FRONT_MOVE")
        if re.search(r"\brear\b", code):
            tags.append("REAR_MOVE")
        return VisualIR(structure=structure, operation=None, roles=[], visual_tags=tags)

    if structure == "tree":
        tags = []
        if re.search(r"->\s*left\b", code):
            tags.append("TRAVERSE_LEFT")
        if re.search(r"->\s*right\b", code):
            tags.append("TRAVERSE_RIGHT")
        return VisualIR(structure=structure, operation="traversal" if tags else None, roles=[], visual_tags=tags)

    return VisualIR(structure=structure, operation=None, roles=[], visual_tags=[])


def _extract_linked_list_roles(code: str) -> list[VisualRole]:
    role_by_name = {
        "head": "head_node",
        "tail": "tail_node",
        "current": "current_node",
        "cur": "current_node",
        "prev": "previous_node",
        "next": "next_node",
    }
    roles: list[VisualRole] = []
    seen: set[str] = set()

    for name, role in role_by_name.items():
        if re.search(rf"\b{re.escape(name)}\b", code) and name not in seen:
            roles.append(VisualRole(name=name, role=role))
            seen.add(name)

    return roles
