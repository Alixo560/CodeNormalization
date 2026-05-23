import re
from collections import Counter

from backend.app.schemas.style_check import StructureDetection, StyleCheckRequest


STRUCTURE_LABELS = {
    "linked_list": "链表",
    "stack": "栈",
    "queue": "队列",
    "tree": "树",
    "graph": "图",
    "string": "串",
    "array": "数组",
    "search": "查找",
    "sort": "排序",
}


DETECTION_RULES: dict[str, list[tuple[str, str]]] = {
    "linked_list": [
        (r"\bNode\s*\*", "Node*"),
        (r"->\s*next\b", "->next"),
        (r"\bhead\b", "head"),
        (r"\btail\b", "tail"),
        (r"\bnext_node\b", "next_node"),
    ],
    "stack": [
        (r"\bstack\b", "stack"),
        (r"\bPush\s*\(", "Push()"),
        (r"\bPop\s*\(", "Pop()"),
        (r"\bTop\s*\(", "Top()"),
        (r"\btop\b", "top"),
        (r"\.empty\s*\(", ".empty()"),
    ],
    "queue": [
        (r"\bqueue\b", "queue"),
        (r"\bfront\b", "front"),
        (r"\brear\b", "rear"),
        (r"\bEnqueue\s*\(", "Enqueue()"),
        (r"\bDequeue\s*\(", "Dequeue()"),
    ],
    "tree": [
        (r"\bTreeNode\b", "TreeNode"),
        (r"\broot\b", "root"),
        (r"->\s*left\b", "->left"),
        (r"->\s*right\b", "->right"),
        (r"\bPreorder", "Preorder"),
        (r"\bInorder", "Inorder"),
        (r"\bPostorder", "Postorder"),
    ],
    "graph": [
        (r"\badj_list\b", "adj_list"),
        (r"\badj_matrix\b", "adj_matrix"),
        (r"\bvisited\b", "visited"),
        (r"\bDepthFirstSearch\b|\bDFS\b", "DFS"),
        (r"\bBreadthFirstSearch\b|\bBFS\b", "BFS"),
    ],
    "string": [
        (r"\bstring\b", "string"),
        (r"\btext\b", "text"),
        (r"\bpattern\b", "pattern"),
        (r"\bKMP\b", "KMP"),
        (r"\bnext\s*\[", "next[]"),
    ],
    "array": [
        (r"\brows\b", "rows"),
        (r"\bcols\b", "cols"),
        (r"\barr\s*\[", "arr[]"),
        (r"\bdata\s*\[", "data[]"),
    ],
    "search": [
        (r"\btarget\b", "target"),
        (r"\bmid\b", "mid"),
        (r"\bleft\b", "left"),
        (r"\bright\b", "right"),
        (r"left\s*\+\s*\(right\s*-\s*left\)\s*/\s*2", "binary-search-mid"),
    ],
    "sort": [
        (r"\bBubbleSort\b", "BubbleSort"),
        (r"\bQuickSort\b", "QuickSort"),
        (r"\bMergeSort\b", "MergeSort"),
        (r"\bpivot\b", "pivot"),
        (r"\bswap\s*\(", "swap()"),
        (r"\bpartition\b", "partition"),
    ],
}


def detect_structure(request: StyleCheckRequest) -> StructureDetection:
    """Infer the main data-structure topic from lightweight lexical evidence."""
    code = request.code
    scores: Counter[str] = Counter()
    evidence_by_structure: dict[str, list[str]] = {}

    for structure, rules in DETECTION_RULES.items():
        for pattern, evidence in rules:
            if re.search(pattern, code, flags=re.IGNORECASE):
                scores[structure] += 1
                evidence_by_structure.setdefault(structure, []).append(evidence)

    course_stage = (request.context.course_stage or "").lower()
    for structure in DETECTION_RULES:
        if structure in course_stage:
            scores[structure] += 2
            evidence_by_structure.setdefault(structure, []).append(f"course_stage:{structure}")

    if not scores:
        return StructureDetection(primary_structure=None, confidence=0.0, evidence=[])

    ranked = scores.most_common()
    primary, primary_score = ranked[0]
    secondary = [structure for structure, score in ranked[1:] if score >= 2]
    total_score = sum(scores.values())
    confidence = min(0.95, max(0.35, primary_score / total_score + min(primary_score, 5) * 0.08))

    return StructureDetection(
        primary_structure=primary,
        secondary_structures=secondary,
        confidence=round(confidence, 2),
        evidence=evidence_by_structure.get(primary, [])[:6],
    )
