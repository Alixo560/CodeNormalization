# 数据结构课程代码规范指导插件

**产品名称**：数据结构课程代码规范指导插件  
**目标平台**：VS Code 

**目标语言**：C++

---

## 一、背景

在数据结构课程教学中，现有评测平台通常关注程序是否能够编译、是否通过测试用例、算法结果是否正确，但对学生代码的可读性、命名习惯、注释意识和基础结构表达缺乏持续训练。

学生常见问题包括：

- 变量名随意，如 `a`、`b`、`p`、`q` 等缺少语义；
- 缩进、空格、换行风格不统一；
- 链表、树、排序等核心逻辑缺少必要注释；
- 使用魔数、复杂表达式或过长函数，影响阅读；
- 过度依赖能运行，而忽视代码表达是否清晰。

本插件旨在补足自动评测系统之外的“编码习惯训练”环节，以轻量、即时、教学友好的方式帮助学生逐步建立良好的代码规范意识。

---

## 二、目标

开发一个面向数据结构课程的 VS Code 插件，在学生编写代码后，对其代码进行聚焦于**可读性**的规范检查，并给出可理解、可选择、非强制的改进建议。

核心目标：

1. **提升代码可读性**：重点检查格式、命名、注释、基础结构表达。
2. **服务课程教学**：建议不仅指出问题，还解释原因，并适度关联数据结构知识点。
3. **不干扰算法学习**：不改变算法逻辑，不进行性能优化，不引入超纲设计。
4. **保证输出可控**：通过规则库、结构化输出、后端校验、patch 安全检查约束 LLM 行为。
5. **支持教师扩展**：允许后续通过规则库、Skill 库和课程配置文件扩展课程规范。

---

## 三、边界

### 3.1 本产品负责

- 代码格式规范提示；
- 命名清晰度建议；
- 注释充分性建议；
- 魔数、复杂表达式、过长函数等基础可读性提示；
- 教学性解释；
- 可选的进阶知识提示；
- 局部代码修改建议；
- 对 LLM 输出进行结构化约束和安全校验。

### 3.2 本产品不负责

- 判断算法是否正确；
- 修复语法错误；
- 替学生完成作业；
- 自动优化时间复杂度或空间复杂度；
- 自动替换为更高级算法或数据结构；
- 进行工业级代码审查；
- 强制修改学生代码。

---

## 四、目标用户

### 4.1 主要用户

- 数据结构课程学生；
- 大一、大二计算机相关专业学生；
- 编程基础已有一定积累，但工程规范意识仍在建立阶段的学习者。

### 4.2 次要用户

- 数据结构课程教师；
- 助教；
- 实验课维护人员。

教师和助教主要关注规则配置、建议质量、课程一致性和学生使用反馈。

---

## 五、核心设计原则

1. **规则优先，LLM 补充**  
   能用确定性工具解决的问题，不交给 LLM 判断。格式问题由 `clang-format` 处理，基础静态检查由 `clang-tidy` 或 AST 工具处理，LLM 主要负责语义解释和教学表达。

2. **局部建议，不整体重写**  
   LLM 不直接返回完整重写后的代码，而是返回局部 suggestion 或 patch，后端验证安全后再允许应用。

3. **只改表达，不改逻辑**  
   建议只能提升可读性，不能改变控制流、数据结构、函数调用关系、算法步骤或复杂度。

4. **教学友好，不制造挫败感**  
   建议采用温和表达，强调“可读性提升”，避免使用“错误”“糟糕”等强负面措辞。

5. **输出必须结构化**  
   LLM 输出必须符合 JSON Schema，并经过 Pydantic 或等价机制校验。

6. **教师规则高于模型判断**  
   课程规则库、允许缩写、禁用建议、课程阶段配置优先级高于 LLM 输出。

---

## 六、核心功能

### 6.1 代码规范检查

用户可以对选中代码或当前文件触发检查。

检查范围包括：

- 格式与风格；
- 命名清晰度；
- 注释充分性；
- 基础结构可读性；
- 课程相关可读性问题。

### 6.2 教学性建议生成

插件针对发现的问题生成建议，每条建议包含：

- 问题类型；
- 代码位置；
- 原始代码片段；
- 建议替换片段；
- 修改原因；
- 关联课程概念；
- 是否可一键应用；
- 置信度；
- 安全等级。

示例：

```json
{
  "type": "naming",
  "line_start": 8,
  "line_end": 8,
  "original": "Node* p = head;",
  "replacement": "Node* cur = head;",
  "reason": "在链表遍历中，cur 能表达当前访问节点的含义，比 p 更便于理解遍历过程。",
  "course_concept": "链表遍历",
  "apply_safe": true
}
```

### 6.3 结果展示

MVP 阶段：

- 通过右键菜单触发；
- 在侧边栏或 WebView 面板展示建议；
- 展示“代码已规范”的积极反馈；
- 支持复制建议或查看修改原因。

增强阶段：

- 行内波浪线提示；
- 灯泡 Code Action；
- 单条建议一键应用；
- 忽略本条建议；
- 本文件重新检查；
- 查看进阶建议。

### 6.4 进阶知识提示

在 Advanced Mode 下，系统可给出一条可选、默认折叠的扩展提示。

进阶提示可以包括：

- 当前代码涉及的数据结构概念；
- 与教材章节相关的知识点；
- 常见错误提醒；
- 算法复杂度说明；
- 后续学习方向。

注意：进阶提示只用于学习参考，不参与自动修改。

---

## 七、系统架构

```text
学生 VS Code
    |
    | VS Code Extension API
    v
[插件前端 TypeScript]
    |
    | HTTP / JSON
    v
[FastAPI 后端控制层]
    |
    | 并行 / 串行编排
    |
    +--> clang-format
    |
    +--> clang-tidy / AST / tree-sitter
    |
    +--> 课程规则库 YAML/JSON
    |
    +--> Skill 库 / RAG 检索
    |
    +--> LangChain 编排层
          |
          +--> Prompt 管理
          +--> RAG 检索
          +--> 结构化输出解析
          +--> 重试与降级
    |
    +--> 输出 Schema 校验
    |
    +--> Patch / Diff / AST 安全校验
    |
    v
[统一建议结果]
    |
    v
VS Code 展示与交互
```

---

## 八、LangChain 技术定位

### 8.1 推荐结论

本项目确定采用 **LangChain + FastAPI** 完成 LLM 流程编排，不采用 Dify、Coze 等低代码工作流平台作为 MVP 技术路线。

LangChain 在本项目中负责：

- 组织基础检查 Prompt；
- 根据课程规则动态注入上下文；
- 调用 LLM 生成结构化建议；
- 接入 Skill 库和 RAG 检索；
- 解析并校验模型输出；
- 在输出失败时执行重试；
- 将模型建议传递给后端安全校验模块。

LangChain 不直接负责：

- 决定建议是否最终可展示；
- 决定建议是否可一键应用；
- 执行代码 patch；
- 判断算法逻辑是否改变；
- 替代后端规则库；
- 替代 AST / diff 安全校验。

### 8.2 LangChain 编排架构

```text
FastAPI 后端
    |
    +--> 代码预处理
    +--> clang-format / clang-tidy
    +--> 课程规则库
    +--> Skill / RAG 检索
    +--> LangChain 调用 LLM
    +--> Pydantic 结构化输出校验
    +--> Patch / Diff / AST 安全校验
    +--> 返回 VS Code
```

即：LangChain 负责编排 LLM 生成建议，FastAPI 后端负责裁决建议是否可信、是否安全、是否可展示。

### 8.3 不采用 Dify / Coze 的原因

本项目暂不采用 Dify / Coze，主要原因包括：

- 插件需要与代码安全校验、AST 检查、patch 应用深度集成；
- 后端需要精细控制模型输出、重试、降级和日志；
- 课程规则库和 Skill 库需要纳入版本管理；
- 未来可能需要本地化部署或私有化模型接入；
- 自研 FastAPI + LangChain 方案更适合工程落地和长期维护。

Dify / Coze 可作为后续教学展示或 Prompt 实验工具，但不进入 MVP 主链路。

---

## 九、LLM 输出约束机制

### 9.1 结构化输出

LLM 必须返回符合 JSON Schema 的结构化结果，不允许返回 Markdown、自然语言前缀或不完整 JSON。

响应示例：

```json
{
  "status": "has_suggestions",
  "message": "发现 2 处可读性建议",
  "suggestions": [
    {
      "id": "naming_001",
      "type": "naming",
      "severity": "info",
      "line_start": 1,
      "line_end": 1,
      "original": "int a, b;",
      "replacement": "int leftValue, rightValue;",
      "reason": "变量名应表达其含义，便于阅读输入数据的用途。",
      "course_concept": "变量命名与代码可读性",
      "confidence": 0.82,
      "apply_safe": true
    }
  ],
  "advanced_tip": null
}
```

### 9.2 Schema 校验

后端使用 Pydantic 或等价机制校验：

- 字段是否完整；
- 类型是否合法；
- 枚举值是否属于允许范围；
- 行号是否有效；
- replacement 是否为空；
- 建议数量是否超过限制；
- reason 是否过长；
- 是否包含禁止内容。

### 9.3 安全校验

后端对 LLM 输出进行二次验证：

- replacement 必须是局部替换；
- 不允许新增头文件；
- 不允许新增复杂数据结构；
- 不允许改变循环结构；
- 不允许改变条件表达式语义；
- 不允许改变函数调用关系；
- 不允许删除核心语句；
- 不允许修改输入输出逻辑；
- 不允许将当前算法替换为另一种算法。

### 9.4 失败处理

若 LLM 输出不合法：

1. 自动重试一次；
2. 若仍失败，丢弃 LLM 建议；
3. 仅返回 clang-format 或规则引擎结果；
4. 前端提示“智能建议暂不可用，请稍后重试”。

---

## 十、Prompt 设计

### 10.1 System Prompt

```text
你是数据结构课程的编程助教。
你的任务是帮助学生提升 C++ 代码的可读性和规范性。
你只能提出轻量、局部、教学友好的建议。
你不能改变算法逻辑、数据结构、控制流、时间复杂度或空间复杂度。
你不能替学生完成作业。
```

### 10.2 Boundary Prompt

```text
禁止提出以下建议：
1. 替换算法；
2. 引入新的数据结构；
3. 引入新的库；
4. 修改输入输出协议；
5. 改变循环条件或分支条件；
6. 进行性能优化；
7. 进行高级架构重构；
8. 输出完整重写后的代码。
```

### 10.3 Rule Prompt

由课程规则库动态注入：

```text
允许的常见缩写：
num, cnt, idx, res, tmp, cur, prev, next, head, tail

当前课程阶段：
线性表、链表、栈、队列、树、排序基础

当前检查范围：
命名、注释、魔数、基础可读性
```

### 10.4 Output Prompt

```text
你只能输出符合给定 JSON Schema 的 JSON。
不要输出 Markdown。
不要输出解释性前缀。
如果没有建议，status 必须为 clean，suggestions 必须为空数组。
每条建议必须是局部建议。
```

---

## 十一、规则库设计

规则库用于存储课程层面的确定性规范。

示例：

```yaml
allowed_abbreviations:
  - num
  - cnt
  - idx
  - res
  - tmp
  - cur
  - prev
  - next
  - head
  - tail

forbidden_suggestions:
  - algorithm_replacement
  - performance_optimization
  - advanced_architecture
  - new_library

max_suggestions_per_check: 5

severity_policy:
  naming: info
  comment: info
  readability: warning
  format: info
```

---

## 十二、Skill 库设计

Skill 库用于将课程经验结构化，帮助 LLM 生成更一致的建议。

### 12.1 Skill 类型

1. **规范 Skill**
   - 命名规范；
   - 注释规范；
   - 魔数规范；
   - 函数长度规范。

2. **数据结构主题 Skill**
   - 顺序表；
   - 链表；
   - 栈；
   - 队列；
   - 树；
   - 图；
   - 排序。

3. **教学表达 Skill**
   - 如何解释命名问题；
   - 如何解释注释问题；
   - 如何给出鼓励反馈；
   - 如何避免超纲建议。

### 12.2 Skill 示例

```yaml
id: linked_list_pointer_naming
title: 链表指针命名规范
scope:
  language: cpp
  topics:
    - linked_list
    - pointer
  issue_types:
    - naming
trigger:
  keywords:
    - Node*
    - head
    - next
    - p
    - q
rules:
  allowed_names:
    - head
    - tail
    - cur
    - prev
    - next
  discouraged_names:
    - p
    - q
guidance:
  principle: 指针变量应体现其在链表遍历中的角色。
  good_example: Node* cur = head;
  bad_example: Node* p = head;
llm_instruction: >
  如果学生在链表遍历中使用 p、q 等模糊指针名，
  可以建议改为 cur、prev、next 等角色名，
  但不能改变链表遍历逻辑。
```

---

## 十三、RAG 设计

RAG 不用于基础规范判断，而主要服务于 Advanced Mode 的教学拓展。

### 13.1 检索内容

- 教材章节摘要；
- 数据结构概念说明；
- 教师提供的典型代码；
- 常见错误案例；
- 课程规范文档；
- 实验指导书。

### 13.2 检索策略

根据代码特征生成检索关键词：

- 是否出现 `Node`、`next`、`head`；
- 是否出现栈、队列、树等结构；
- 是否出现排序循环；
- 是否出现递归；
- 是否出现指针操作。

检索结果只作为 LLM 的背景材料，不直接作为最终建议。

---

## 十四、核心 API 设计

### 14.1 检查接口

```text
POST /api/v1/style-check
```

请求：

```json
{
  "code": "int a,b;",
  "lang": "cpp",
  "mode": "basic",
  "context": {
    "file_name": "main.cpp",
    "course_stage": "linked_list",
    "selected_range": {
      "start_line": 1,
      "end_line": 20
    }
  },
  "user_preferences": {
    "ignored_rule_ids": []
  }
}
```

响应：

```json
{
  "status": "has_suggestions",
  "message": "发现 2 处可读性建议",
  "formatted_code": "int a, b;",
  "suggestions": [
    {
      "id": "naming_001",
      "type": "naming",
      "severity": "info",
      "line_start": 1,
      "line_end": 1,
      "original": "int a, b;",
      "replacement": "int leftValue, rightValue;",
      "reason": "变量名应表达其含义，便于阅读输入数据的用途。",
      "course_concept": "变量命名与代码可读性",
      "apply_safe": true,
      "confidence": 0.82
    }
  ],
  "advanced_tip": null,
  "metadata": {
    "ruleset_version": "2026-spring-v1",
    "llm_used": true,
    "workflow_engine": "langchain"
  }
}
```

---

## 十五、前端交互设计

### 15.1 MVP 交互

1. 学生选中代码或打开文件；
2. 右键点击“代码规范建议”；
3. 插件调用后端接口；
4. 面板展示建议列表；
5. 每条建议展示原因和可选替换；
6. 若无建议，展示积极反馈。

### 15.2 增强交互

- 行内 Diagnostic；
- 灯泡 Code Action；
- 一键应用单条建议；
- 忽略建议；
- 展开进阶知识提示；
- 查看课程规则说明。

---

## 十六、实施路线图

### Phase 1：MVP

1. 实现 FastAPI 后端；
2. 集成 `clang-format`；
3. 定义响应 JSON Schema；
4. 实现基础规则库；
5. 接入 LangChain 编排链路；
6. 实现 Pydantic 输出校验；
7. 开发 VS Code 插件右键触发；
8. 实现结果面板展示。

### Phase 2：可控增强

1. 加入 patch 安全校验；
2. 加入 AST 或 tree-sitter 结构检查；
3. 支持单条建议一键应用；
4. 实现忽略规则；
5. 建立基础 Skill 库；
6. 引入日志和建议质量评估。

### Phase 3：教学整合

1. 接入教材 RAG；
2. 支持教师可视化配置规则；
3. 构建课程知识图谱；
4. 输出班级层面的规范问题统计；
5. 支持教师通过配置文件维护课程规则和 Skill。

---

## 十七、成功标准

1. **使用率**：超过 60% 的学生在完成作业时主动使用插件不少于 3 次。
2. **理解度**：超过 70% 的学生表示能够理解插件建议原因。
3. **代码质量提升**：教师主观评估中，基础可读性问题减少 50% 以上。
4. **低干扰**：学生反馈插件不会干扰算法思考和调试过程。
5. **输出稳定性**：LLM 输出 JSON Schema 校验通过率达到 95% 以上。
6. **安全性**：自动应用建议不得改变算法逻辑。

---

## 十八、主要风险与应对

| 风险 | 说明 | 应对 |
| --- | --- | --- |
| LLM 输出不稳定 | JSON 格式错误或建议发散 | Schema 校验、重试、失败降级 |
| 模型误改逻辑 | 建议可能改变算法行为 | 局部 patch、AST 校验、禁止自动整体重写 |
| 建议超纲 | 引入高级设计或算法 | 课程阶段配置、禁用建议类型 |
| 学生过度依赖 | 直接接受建议而不理解 | 必须展示原因，不默认自动应用 |
| 教师规则不统一 | 不同教师规范偏好不同 | 规则包版本化、教师可配置 |
| LangChain 编排复杂度增加 | Prompt、RAG、重试和校验链路可能变复杂 | 将 LangChain 封装在独立 service 中，保持接口稳定 |

---

## 十九、目录结构建议

```text
project/
  frontend/
    extension/
      src/
      package.json
  backend/
    app/
      api/
      services/
      schemas/
      prompts/
      rules/
      skills/
      validators/
    tests/
  docs/
    prd/
    ruleset/
```

---

## 二十、总结

本插件的核心不是让 LLM 替学生改代码，而是通过确定性工具、课程规则库和受控的 LLM 教学表达，为学生提供轻量、可信、可理解的代码规范反馈。

推荐采用：

```text
VS Code 插件 + FastAPI 后端 + 规则库 + LangChain + 结构化输出校验 + Patch 安全验证
```

本项目主链路采用 LangChain 实现 LLM 编排，所有规范性、安全性和课程一致性由自研 FastAPI 后端控制层保障。
