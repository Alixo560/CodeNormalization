# 数据结构课程代码规范指导插件 PRD v4

**版本**：v4  
**日期**：2026-05-23  
**目标平台**：VS Code 插件 + FastAPI 后端  
**目标语言**：C / C++，优先支持 C++  
**本版本重点**：从“规范建议训练”升级为“规范建议 + 保守规范化修改 + 可视化辅助 IR”，并为外部评分工作提供规范化评分参考标准

---

## 1. 背景

当前插件已经具备代码规范性训练的基础能力：学生选择一段代码后，系统返回规范建议与解释，帮助学生理解命名、格式、注释、可读性等问题。

下一阶段需要支持学生完成代码后，对代码进行保守规范化修改，并将规范化结果传回后端，帮助后续代码可视化同学识别数据结构语义、操作行为和可视化标签。

同时，由于规范化将成为提交后处理流程的一部分，评分工作可以新增“代码规范化评分”维度，暂定满分 10 分。该评分标准提供给评分工作的同学参考，插件本身不负责评分。

---

## 2. 产品目标

1. 在不改变算法逻辑的前提下，对学生代码进行保守规范化。
2. 自动识别代码主要涉及的数据结构类型，例如链表、栈、队列、树、图、排序、查找等。
3. 基于“通用规范规则 + 数据结构专属规则 + LLM 语义补充”生成规范建议和规范化修改。
4. 输出结构化 IR，服务代码可视化、教学解释和后端归档。
5. 为评分工作的同学提供代码规范化评分参考标准，满分 10 分；插件本身不计算、不展示、不提交该分数。
6. 控制 LLM 调用成本与响应时间，避免所有逻辑都依赖 LLM。

---

## 3. 非目标

本阶段不负责：

- 判断算法答案是否正确。
- 自动修复算法 bug。
- 改变时间复杂度或空间复杂度。
- 将学生代码替换为另一种算法。
- 引入课程阶段之外的新数据结构或高级 C++ 技巧。
- 强制覆盖学生源代码。
- 替代可视化系统本身。

---

## 4. 核心原则

### 4.1 规则优先，LLM 补语义

确定性问题优先交给规则、AST、格式化工具处理。LLM 只负责规则难以判断的语义命名、教学解释、数据结构意图补充和低置信度分类。

### 4.2 保守规范化

允许修改：

- 缩进、空格、换行、大括号风格。
- `NULL` 到 `nullptr` 等低风险现代化表达。
- `using namespace std;` 的规范提示或保守替换。
- 局部变量、成员变量、函数、类的命名规范化。
- 必要注释和可视化标签。
- 魔法数字的提示或命名建议。

默认禁止修改：

- 控制流结构。
- 条件表达式语义。
- 循环边界。
- 函数调用关系。
- 数据结构行为。
- 输入输出协议。
- 算法步骤。
- 复杂度。

### 4.3 输出结构化，而不是只输出自然语言

后端需要统一返回规范化代码、diff、建议列表、数据结构标签、可视化 IR 和元信息，便于前端展示、后端保存和可视化系统消费。

### 4.4 快路径优先

常见代码应尽量走本地规则和工具链，不进入 LLM。只有当命名语义、数据结构分类或教学解释需要模型判断时才调用 LLM。

---

## 5. 用户场景

### 5.1 训练场景：学生写代码时请求建议

学生选择代码，点击“代码规范建议”。系统返回：

- 发现的问题。
- 建议原因。
- 可选替换片段。
- 数据结构识别结果。
- 可用于评分工作的规范性证据，例如建议类型、严重程度、结构识别结果。

该场景重视响应速度，不默认修改代码。

### 5.2 提交场景：学生完成代码后请求规范化

学生完成代码后点击“生成规范化版本”或由后端提交流程触发。系统返回：

- normalized_code。
- diff / patch。
- 修改原因。
- 数据结构标签。
- 可视化 IR。
- 可用于评分工作的规范化证据。
- 不安全修改警告。

该场景可以比训练场景稍慢，但必须保证修改安全。

### 5.3 可视化协作场景

规范化服务将代码中的变量角色、数据结构类型、操作行为提取为 IR，供可视化系统使用。例如：

```json
{
  "structure": "linked_list",
  "operation": "traversal",
  "roles": [
    {
      "name": "current",
      "role": "current_node"
    }
  ],
  "visual_tags": ["LIST_TRAVERSAL"]
}
```

---

## 6. 工作流设计

### 6.1 总体流程

```text
VS Code 插件
  ->
获取选中代码或当前文件
  ->
FastAPI 后端
  ->
代码预处理
  ->
基础规范化
  ->
数据结构识别
  ->
规则与 Skill 匹配
  ->
LLM 语义补充
  ->
规范化修改生成
  ->
diff 与 AST 安全校验
  ->
返回前端与后端归档
```

### 6.2 阶段一：代码预处理

输入：

- 原始代码。
- 文件名。
- 语言。
- 选区范围。
- 课程阶段。
- 作业 ID / 学生 ID，可选。

处理：

- 判断是否为完整文件或代码片段。
- 记录原始代码 hash。
- 清理不可见字符。
- 提取 include、class、struct、function、loop、pointer 等基础特征。

输出：

- preprocessed_code。
- code_fingerprint。
- static_features。

### 6.3 阶段二：基础规范化

优先使用确定性工具：

- `clang-format`：缩进、空格、换行、大括号。
- 静态规则：`using namespace std;`、成员变量后缀 `_`、常量命名、include 顺序。
- AST / tree-sitter：变量声明、函数声明、类成员识别。

输出：

- formatted_code。
- deterministic_suggestions。
- deterministic_evidence。

### 6.4 阶段三：数据结构识别

先使用规则识别，后使用 LLM 兜底。

规则示例：

| 数据结构 | 特征 |
| --- | --- |
| 链表 | `Node`、`next`、`head`、指针移动、`current = current->next` |
| 栈 | `push`、`pop`、`top`、`stack`、`top == -1` |
| 队列 | `front`、`rear`、`enqueue`、`dequeue`、循环队列取模 |
| 树 | `root`、`left`、`right`、递归遍历 |
| 图 | `adj_list`、`adj_matrix`、`visited`、DFS、BFS |
| 字符串 | `text`、`pattern`、KMP、`next` 数组 |
| 排序 | `swap`、`pivot`、partition、递归排序 |
| 查找 | `target`、`mid`、`left`、`right`、二分查找 |

输出：

```json
{
  "primary_structure": "linked_list",
  "secondary_structures": [],
  "confidence": 0.88,
  "evidence": ["Node*", "head", "current->next"]
}
```

### 6.5 阶段四：规则与 Skill 匹配

根据数据结构分类只加载相关规则，不加载完整规则库。

例如识别为链表时，只注入：

- 通用命名规则。
- 链表指针命名规则。
- 链表操作命名规则。
- 链表可视化标签规则。

这样可以减少 token、提高响应速度、降低模型发散。

### 6.6 阶段五：LLM 语义补充

LLM 负责：

- 变量语义角色判断。
- 低置信度数据结构确认。
- 命名建议生成。
- 教学解释生成。
- 可视化 IR 补全。

LLM 不负责：

- 直接整段重写代码。
- 最终决定 patch 是否安全。
- 修改算法逻辑。
- 给出不受规则约束的自由建议。

### 6.7 阶段六：规范化修改生成

修改生成分为两类：

1. 确定性修改：由工具或规则直接生成。
2. 语义修改：由 LLM 输出结构化建议，后端转换为 patch。

所有修改必须生成 diff，并进行安全校验。

### 6.8 阶段七：安全校验

校验项：

- diff 是否只影响允许区域。
- 是否改变函数签名。
- 是否改变循环条件。
- 是否改变分支条件。
- 是否新增复杂数据结构。
- 是否删除核心语句。
- 是否改变输入输出。
- 是否导致编译错误风险升高。

安全等级：

| 等级 | 含义 | 是否允许自动应用 |
| --- | --- | --- |
| safe | 格式、命名、注释等低风险修改 | 允许 |
| review_required | 可能影响接口或较大范围命名 | 需要学生确认 |
| unsafe | 可能改变逻辑 | 禁止自动应用 |

---

## 7. 外部规范化评分参考标准

本节提供给评分工作的同学参考，不属于插件功能。插件可以提供规范建议、结构识别、diff、visual IR 和 evidence，但不直接给代码打分，也不在前端展示分数。

### 7.1 总分

规范化评分满分 10 分，可作为代码总评分中的独立维度，也可以按课程需要折算为总成绩的 5% 到 15%。

### 7.2 评分维度

| 维度 | 分值 | 说明 |
| --- | ---: | --- |
| 格式与布局 | 2 分 | 缩进、空格、换行、大括号、单行长度是否清晰统一 |
| 命名规范 | 2 分 | 类、函数、变量、成员变量、常量是否符合课程命名规范 |
| 数据结构语义表达 | 2 分 | 是否使用能表达数据结构角色的命名，如 `head`、`current`、`root`、`left`、`right` |
| 封装与结构组织 | 1 分 | 类成员访问控制、函数职责、文件组织是否合理 |
| 注释与教学可读性 | 1 分 | 是否在关键逻辑处解释“为什么”，而不是堆砌无效注释 |
| 安全规范 | 1 分 | 是否避免 `using namespace std;`、魔法数字、宏滥用、全局变量滥用等问题 |
| 可视化友好度 | 1 分 | 是否便于提取节点关系、操作行为、角色标签和可视化 IR |

### 7.3 扣分参考

| 问题 | 建议扣分 |
| --- | ---: |
| 严重缩进混乱，影响阅读 | 0.5 - 1.5 |
| 大量无语义变量名，如 `a`、`b`、`p`、`q`，且非算法惯例 | 0.5 - 2 |
| 成员变量无 `_` 后缀，且与局部变量混淆 | 0.5 - 1 |
| 数据结构角色命名不清，如链表遍历全用 `p/q/t` | 0.5 - 1.5 |
| 使用 `using namespace std;` | 0.5 |
| 魔法数字未命名 | 0.5 - 1 |
| 函数过长或职责混杂 | 0.5 - 1 |
| 缺少关键复杂逻辑说明 | 0.5 - 1 |
| 可视化角色难以提取 | 0.5 - 1 |
| 规范化修改可能改变逻辑 | 不自动扣规范分，但标记为 unsafe |

### 7.4 评分证据来源

评分同学可以参考插件输出的以下信息：

- suggestions：规范建议类型、位置、原因和安全等级。
- structure_detection：数据结构识别结果、置信度和证据。
- visual_ir：可视化角色、操作行为和标签。
- diff：规范化前后的表达变化。
- blocked_changes：因可能改变逻辑而被阻止的修改。

### 7.5 评分边界

规范化评分只评价代码表达质量，不评价算法正确性。若代码存在算法错误，规范化评分仍可较高；若算法正确但命名和结构混乱，规范化评分应较低。该评分由评分系统或评分同学完成，不由插件自动生成。

---

## 8. API 设计

### 8.1 训练建议接口

```text
POST /api/v1/style-check
```

请求：

```json
{
  "code": "Node* p = head;",
  "lang": "cpp",
  "mode": "basic",
  "context": {
    "file_name": "list.cpp",
    "course_stage": "linked_list",
    "selected_range": {
      "start_line": 1,
      "end_line": 20
    }
  }
}
```

响应：

```json
{
  "status": "has_suggestions",
  "message": "发现 1 条规范建议",
  "formatted_code": "Node* p = head;",
  "structure_detection": {
    "primary_structure": "linked_list",
    "confidence": 0.86,
    "evidence": ["Node*", "head"]
  },
  "suggestions": [
    {
      "id": "naming_001",
      "type": "naming",
      "severity": "info",
      "line_start": 1,
      "line_end": 1,
      "original": "Node* p = head;",
      "replacement": "Node* current = head;",
      "reason": "在链表遍历中，current 能更清楚表达当前节点角色。",
      "course_concept": "链表遍历",
      "apply_safe": true,
      "confidence": 0.88
    }
  ],
  "metadata": {
    "ruleset_version": "2026-spring-v1",
    "llm_used": true,
    "workflow_engine": "rules+llm"
  }
}
```

### 8.2 规范化接口

```text
POST /api/v1/normalize-code
```

请求：

```json
{
  "code": "Node* p = head;",
  "lang": "cpp",
  "apply_level": "safe_only",
  "context": {
    "file_name": "list.cpp",
    "course_stage": "linked_list",
    "assignment_id": "ds-list-001",
    "student_id": "anonymous-or-hash"
  }
}
```

响应：

```json
{
  "status": "normalized",
  "normalized_code": "Node* current = head;",
  "diff": "--- original\n+++ normalized\n@@\n-Node* p = head;\n+Node* current = head;",
  "structure_detection": {
    "primary_structure": "linked_list",
    "confidence": 0.86,
    "evidence": ["Node*", "head"]
  },
  "visual_ir": {
    "structure": "linked_list",
    "operation": "traversal",
    "roles": [
      {
        "name": "current",
        "role": "current_node"
      }
    ],
    "visual_tags": ["LIST_TRAVERSAL"]
  },
  "applied_changes": [
    {
      "id": "rename_001",
      "type": "naming",
      "safety": "safe",
      "reason": "p 被识别为链表当前节点，规范化为 current。"
    }
  ],
  "blocked_changes": [],
  "metadata": {
    "ruleset_version": "2026-spring-v1",
    "llm_used": true,
    "latency_ms": 1280
  }
}
```

### 8.3 后端归档字段

后端建议保存：

- original_code_hash。
- normalized_code_hash。
- diff。
- structure_detection。
- visual_ir。
- applied_changes。
- blocked_changes。
- ruleset_version。
- model_version。
- latency_ms。
- created_at。

---

## 9. 前端交互改造

### 9.1 新增命令

| 命令 | 说明 |
| --- | --- |
| 代码规范建议 | 保持现有训练能力，只返回建议 |
| 生成规范化版本 | 返回规范化代码和 diff |
| 发送规范化结果到后端 | 提交 normalized_code、diff、visual_ir 和修改证据 |

### 9.2 面板展示

建议面板包含：

- 数据结构识别结果。
- 建议列表。
- 可应用修改。
- 被阻止修改及原因。
- 可视化标签预览。

### 9.3 应用修改策略

默认只允许学生主动应用修改。提交后自动规范化流程也应保存 diff，便于追踪。

---

## 10. 后端改造任务

### 10.1 Schema

需要新增或扩展：

- `StructureDetection`
- `VisualIR`
- `AppliedChange`
- `BlockedChange`
- `NormalizeCodeRequest`
- `NormalizeCodeResponse`

现有 `StyleCheckResponse` 需要增加：

- `structure_detection`

### 10.2 Service

建议拆分服务：

```text
services/
  preprocessing_service.py
  deterministic_style_check_service.py
  structure_detection_service.py
  skill_matching_service.py
  llm_style_check_service.py
  normalization_service.py
  safety_validation_service.py
  visual_ir_service.py
```

### 10.3 Rules / Skills

规则库建议拆分：

```text
rules/
  common_style_rules.yaml
  scoring_rules.yaml
  structures/
    linked_list.yaml
    stack.yaml
    queue.yaml
    tree.yaml
    graph.yaml
    string.yaml
    array.yaml
    search.yaml
    sort.yaml
```

### 10.4 Prompt

LLM prompt 应分为：

- 数据结构确认 prompt。
- 语义命名 prompt。
- 教学解释 prompt。
- visual IR 生成 prompt。

不要让一个 prompt 同时完成所有任务。

---

## 11. 性能设计

### 11.1 快路径

当规则置信度足够高且只存在格式问题时：

- 不调用 LLM。
- 直接返回格式化结果、确定性建议和结构化证据。

### 11.2 LLM 调用条件

满足任一条件才调用 LLM：

- 数据结构识别置信度低于阈值，例如 0.75。
- 存在模糊命名，需要语义判断。
- 需要生成教学解释。
- 需要生成 visual IR。
- 用户选择 advanced 模式。

### 11.3 缓存

缓存 key：

```text
code_hash + ruleset_version + course_stage + mode
```

可缓存：

- 数据结构识别结果。
- LLM 建议。
- visual IR。

### 11.4 目标延迟

| 场景 | 目标延迟 |
| --- | ---: |
| 仅格式化 / 规则检查 | < 500ms |
| 训练建议，含一次 LLM | 1s - 3s |
| 提交后完整规范化 | 2s - 6s |
| LLM 失败降级 | < 1s 返回规则结果 |

---

## 12. 里程碑

### Phase 1：结构识别与规范证据

- 扩展 response schema。
- 增加数据结构规则识别。
- 增加可供评分工作参考的规范证据输出。
- 前端展示结构标签和规范建议。

### Phase 2：保守规范化

- 增加 `/normalize-code` 接口。
- 生成 normalized_code 和 diff。
- 增加安全校验。
- 支持前端预览和应用修改。

### Phase 3：可视化 IR

- 输出 visual_ir。
- 支持链表、栈、队列、树的基础标签。
- 将规范化结果传回后端供可视化系统消费。

### Phase 4：效率优化

- 增加缓存。
- 拆分 prompt。
- 增加规则优先快路径。
- 收集延迟、LLM 调用率和失败率。

---

## 13. 成功指标

1. 80% 以上请求能通过规则快路径或一次 LLM 调用完成。
2. 训练建议场景 P95 延迟低于 3 秒。
3. 提交后规范化场景 P95 延迟低于 6 秒。
4. 自动应用的 safe 修改不改变算法行为。
5. 插件输出的规范证据能够支持评分同学进行 10 分制规范化评分。
6. 可视化系统可以从 visual_ir 中稳定识别主数据结构和关键操作。
7. 学生能够理解每条规范建议的原因，而不是只看到“扣分”。

---

## 14. 风险与应对

| 风险 | 说明 | 应对 |
| --- | --- | --- |
| LLM 生成慢 | 完整上下文过大导致延迟高 | 规则预筛、按结构加载 skill、缓存 |
| LLM 误改逻辑 | 模型可能提出越界修改 | diff + AST 安全校验，unsafe 禁止应用 |
| 评分争议 | 学生或教师对扣分不认可 | 插件不直接评分，仅输出可解释的规范证据供评分工作参考 |
| 结构识别错误 | 代码可能混合多个数据结构 | 输出置信度和证据，低置信度不强行应用结构规则 |
| 规则过重 | Google C++ 规范对课程代码可能过严 | 课程规则优先，工业规则作为参考 |
| 可视化 IR 不稳定 | 命名混乱时角色难提取 | 保留 evidence、confidence 和原始符号映射 |

---

## 15. MVP 验收标准

MVP 至少完成：

1. `style-check` 返回结构识别和规范证据。
2. 能识别链表、栈、队列、树四类基础结构。
3. 能按规则给出格式、命名、注释、数据结构语义表达方面的建议证据。
4. 新增 `normalize-code` 设计或接口雏形。
5. 规范化输出包含 `normalized_code`、`diff`、`applied_changes`、`blocked_changes`。
6. 所有自动应用修改都标记 safety。
7. 前端能展示结构标签和规范建议。

---

## 16. 总结

v4 的核心升级是将插件从“规范建议工具”推进到“规范化工作流基础设施”。

推荐主链路：

```text
规则 / clang-format / AST
  ->
数据结构识别
  ->
按结构加载 skill
  ->
LLM 语义补充
  ->
安全 diff
  ->
visual IR
  ->
返回前端与后端
```

这样既能控制效率，又能保护学生原始算法意图，并为代码可视化同学提供稳定、结构化、可追踪的输入。
