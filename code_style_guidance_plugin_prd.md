# 数据结构课程代码规范指导插件（Code Style Guidance Plugin）PRD

---

# 一、产品背景（Background）

在数据结构课程的教学过程中，学生通常能够编写出可以运行的程序，但代码在以下方面存在较大差异：

- 代码风格不统一（缩进、空格、换行）
- 变量命名不规范
- 注释不足或缺失
- 代码结构可读性较差

目前大多数教学平台主要关注：

- 程序是否通过测试用例
- 算法是否正确

而较少对：

> 代码规范（Code Style）与可读性（Readability）进行系统训练。

因此，本任务旨在创建一个：

> **代码规范指导插件**

该插件在学生编写代码后，能够提供轻量级规范建议，并解释原因，帮助学生逐步形成良好的编码习惯。

---

# 二、产品目标（Goals）

本插件的目标：

> 在不改变算法、不引入超纲内容的前提下，对学生代码提供轻量规范建议，并解释原因。

核心原则：

- 不强制修改
- 不进行复杂优化
- 不改变算法逻辑
- 不过度修改学生代码

---

# 三、非目标（Non-Goals）

以下内容 **不在本期实现范围**：

- 代码质量评分系统
- 自动复杂度分析
- 自动算法优化
- 自动重构为更高级数据结构
- 代码自动提交或自动替换
- 工业级代码审查系统

---

# 四、目标用户（Target Users）

主要用户：

- 数据结构课程初学者
- 大一 / 大二计算机专业学生

用户特点：

- 编程经验有限
- 正在学习基础语法与数据结构
- 需要明确、可理解的规范提示

---

# 五、核心功能（Core Features）

本插件包含以下 4 个核心功能：

1）代码规范检查

2）规范建议生成

3）规范原因解释

4）规范完成提示

---

# 六、用户使用流程

## 场景：学生希望检查一段代码是否规范

```text
学生编写代码

        ↓

选中一段代码（或整个文件）

        ↓

右键

        ↓

点击：

代码规范建议

        ↓

插件调用后端 API

        ↓

系统返回：

规范建议
修改说明

        ↓

在编辑器中显示结果
```

---

# 七、交互设计（Interaction Design）

## 触发方式

```text
右键菜单

→ 代码规范建议
```

---

## 输入

```cpp
int a,b;
cin>>a>>b;
```

---

## 输出示例

```text
建议如下：

1. 建议使用更清晰的变量名（可选）

---

修改后的代码：

int num1, num2;
cin >> num1 >> num2;
```

---

## 若代码已经规范

系统显示：

```text
代码已经很规范了！
请继续保持良好的编码习惯。
```

---

## 进阶（可选按钮）

```text
查看进阶建议（选做）
```

点击后：

```text
可以考虑使用更高效的数据结构
```

默认不展示。

---

# 八、系统架构（System Architecture）

```text
Web VS Code (Monaco Editor)

        │
        │ HTTP
        ▼

Code Style Extension

        │
        ▼

Backend API Server

        │
        ├── clang-format
        │
        ├── clang-tidy
        │
        └── LLM API
```

---

# 九、技术栈（Tech Stack）

## 前端（插件）

```text
TypeScript
VS Code Extension API
Monaco Editor
```

---

## 后端

```text
Python
FastAPI
```

---

## 代码规范工具

```text
clang-format
clang-tidy
```

---

# 十、核心接口设计（API Design）

## API

```text
POST /api/style-check
```

---

## 请求

```json
{
  "code": "int a,b;",
  "mode": "basic"
}
```

---

## 返回

```json
{
  "status": "has_suggestions",
  "message": "发现 2 条规范建议",
  "normalized_code": "...",
  "suggestions": [
    {
      "type": "format",
      "reason": "建议在运算符两侧添加空格"
    }
  ]
}
```

---

# 十一、Prompt 设计（关键）

## 基础 Prompt（Basic Mode）

```text
你是数据结构课程的编程助教。

请对以下 C++ 代码进行轻量规范检查。

目标：

1. 提高代码可读性
2. 保持算法与逻辑完全不变
3. 不要引入新数据结构
4. 不要进行性能优化
5. 不要添加超纲内容

请特别注意：

如果代码已经规范，请直接回复：

代码已经很规范了！

不要过度修改代码。

允许使用常见缩写变量名，例如：

num
res
cnt
idx
temp

如果变量名清晰，请保持不变。

如果代码中存在：

using namespace std;

请不要额外添加 std:: 前缀。

输出格式：

1. 是否需要修改
2. 修改后的代码（如有）
3. 修改原因（逐条说明）
```

---

## 进阶 Prompt（Advanced Mode）

```text
在基础规范建议之外，提供可选的进阶优化建议。

注意：

这些建议仅用于学习参考，不要默认修改代码。
```

---

# 十二、插件核心逻辑（Plugin Logic）

```text
用户选中代码

        ↓

插件读取选区

        ↓

发送请求：

POST /api/style-check

        ↓

后端执行：

1. clang-format
2. clang-tidy
3. LLM 规范建议

        ↓

返回结果

        ↓

插件展示建议
```

---

# 十三、最小可实现版本（MVP）

必须实现：

```text
右键菜单：代码规范建议

发送代码到后端

返回规范建议

显示修改原因

若代码规范：

显示：

代码已经很规范了！
```

---

# 十四、实现步骤（Implementation Plan）

## Step 1

安装工具：

```bash
clang-format
clang-tidy
```

---

## Step 2

实现后端 API

```python
POST /api/style-check
```

---

## Step 3

实现调用 clang-format

---

## Step 4

接入 AI API

---

## Step 5

实现 VS Code 插件

---

## Step 6

在编辑器中展示建议

---

# 十五、目录结构建议（Project Structure）

```text
project/

frontend/

extension/

backend/

api/

services/

prompt/
```

---

# 十六、未来可扩展功能（Future Scope）

以下功能建议在后续版本考虑：

```text
进阶优化建议
复杂度提示
自动注释建议
代码示例推荐
课程规范模板
```

---

# 十七、成功标准（Success Criteria）

本功能上线后，满足：

```text
学生能够主动检查代码规范
学生能够理解修改原因
学生代码可读性明显提升
教师无需手动指出基础风格问题
```

