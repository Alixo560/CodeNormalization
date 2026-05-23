# 数据结构课程代码规范指导插件

这是一个面向数据结构课程的 VS Code 插件原型，采用：

- VS Code Extension + TypeScript
- FastAPI 后端
- LangChain 编排层
- 规则库 + 结构化输出校验 + 安全校验

## 开发环境

- Node.js 22+
- npm
- VS Code
- Anaconda Python 3.10 环境：`D:/Conda/envs/mcm_py310/python.exe`

## 启动后端

首次接入硅基流动 API 前，复制 `.env.example` 为 `.env`，并填写：

```env
SILICONFLOW_API_KEY=你的硅基流动 API Key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_ENABLED=1
```

如果暂时不想调用真实模型，可以设置：

```env
LLM_ENABLED=0
```

```powershell
npm.cmd run dev:backend
```

## 编译插件

```powershell
npm.cmd --prefix frontend/extension install
npm.cmd --prefix frontend/extension run compile
```

## 运行插件

在 VS Code 中打开 `frontend/extension`，按 `F5` 启动 Extension Development Host。
