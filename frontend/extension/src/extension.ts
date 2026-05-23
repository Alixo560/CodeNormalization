import * as vscode from 'vscode';

type StyleCheckResponse = {
  status: 'clean' | 'has_suggestions' | 'partial';
  message: string;
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

export function activate(context: vscode.ExtensionContext) {
  const command = vscode.commands.registerCommand('dsStyleGuidance.checkSelection', async () => {
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
      const isFetchFailed =
        message === 'fetch failed' ||
        message.includes('fetch failed') ||
        (error instanceof TypeError && String(error.cause ?? '').includes('ECONNREFUSED'));
      const hint = isFetchFailed
        ? ` 无法连接 ${apiBaseUrl}。请先在本仓库根目录终端执行 npm run dev:backend（若未装全局 python，可用 package.json 里的 dev:backend:conda），再重试检查。`
        : '';
      vscode.window.showErrorMessage(`代码规范检查失败：${message}。${hint}`);
    }
  });

  context.subscriptions.push(command);
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
      ${result.suggestions.length ? suggestionHtml : '<p>代码风格良好，可读性高。</p>'}
    </body>
    </html>
  `;
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
