# 淘宝、小红书、微博与天猫：专项开屏范围

更新日期：2026-10-19。以下区分“已写入代码”和“真实手机效果”；没有在用户 iPhone 上测试，不能承诺所有 App 版本都生效。自动签到仍暂停。

本页保留前轮淘宝/小红书/微博及独立天猫的详细边界。图片新提取的135款见[完整调查](APP-INVENTORY.md)，本轮新增35款的稳定链接与开关见[模块目录](AD-MODULES.md)。

## 当前交付

| 软件 | 专项状态 | 已做的处理 | 保留/限制 |
|---|---|---|---|
| 淘宝 | 已制作可选 `taobao.stoverride` + 本地响应脚本 | 只匹配 `guide-acs.m.taobao.com/gw/mtop.taobao.wireless.home.splash.awesome.get`。只修改 `splash_home_base` 中明确命名 `taobao-splash` 的广告条目：显示次数、等待、冷热启动、展示时间，以及其中图片/视频素材字段 | 保留 MTOP 成功/错误信息、普通首页区块和其他字段。不拦整个网关、整个首页、通用 cloudvideo 视频接口或 poplayer 活动弹层，避免误伤商品视频和正常领券。JSONP、未知复杂字段类型或失败结果不改；已知广告控制字段支持数字/布尔值并补齐缺省值 |
| 小红书 | 已制作可选 `xiaohongshu.stoverride` + 本地响应脚本 | 只匹配 `edith.xiaohongshu.com/api/sns/v*/system_service/splash_config`，调整 `ads_groups` 及其广告项中已知的展示起止时间 | 保留普通系统配置、笔记、搜索、消息、下载权限、水印及账号信息；不带入原脚本的正文日志、无水印保存或画质修改 |
| 微博 | 已制作可选 `weibo.stoverride` + 本地请求脚本（兼容旧响应式配置） | 普通微博的两个专用开屏 JSON 接口：`bootrealtime.uve.weibo.com/v*/ad/realtime`、`bootpreload.uve.weibo.com/v*/ad/preload`，新模块在请求阶段直接返回空JSON；旧响应式配置也可用新脚本，但需更新模块才会停止等待服务器响应 | 不挂接通用 api.weibo 域名，不改时间线、消息、登录、签到或会员；不复制其远程整包净化脚本。不声称已覆盖微博国际版或所有备用开屏接口 |
| 独立天猫 App | **尚未实现专项** | 仍只有原通用广告域名层覆盖 | 已检查来源中的淘宝接口、天猫精灵/养车规则、天猫营销域名，都不能证明独立天猫购物 App 的开屏链路。不能把淘宝适配直接标成天猫完成；淘宝内的天猫入口如恰好共用已匹配接口，只按实际请求处理，不据此声称独立 App 支持 |

开屏图片/视频可能已经缓存到 App 私有目录；Stash 响应脚本只能处理后续命中的网络响应，不能删除该目录或保证立刻清除旧广告。网络协议、证书固定、App 版本和接口变化都可能影响效果。不能以此为由关闭 TLS 验证或扩大到全域名解密。

## 资源、许可与适配方式

来源：[`fmz200/wool_scripts`](https://github.com/fmz200/wool_scripts)，锁定 `5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97`，仓库 GPL-3.0。完整许可在 [licenses/fmz200-GPL-3.0.txt](../licenses/fmz200-GPL-3.0.txt)，每个派生模块/脚本保留 SPDX 标识和来源。

实际阅读：

- `Scripts/xiaohongshu/xiaohongshu.js`：文件标注 2026-06-05；提取 splash_config 分支，移除其他功能。
- `Scripts/myBlockAds.js`：文件头 2024-10-15；提取淘宝专用 splash 分支，没有引入其他 App 或通用视频/活动弹层分支。
- `QuantumultX/rewrite/rewrite.snippet`：核对淘宝和小红书匹配端点；没有整包导入其规则。
- `QuantumultX/rewrite/weibo.snippet`：文件标注 2025-12-16，注明整合来源；仅取两个独立开屏路径及空 JSON 处理方式，没有复制其引用的其他作者远程脚本。
- 上游 `Stash/readme.md` 只有借助转换工具的说明，**不是现成 Stash 模块**。本项目手工制作原生 `http.script`、`script-providers`、精确 `http.mitm`，不用第三方转换网站，也不把 QX 配置直接塞进 Stash。

来源日期与仓库存续均不代表当前 App 实测有效。完整路径、源/本地内容 SHA256、许可与适配说明在 [sources.lock.json](../research/sources.lock.json)。另检查的 RuCu6/QuanX 当前地址为404；其他未发现明确许可证的整包脚本没有复制。

## 安装与关闭

公共文件进入 main 后，按 README 的覆写导入方法，逐个添加自己需要的模块：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/taobao.stoverride
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xiaohongshu.stoverride
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/weibo.stoverride
```

这些模块默认不导入、不开启。需要 MITM，新增精确域名为：

- 淘宝：`guide-acs.m.taobao.com`
- 小红书：`edith.xiaohongshu.com`
- 微博：`bootrealtime.uve.weibo.com`、`bootpreload.uve.weibo.com`

响应修改仅匹配表内路径；**CA 解密能力的范围仍然是整个指定域名**。尤其淘宝/小红书主机可能还承载登录数据等普通请求；本地脚本不会输出、保存或上传它们，但你仍需自己接受这层解密范围。不能接受时不启用该模块。不要添加 `*.taobao.com`、`*.weibo.com` 或银行支付主域。

证书仅在设备生成和信任；已有本人生成且可信的 Stash CA 可沿用，不需要把证书/私钥交给别人。启用后先检查脚本下载、最终合并预览中的 handler 和精确域名，再验证目标 App 的开屏与正常业务。

关闭对应覆写即可撤销其响应修改；“广告拦截→DIRECT”只关闭域名拦截，不关闭这些脚本。发现正常功能异常时先关该模块并重建连接，不通过放宽解密/关闭 TLS 来解决。

## 验证结果的含义

模拟测试覆盖：只改开屏字段、保留其他字段、MTOP失败与登录过期不改、支付/领券/正常视频不匹配、伪装域名不匹配、淘宝/小红书未知或超大响应放行、重复执行不继续变动、只有固定无敏感诊断，无存储/外联、恰好完成一次。所有可选模块组合做结构合并检查。

这些验证不能替代 Stash 原生导入、真实 TLS/MITM、真实响应或广告展示效果。独立天猫专项不在已实现列表；后续需独立版本的明确开屏路径和数据结构证据，不需要用户提交 Cookie、完整抓包或登录信息。
