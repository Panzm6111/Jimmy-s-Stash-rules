# 海外 AI 分流覆盖

`海外AI` 是原来 `OpenAI` 策略组的扩展，默认选择 `美国`。美国组再从自己的节点中自动选择探测延迟最低的节点；也可以手动把海外 AI 改到其他地区。AI 分流不需要 MITM 证书，不解密聊天内容。

更新后请在 Stash 的代理页面确认一次：`海外AI → 美国`。已有界面选择是否保留取决于 Stash；重命名后的组不能沿用旧组名来保证选择保留。探测通过只表示测试地址可达，AI 服务能否使用仍受账号、地区、节点 IP 和平台政策影响。

## 本次实际加入

核实日期：**2026-10-19**。共 **25 类服务、123 条域名规则**，覆盖主站、已知专用 API 和部分专用资源域名。下表是代表域名，完整清单在 [rules/openai.yaml](../rules/openai.yaml)。保留这个已有文件路径，便于原链接继续更新。

| 服务 | 代表域名 |
| --- | --- |
| OpenAI / ChatGPT / Sora | `openai.com`、`chatgpt.com`、`sora.com` |
| Anthropic / Claude | `anthropic.com`、`claude.ai`、`claudeusercontent.com` |
| Google AI：Gemini、AI Studio、NotebookLM、Code Assist、Jules、Flow、Opal、Antigravity、Stitch | `gemini.google.com`、`aistudio.google.com`、`notebooklm.google.com`、`generativelanguage.googleapis.com` 等专用主机 |
| Microsoft Copilot | `copilot.microsoft.com`、`copilot.cloud.microsoft`、`copilot.com` |
| GitHub Copilot | `githubcopilot.com`、`copilot-proxy.githubusercontent.com` |
| Perplexity | `perplexity.ai`、`pplx.ai` |
| Poe | `poe.com`、`poecdn.net` |
| xAI / Grok | `grok.com`、`x.ai` |
| Meta AI | `meta.ai`、`metaaivm.com` |
| Cohere | `cohere.ai`、`cohere.com` |
| Mistral | `mistral.ai` |
| Midjourney | `midjourney.com` |
| Jasper / Clipdrop | `jasper.ai`、`clipdrop.co` |
| NovelAI | `novelai.net` |
| OpenRouter | `openrouter.ai` |
| Groq | `groq.com` |
| Cerebras | `cerebras.ai` |
| Hugging Face | `huggingface.co`、`hf.co`、`hf.space` |
| Cursor | `cursor.com`、`cursor.sh`、`cursorapi.com` |
| Windsurf / Codeium | `windsurf.com`、`codeium.com` |
| ElevenLabs | `elevenlabs.io`、`elevenlabs.com` |
| JetBrains AI / Grazie | `jetbrains.ai`、`grazie.ai` |
| Devin | `devin.ai` |
| CodeRabbit | `coderabbit.ai` |
| Duck.ai | `duck.ai` |

“海外 AI”是策略用途，域名名单不能自动识别所有未知、刚上线或改域名的 AI 服务。当前已审核来源没有涵盖 Suno、Runway、Character.AI、Stability、Leonardo、Recraft，本轮未将这些服务标为已覆盖，后续须补充可靠来源。中国 AI 不加入这份清单，包括 DeepSeek、Kimi、豆包、千问等；它们仍按原有国内及其他分流规则处理。默认国内规则没有命中的新域名，也可能需要根据实际连接补充。

## 分流边界与故障处理

- Copilot 的专用域名规则排在普通 Microsoft 规则前，因此 Copilot 可以走美国，同时 Microsoft 普通业务仍保持原有策略。GitHub Copilot 与普通 GitHub 也分别处理。
- Google、Microsoft、GitHub 以及共享云服务只加入已列出的 AI 专用域名。`google.com`、`microsoft.com`、`github.com`、`auth0.com`、`cloudflare.com` 等整站不会因此改走美国。
- 登录、验证码、支付、第三方模型或共享后端可能使用清单之外的主机，因此可能继续走其原有策略。嵌在其他 App 内、与普通业务共用同一域名的 AI 功能，也不能只靠域名规则单独识别。
- 美国节点全部失效时，先恢复或更换美国节点；如需换地区，由你在 `海外AI` 中明确选择。配置不会在美国组里加入其他国家或直连作为后备。
- 出现“地区不支持”或登录循环时，先确认 `海外AI → 美国` 与实际选中节点，再查看 Stash 连接记录中的主机名和命中策略。反馈域名、策略和错误文字即可，不发送聊天内容、Cookie、token 或完整请求地址。

## 来源、许可和维护

主要来源是 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)，固定提交 [`6ee52f2c36634aeabeb9c4ba486ca02cd84c3d4f`](https://github.com/v2fly/domain-list-community/tree/6ee52f2c36634aeabeb9c4ba486ca02cd84c3d4f)，提交日期为 2026-10-19，采用 [MIT 许可](../licenses/v2fly-domain-list-community-MIT.txt)。已读取实际数据文件和许可证。它是域名资料来源；此项目只将人工选中的域名转换为 Stash 的 `DOMAIN`、`DOMAIN-SUFFIX` 规则，不导入其他客户端配置。

上游 `category-ai-!cn` 同时含有部分中国厂商面向海外的服务，其名称不能用来判断厂商归属。本项目逐条选择已知海外服务，并记录所有未选条目；遥测、广告、无法确认专属性的条目、共享 `host.livekit.cloud` / `turn.livekit.cloud` 及正则条目均未直接导入。原项目已有的 `openai-api.arkoselabs.com` 专用主机规则继续保留。

[research/ai-sources.json](../research/ai-sources.json) 记录 15 个源文件的固定 URL、SHA-256、逐条选择和剔除清单、转换方法与本地规则出处。[生成工具](../tools/generate_ai_rules.py) 可以复现产物：

```sh
python tools/generate_ai_rules.py
# 有对应提交的上游检出目录时，可同时验证源文件和许可：
python tools/generate_ai_rules.py --source-dir /path/to/domain-list-community
```

未来更新应先审阅新来源，再修改这份 manifest 并运行 `--write`，随后执行项目验证及重新生成主配置。不要把上游整个 AI 分类不经审阅直接覆盖进来。

上述验证属于源文件、语法、转换与路由模型检查；尚未在你的 iPhone 上逐一验证这些平台登录、访问和服务解锁。
