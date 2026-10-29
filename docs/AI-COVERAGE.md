# 海外 AI 分流覆盖

2026-10-29起，两端的 `海外AI` 直接使用社区维护的完整分类：MetaCubeX 的 `category-ai-!cn` 与 Sukka 的 `Source/non_ip/ai.conf`，只做兼容格式转换和去重。当前两份来源分别213条、55条，合并为231条；原 [rules/openai.yaml](../rules/openai.yaml) 地址保持不变。来源、提交、许可和逐文件哈希见 [community-sources.json](../research/community-sources.json)。

`海外AI` 默认美国。两端将原“日本+美国”改为 `ai`，在日本、美国、新加坡、台湾节点间自动测速选优，各业务select组都可选择；其他选项及默认值保留。Clash带前缀入口显示为 `Jimmy · ai`；测速地址成功不代表账号、地区和平台风控一定通过。AI分流不需要MITM，不解密聊天正文。

## 覆盖与边界

覆盖由上游分类决定，包括ChatGPT、Claude、Gemini、Copilot、Perplexity、Grok、Cursor等服务及上游收录的依赖。本项目不再手工选择25类服务或逐条维护域名；旧 [ai-sources.json](../research/ai-sources.json) 明确标为历史资料，退出当前生成链。

`!cn` 是上游分类名，不等于厂商国籍证明；其中可能包含中国厂商面向海外的服务。共享依赖 `host.livekit.cloud` 本轮按上游分类进入AI组，因此其他使用相同主机的业务也可能走AI出口。此处遵循完整维护集，不再本地挑选排除项。

Sukka源中的一条Gemini跳转 `URL-REGEX` 需要URL层语义，不能等价转换成两端通用域名规则；转换器显式记录该条未采用，保留其余完整域名规则。新增未知规则类型会使维护停止。没有增加Google全域MITM。

AI在普通Microsoft、GitHub及通用海外分类之前。`api.github.com` 按当前AI上游走海外AI，普通GitHub走总代理；`google.com` 由通用海外集走总代理，`microsoft.com` 仍走Microsoft。原系统通知、更新与特定登录直连例外保持更高优先级。

## 更新与检查

电脑每日12点检查上游、隔离验证，有实际变化才提交并推送。客户端 `海外AI` 规则集每24小时尝试下载；新增provider或顺序变化仍需刷新主配置，见 [更新教程](UPDATES.md)。

```sh
python tools/community_rules.py
python tools/build_ads.py
```

以上验证来源哈希、完整集合合并与生成一致性；不访问真实AI账号。出现地区限制或登录循环时，核对实际选中节点和连接记录中的命中策略。反馈域名、策略与错误文字即可，不发送聊天、Cookie、令牌或完整请求URL。手机逐服务登录及解锁效果仍待验收。
