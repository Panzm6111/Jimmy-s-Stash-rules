# Clash Verge 使用方法

适用 Clash Verge Rev（Mihomo 内核）。保留 Stash 全部有序分流、软件策略、地区池、AI规则和手动选择；广告部分只使用现有域名规则集。HTTPS MITM、43条URL改写、11份响应JS及手动自检仍只供Stash使用。域名拦截无法处理与正常内容共用域名的广告，不保证开屏或视频内广告消失。

## 推荐：在原机场订阅上使用扩展脚本

1. 先在 Clash Verge 的“订阅”中正常导入你的机场 Clash/Mihomo 订阅，确认有节点。订阅地址保留在本机。
2. 打开本项目 [config/clash-verge.js](../config/clash-verge.js)，复制全部内容。
3. 右键这份机场订阅卡片，选择“编辑扩展脚本/编辑脚本”，粘贴并保存，然后重新激活该订阅。不同版本名称略有区别；这是对配置做转换的脚本，不处理网络响应。
4. 使用“规则”模式。进入“代理”，将“总代理”从初始REJECT改成你需要的地区或“自动节点”。新增统一“TikTok”组接管TikTok、Instagram和X，默认美国；“海外AI”保留美国默认值，另可选“日本”“日本+美国”或单独节点。
5. “日本+美国”仅从这两个国家的节点中每1800秒测速选择；它不把两跳串联。空组及全失效时的实际连接仍需用户验证。
6. 域名广告规则集“基础广告”按24小时尝试刷新。机场节点仍从原订阅更新；更新本项目的策略/规则正文时，重新复制新扩展脚本并激活。脚本没有网络/文件IO，不会偷偷自更新。

脚本保持机场所有节点参数和原代理集，使用原代理集及内嵌节点构建本项目策略组，替换机场原来的策略与分流。原订阅其余设置按生成配置合并。主配置和脚本共用生成器，完整路由顺序相同，不额外叠加一套只含广告的简化分流。原“广告拦截”组仍可REJECT/DIRECT切换。

如提示节点名称与本项目策略组重名，先在机场订阅端或本机调整冲突名称；程序会停止，不静默遗漏节点。其他已启用的全局/订阅扩展可能覆盖规则；先备份并检查最终生效配置，避免两套规则扩展同时改写。

## 另一个入口：完整公共配置

[config/clash-verge.yaml](../config/clash-verge.yaml) 是可重复生成的完整Mihomo模板；稳定链接：

https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/config/clash-verge.yaml

它的机场URL是不可用占位符。仅导入公共链接不会产生节点。若使用这个入口，在这份配置的**本机扩展配置**设置：

```yaml
proxy-providers:
  机场:
    url: "在本机粘贴你自己的Clash格式机场订阅URL"
```

占位符必须换成真实URL；不要把修改后的扩展配置上传GitHub。通常推荐上面的“原机场订阅 + 扩展脚本”方法，不需要重复填写URL，也无需第三方转换站。

## 回退与验证

先保留原订阅备份。移除/停用本项目扩展脚本并重新激活原订阅即可恢复。HTTP层无需装证书。出现业务误伤，可先把“广告拦截”切为DIRECT，检查该连接命中的规则。

本项目核验了生成结果、完整路由与节点保留，并使用本机Mihomo做配置解析；不等同于你当前机场连通、AI账号解锁、广告效果或Clash界面操作已验收。最终验证日期和结果以 [PROGRESS](../PROGRESS.md) 为准。

依据：[Clash Verge扩展配置与脚本](https://www.clashverge.dev/guide/extend.html)、[自定义脚本](https://www.clashverge.dev/guide/script.html)、[Mihomo规则](https://wiki.metacubex.one/config/rules/)、[代理集](https://wiki.metacubex.one/config/proxy-providers/)。本文件由本项目生成器维护说明配合源码接续，第三方规则许可沿用 [SOURCES](SOURCES.md)。
