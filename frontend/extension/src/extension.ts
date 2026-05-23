import * as vscode from 'vscode';

type StyleCheckResponse = {
  status: 'clean' | 'has_suggestions' | 'partial';
  message: string;
  structure_detection?: StructureDetection | null;
  metadata?: {
    ruleset_version: string;
    llm_used: boolean;
    workflow_engine: string;
  };
  suggestions: Array<{
    id: string;
    type: string;
    severity: string;
    line_start: number;
    line_end: number;
    original: string;
    replacement?: string | null;
    reason: string;
    course_concept?: string | null;
    apply_safe: boolean;
    confidence: number;
  }>;
};

type StructureDetection = {
  primary_structure?: string | null;
  secondary_structures: string[];
  confidence: number;
  evidence: string[];
};

type VisualIR = {
  structure?: string | null;
  operation?: string | null;
  roles: Array<{
    name: string;
    role: string;
  }>;
  visual_tags: string[];
};

type NormalizeCodeResponse = {
  status: 'normalized' | 'unchanged' | 'partial';
  message: string;
  normalized_code: string;
  diff?: string | null;
  structure_detection: StructureDetection;
  visual_ir?: VisualIR | null;
  suggestions: StyleCheckResponse['suggestions'];
  applied_changes: Array<{
    id: string;
    type: string;
    safety: string;
    reason: string;
  }>;
  blocked_changes: Array<{
    id: string;
    type: string;
    safety: string;
    reason: string;
  }>;
  metadata?: {
    ruleset_version: string;
    llm_used: boolean;
    workflow_engine: string;
  };
};

export function activate(context: vscode.ExtensionContext) {
  const checkCommand = vscode.commands.registerCommand('dsStyleGuidance.checkSelection', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showInformationMessage('请先打开一个 C/C++ 文件。');
      return;
    }

    const document = editor.document;
    const selection = editor.selection;
    const code = selection.isEmpty ? document.getText() : document.getText(selection);

    if (!code.trim()) {
      vscode.window.showInformationMessage('没有可检查的代码。');
      return;
    }

    const config = vscode.workspace.getConfiguration('dsStyleGuidance');
    const apiBaseUrl = config.get<string>('apiBaseUrl', 'http://127.0.0.1:8010');
    const lang = getSupportedLanguageId(document.languageId);

    try {
      const result = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'AI 正在分析代码...',
          cancellable: false
        },
        async (progress) => {
          progress.report({ message: '正在调用代码规范检查服务' });
          const response = await fetch(`${apiBaseUrl}/api/v1/style-check`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              code,
              lang,
              mode: 'basic',
              context: {
                file_name: document.fileName,
                selected_range: {
                  start_line: selection.isEmpty ? 1 : selection.start.line + 1,
                  end_line: selection.isEmpty ? document.lineCount : selection.end.line + 1
                }
              },
              user_preferences: {
                ignored_rule_ids: []
              }
            })
          });

          if (!response.ok) {
            throw new Error(`后端返回 ${response.status}`);
          }

          progress.report({ message: '正在整理建议' });
          return (await response.json()) as StyleCheckResponse;
        }
      );
      showResultPanel(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const hint = buildConnectionHint(message, error, apiBaseUrl);
      vscode.window.showErrorMessage(`代码规范检查失败：${message}。${hint}`);
    }
  });

  const normalizeCommand = vscode.commands.registerCommand('dsStyleGuidance.normalizeSelection', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showInformationMessage('请先打开一个 C/C++ 文件。');
      return;
    }

    const document = editor.document;
    const selection = editor.selection;
    const code = selection.isEmpty ? document.getText() : document.getText(selection);

    if (!code.trim()) {
      vscode.window.showInformationMessage('没有可规范化的代码。');
      return;
    }

    const config = vscode.workspace.getConfiguration('dsStyleGuidance');
    const apiBaseUrl = config.get<string>('apiBaseUrl', 'http://127.0.0.1:8010');
    const lang = getSupportedLanguageId(document.languageId);

    try {
      const result = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: '正在生成规范化预览...',
          cancellable: false
        },
        async (progress) => {
          progress.report({ message: '正在调用代码规范化服务' });
          const response = await fetch(`${apiBaseUrl}/api/v1/normalize-code`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              code,
              lang,
              apply_level: 'safe_only',
              context: {
                file_name: document.fileName,
                selected_range: {
                  start_line: selection.isEmpty ? 1 : selection.start.line + 1,
                  end_line: selection.isEmpty ? document.lineCount : selection.end.line + 1
                }
              },
              user_preferences: {
                ignored_rule_ids: []
              }
            })
          });

          if (!response.ok) {
            throw new Error(`后端返回 ${response.status}`);
          }

          progress.report({ message: '正在整理规范化结果' });
          return (await response.json()) as NormalizeCodeResponse;
        }
      );
      showNormalizePanel(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const hint = buildConnectionHint(message, error, apiBaseUrl);
      vscode.window.showErrorMessage(`代码规范化失败：${message}。${hint}`);
    }
  });

  context.subscriptions.push(checkCommand, normalizeCommand);
}

function getSupportedLanguageId(languageId: string): 'c' | 'cpp' {
  if (languageId === 'c') {
    return 'c';
  }
  return 'cpp';
}

function showResultPanel(result: StyleCheckResponse) {
  const panel = vscode.window.createWebviewPanel(
    'dsStyleGuidanceResult',
    '代码规范建议',
    vscode.ViewColumn.Beside,
    {
      enableScripts: false
    }
  );

  const suggestionHtml = result.suggestions
    .map((suggestion, index) => {
      const replacement = suggestion.replacement
        ? `<pre><code>${escapeHtml(suggestion.replacement)}</code></pre>`
        : '<p>AI 未提供具体替换片段，可参考上方原因说明。</p>';

      return `
        <section class="suggestion">
          <h2>建议 ${index + 1}：${escapeHtml(suggestion.type)}</h2>
          <p><strong>位置：</strong>第 ${suggestion.line_start} 行</p>
          <p><strong>原因：</strong>${escapeHtml(suggestion.reason)}</p>
          ${suggestion.course_concept ? `<p><strong>关联知识点：</strong>${escapeHtml(suggestion.course_concept)}</p>` : ''}
          <p><strong>原代码：</strong></p>
          <pre><code>${escapeHtml(suggestion.original)}</code></pre>
          <p><strong>建议内容：</strong></p>
          ${replacement}
        </section>
      `;
    })
    .join('');
  const structureHtml = renderStructureDetection(result.structure_detection);

  panel.webview.html = `
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <style>
        body {
          font-family: var(--vscode-font-family);
          padding: 16px;
          line-height: 1.6;
        }
        h1 {
          font-size: 20px;
        }
        h2 {
          font-size: 15px;
          margin-top: 0;
        }
        .suggestion {
          border: 1px solid var(--vscode-panel-border);
          border-radius: 6px;
          padding: 12px;
          margin: 12px 0;
        }
        .llm-fallback {
          border: 1px solid var(--vscode-inputValidation-warningBorder);
          background: var(--vscode-inputValidation-warningBackground);
          padding: 10px 12px;
          border-radius: 6px;
          margin-bottom: 12px;
        }
        pre {
          background: var(--vscode-textCodeBlock-background);
          padding: 10px;
          overflow-x: auto;
        }
      </style>
    </head>
    <body>
      ${
        result.metadata && !result.metadata.llm_used
          ? `<p class="llm-fallback" role="status"><strong>提示：</strong>本次未调用硅基流动模型（本地规则结果）。请确认仓库根目录或 <code>backend</code> 下存在 <code>.env</code> 且已配置 <code>SILICONFLOW_API_KEY</code>，并查看运行后端的终端日志；也可访问 <code>/health</code> 查看 <code>siliconflow_api_key_configured</code>。</p>`
          : ''
      }
      <h1>${escapeHtml(result.message)}</h1>
      ${structureHtml}
      ${result.suggestions.length ? suggestionHtml : '<p>代码风格良好，可读性高。</p>'}
    </body>
    </html>
  `;
}

function showNormalizePanel(result: NormalizeCodeResponse) {
  const panel = vscode.window.createWebviewPanel(
    'dsStyleGuidanceNormalizeResult',
    '代码规范化预览',
    vscode.ViewColumn.Beside,
    {
      enableScripts: false
    }
  );

  const appliedHtml = result.applied_changes.length
    ? result.applied_changes
        .map(
          (change) => `
            <li>
              <strong>${escapeHtml(change.type)}</strong>
              <span class="badge">${escapeHtml(change.safety)}</span>
              ${escapeHtml(change.reason)}
            </li>
          `
        )
        .join('')
    : '<li>暂无自动应用的安全修改。</li>';

  const blockedHtml = result.blocked_changes.length
    ? result.blocked_changes
        .map(
          (change) => `
            <li>
              <strong>${escapeHtml(change.type)}</strong>
              <span class="badge">${escapeHtml(change.safety)}</span>
              ${escapeHtml(change.reason)}
            </li>
          `
        )
        .join('')
    : '<li>没有被阻止的修改。</li>';

  panel.webview.html = `
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <style>
        body {
          font-family: var(--vscode-font-family);
          padding: 16px;
          line-height: 1.6;
        }
        h1 {
          font-size: 20px;
        }
        h2 {
          font-size: 15px;
          margin-top: 20px;
        }
        .section {
          border: 1px solid var(--vscode-panel-border);
          border-radius: 6px;
          padding: 12px;
          margin: 12px 0;
        }
        .badge {
          display: inline-block;
          margin: 0 6px;
          padding: 1px 6px;
          border: 1px solid var(--vscode-panel-border);
          border-radius: 999px;
          font-size: 12px;
        }
        pre {
          background: var(--vscode-textCodeBlock-background);
          padding: 10px;
          overflow-x: auto;
        }
      </style>
    </head>
    <body>
      <h1>${escapeHtml(result.message)}</h1>
      ${renderStructureDetection(result.structure_detection)}
      ${renderVisualIr(result.visual_ir)}
      <section class="section">
        <h2>规范化代码</h2>
        <pre><code>${escapeHtml(result.normalized_code)}</code></pre>
      </section>
      <section class="section">
        <h2>Diff</h2>
        ${result.diff ? `<pre><code>${escapeHtml(result.diff)}</code></pre>` : '<p>本次没有生成代码差异。</p>'}
      </section>
      <section class="section">
        <h2>已应用修改</h2>
        <ul>${appliedHtml}</ul>
      </section>
      <section class="section">
        <h2>未自动应用修改</h2>
        <ul>${blockedHtml}</ul>
      </section>
    </body>
    </html>
  `;
}

function renderStructureDetection(structure?: StructureDetection | null): string {
  if (!structure || !structure.primary_structure) {
    return '';
  }

  const evidence = structure.evidence.length
    ? `<p><strong>识别证据：</strong>${structure.evidence.map(escapeHtml).join('、')}</p>`
    : '';
  const secondary = structure.secondary_structures.length
    ? `<p><strong>可能相关结构：</strong>${structure.secondary_structures.map(escapeHtml).join('、')}</p>`
    : '';

  return `
    <section class="suggestion section">
      <h2>数据结构识别</h2>
      <p><strong>主结构：</strong>${escapeHtml(structure.primary_structure)}</p>
      <p><strong>置信度：</strong>${Math.round(structure.confidence * 100)}%</p>
      ${secondary}
      ${evidence}
    </section>
  `;
}

function renderVisualIr(visualIr?: VisualIR | null): string {
  if (!visualIr || (!visualIr.structure && !visualIr.visual_tags.length && !visualIr.roles.length)) {
    return '';
  }

  const roles = visualIr.roles.length
    ? `<p><strong>角色：</strong>${visualIr.roles
        .map((role) => `${escapeHtml(role.name)} = ${escapeHtml(role.role)}`)
        .join('、')}</p>`
    : '';
  const tags = visualIr.visual_tags.length
    ? `<p><strong>可视化标签：</strong>${visualIr.visual_tags.map(escapeHtml).join('、')}</p>`
    : '';

  return `
    <section class="section">
      <h2>可视化 IR</h2>
      ${visualIr.structure ? `<p><strong>结构：</strong>${escapeHtml(visualIr.structure)}</p>` : ''}
      ${visualIr.operation ? `<p><strong>操作：</strong>${escapeHtml(visualIr.operation)}</p>` : ''}
      ${roles}
      ${tags}
    </section>
  `;
}

function buildConnectionHint(message: string, error: unknown, apiBaseUrl: string): string {
  const isFetchFailed =
    message === 'fetch failed' ||
    message.includes('fetch failed') ||
    (error instanceof TypeError && String(error.cause ?? '').includes('ECONNREFUSED'));
  return isFetchFailed
    ? ` 无法连接 ${apiBaseUrl}。请先在本仓库根目录终端执行 npm run dev:backend（若未装全局 python，可用 package.json 里的 dev:backend:conda），再重试。`
    : '';
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function deactivate() {}
