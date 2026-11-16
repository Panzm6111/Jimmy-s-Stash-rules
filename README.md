# Jimmy 的 Stash 与 Clash 规则

只发布当前这两份配置，沿用原订阅地址：

| 客户端 | 最新主订阅 |
|---|---|
| Stash | [config/stash.yaml](config/stash.yaml) |
| Clash Verge | [config/clash-verge-auto.yaml](config/clash-verge-auto.yaml) |

本页对应 ROUTE-20261116.2。AI组（最稳）按 HKG B/C/J、新加坡 A、台湾 B、日本 A、美国 B 的优先级故障回退；AI最速组收日本 A/B、HKG B/C/J；最优速组收日本 A/B、HKG B/A/C/I/J/M。Stash 精选池设 5 秒主动兜底探测、3 秒探测限时；Clash 保留电脑现有 60 秒节奏。海外AI/Claude 默认 AI组，其余代理业务默认总代理，国内与系统直连沿用。手机删除旧 GPT/TikTok 服务检测覆写，保留私人机场与 MitM，刷新原主配置即可；不再需要脚本控制端口/密钥。Stash 原生测速共享，统一以 ChatGPT 为目标；Clash 保留 AI 与通用目标独立检查。入口测速不能证明真实回复或 TikTok 播放可用。[故障恢复、覆写删除与日志指南](docs/ROUTING.md#iphone-service-health)。

Claude 网页版使用独立策略组，默认选 `AI组`。主站、账户验证和第一方资源都按这个组分流。[网页版设置与连接核对](docs/ROUTING.md#claude-web)

## 使用

Stash 导入原公共URL，并关联设备上的私人订阅覆写：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/stash.yaml
```

保留私人机场与证书，刷新“机场”后选择出口。Stash继续保留HTTP改写与广告脚本；具体步骤见[Stash导入](docs/SUBSCRIBE.md)。曾出现配置自动更新后暂时无节点的反馈，根因尚未确定，见[节点排查](docs/SUBSCRIPTION.md#更新后只有分组没有节点)。

Clash Verge 导入完整远程配置，开启1440分钟自动更新：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/clash-verge-auto.yaml
```

私人机场和启动后备仅留在设备的私人Merge；全局Merge不再粘贴Jimmy规则快照。规则、策略组和顺序随主订阅更新，机场节点也独立更新。Clash只使用基础域名去广告，见[Clash使用说明](docs/CLASH-VERGE.md)。

## 自动更新

Stash 26份、Clash 25份兼容规则直订维护中的上游，间隔24小时。6份必要转换由[GitHub Actions](.github/workflows/refresh-rules.yml)每天北京时间12:17计划执行，有实际变化且验证通过才提交。主配置更新和规则集更新是两层：修改策略组需要刷新主配置。电脑上的旧任务已移除，不需要开机维护，详情见[更新说明](docs/UPDATES.md)。

## 需求、沟通和维护源

- 统一主文档：[PROGRESS.md](PROGRESS.md)。Stash / Clash规则维护、调试结论、进度与历史共用这一份；确认需求、关键取舍、沟通和历史证据原文继续保留。
- 需求与实现规格：[AD-ARCHITECTURE](docs/AD-ARCHITECTURE.md)、[App范围](docs/APP-INVENTORY.md)、[分流](docs/ROUTING.md)、[AI覆盖](docs/AI-COVERAGE.md)。
- 来源、许可和验证证据：[SOURCES](docs/SOURCES.md)、[COMMUNITY-SOURCES](docs/COMMUNITY-SOURCES.md)、[research](research/)、[licenses](licenses/)。
- `templates/stash-main.yaml`、`templates/stash-core.stoverride`和`modules/`是生成最新版的维护源，不是另一套安装版本。`rules/`、`scripts/`是最新配置的依赖；`tools/`、`tests/`负责生成、转换和验证，不能只保留两个YAML而删除这些依赖。
- 旧Clash独立配置、全局Merge、扩展脚本及Windows定时发布工具已退役，不再生成或提供旧入口。本次按用户明确要求重建Git历史；原公开历史只在本机忽略目录保留恢复备份。

实际iPhone广告效果、服务地区限制和机场可用性需设备验证，规则数量或CI通过不代表这些已验收。私人URL、节点凭据和证书不进入公开仓库。自动签到继续暂停。
