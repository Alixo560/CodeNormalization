# 1. 命名规范（最重要）

## （1）类名：PascalCase

类名每个单词首字母大写。

```cpp
class BinaryTree;
class LinkedList;
class GraphNode;
```

不要：

```cpp
class binary_tree;
class graph_node;
```

------

## （2）函数名：PascalCase

```cpp
InsertNode()
DeleteEdge()
FindShortestPath()
```

------

## （3）变量名：snake_case

局部变量、普通变量：

```cpp
int node_count;
int max_depth;
```

------

## （4）类成员变量：末尾加 `_`

这是 Google 非常经典的规则。

```cpp
class Stack {
 private:
    int top_;
    int size_;
};
```

目的：

- 一眼区分成员变量
- 避免 `this->`
- 避免变量遮蔽

------

## （5）常量

常量一般：

```cpp
const int kMaxSize = 100;
```

Google 使用：

- `k` 开头
- PascalCase

------

# 2. 文件组织规范

## （1）一个 `.cc` 对应一个 `.h`

例如：

```text
binary_tree.h
binary_tree.cc
```

这是大型工程最基本结构。 ([google.github.io](https://google.github.io/styleguide/cppguide.html?utm_source=chatgpt.com))

------

## （2）头文件必须“自包含”

意思是：

```cpp
#include "xxx.h"
```

后应该能单独编译。

因此：

- 头文件必须自己 include 所需依赖
- 不能依赖“间接 include”

Google 强调：

> “Include What You Use” ([google.github.io](https://google.github.io/styleguide/cppguide.html?utm_source=chatgpt.com))

即：

> 用什么，就 include 什么。

------

### 错误示例

```cpp
// A.h
#include <vector>

// B.h
#include "A.h"

std::vector<int> v;
```

虽然能编译，但不规范。

因为：

```cpp
B.h
```

自己使用了 `vector`，
却没有：

```cpp
#include <vector>
```

------

## （3）头文件保护（Header Guard）

每个 `.h`：

```cpp
#ifndef DATA_STRUCTURE_STACK_H_
#define DATA_STRUCTURE_STACK_H_

class Stack {};

#endif
```

作用：

- 防止重复 include

这是工业代码必须掌握的。

------

# 3. Include 顺序

Google 要求 include 有固定顺序。

例如：

```cpp
#include "binary_tree.h"

#include <iostream>
#include <vector>

#include "graph.h"
```

核心思想：

- 标准库
- 第三方库
- 自己项目

要分层清晰。

------

# 4. 类的访问控制

Google 强调：

> 成员变量默认 private。 ([google.github.io](https://google.github.io/styleguide/cppguide.html?utm_source=chatgpt.com))

例如：

```cpp
class Queue {
 public:
    void Push(int x);

 private:
    std::vector<int> data_;
};
```

不要：

```cpp
class Queue {
 public:
    vector<int> data;
};
```

因为：

- 会破坏封装
- 外部能随意修改内部状态

------

# 5. 类内部顺序

Google 推荐：

```cpp
class BinaryTree {
 public:
    BinaryTree();
    void Insert(int x);

 private:
    TreeNode* root_;
};
```

顺序：

1. public
2. protected
3. private

且：

- public 放前面
- private 放后面

因为用户最关心接口。

------

# 6. 变量作用域最小化

Google 非常强调：

> 变量在哪里用，就在哪里定义。 ([google.github.io](https://google.github.io/styleguide/cppguide.html?utm_source=chatgpt.com))

------

## 不推荐

```cpp
int i;

for (i = 0; i < n; i++) {
}
```

------

## 推荐

```cpp
for (int i = 0; i < n; i++) {
}
```

原因：

- 降低错误率
- 减少变量污染

------

# 7. 不鼓励复杂语法炫技

Google 的整体倾向是：

> “代码首先是给人看的，其次才是给机器运行的。”

因此：

- 不喜欢过度模板元编程
- 不鼓励复杂宏
- 不鼓励难读写法
- 更强调清晰

这点非常适合初学者。

------

# 8. 注释规范

Google 对注释要求：

## 注释解释“为什么”

而不是解释“代码是什么”。

------

## 差的注释

```cpp
i++; // i加1
```

------

## 好的注释

```cpp
// 跳过已经访问过的节点
i++;
```

------

# 9. 命名空间（namespace）

Google 强调：

- 必须使用 namespace
- 禁止：

```cpp
using namespace std;
```

因为大型工程容易冲突。 ([google.github.io](https://google.github.io/styleguide/cppguide.html?utm_source=chatgpt.com))

推荐：

```cpp
std::vector<int> nums;
```

------

# 10. 代码风格的一致性

Google 最核心思想：

> 整个项目看起来像一个人写的。

因此：

- 缩进统一
- 命名统一
- 空格统一
- 文件结构统一

远比“你个人觉得好看”重要。

------

# 必须

### 1. 命名规范

- 类 PascalCase
- 变量 snake_case
- 成员变量 `_`

------

### 2. 缩进与大括号

```cpp
if (...) {
    ...
}
```

不要省略 `{}`。

------

### 3. 头文件规范

- `.h + .cc`
- include guard

------

### 4. 不使用：

```cpp
using namespace std;
```

------

### 5. 类成员 private

------

### 6. 函数职责单一

一个函数不要写 300 行。

------

# 次之

再学习：

- const correctness
- 引用 vs 指针
- RAII
- move semantics
- template 规范
- 异常安全

------

# 可以忽略

- Google Test
- Bazel/CMake
- clang-format
- 大型项目目录结构
- 抽象层设计
- API 设计

------

# Google 规范的优点

## 1. 工程化极强

非常适合：

- 团队协作
- 大项目
- 企业开发

------

## 2. 一致性极强

看代码非常舒服。

------

## 3. 非常强调可读性

对初学者是好事。

------

# Google 规范的缺点

## 1. 有点“保守”

它会限制一些高级 C++ 特性。

社区有人认为：

> “Google 更像在约束 C++，而不是发挥 C++。” ([Reddit](https://www.reddit.com/r/cpp/comments/zajjsk?utm_source=chatgpt.com))

------

## 2. 偏大型工程

有些规则：

- 对算法竞赛
- 小项目
- 学校实验

其实过重。

