# 图片 App 名称与逐款去广告调查

核对日期：2026-10-20（北京时间）。共 **135 个可见名称**；其中 **39 款有专项实现并已纳入整合入口**，8款找到方案但暂缓，其余88款保留通用规则。这里记录实现范围，实际去广告效果仍待设备验收。

对1320×26408长图分12段人工核对可见名称；不保留/发布原截图；不根据名称推断账号持有情况。

“隐藏的 App”是系统入口，未推测其中内容。点点、Fantopia、换机助手、鼾声分析器、钱迹、遥控器等名称不足以唯一定位开发者，未强行套用近似名称规则。

## 调查依据与边界

没有方案只表示本次有限来源未找到可审核实现，不证明整个互联网没有。用户曾反馈旧版去广告整体效果不足；当前整合版尚未提供逐款接口命中或修改结果，所以不能把某个模块直接记为有效或断定某端点已经失效。域名路由不能识别全部App流量，静态测试不能替代手机效果和正常功能验收。

调查时已直接读取固定版本的公开源码、模块与许可，并核对主要仓库HEAD；不是只读项目介绍。本次表述整理没有重新调查接口或扩大实现范围。原检索范围：

- fmz200/wool_scripts@5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97 的730款合集标签及相关实际JS（宣称数量不视作有效性证据）
- blackmatrix7/ios_rule_script@7dd06b44f5093dd5404e1e5f3bca5452d97146ef 原生Stash重写和启动脚本
- app2smile/rules@df6366a7024e0b3f0aa3510c5b791eea6f3cba89 的原生模块与JS
- Maasea/sgmodule@65075cdb388fc5e3094afd7e7314c67b243f3525 的YouTube实际脚本、模块、许可及WeRead模块
- NobyDa/Script@0b8d083d444f4476700cb9d5d059c07b42da85eb 的微信公众号脚本与GPL-3.0许可

来源与文件哈希见 [ad-catalog.json](../research/ad-catalog.json) 和 [sources.lock.json](../research/sources.lock.json)。源文件2024/2025年的日期不因仓库2026年仍有提交就变成已验证有效。原生Stash格式参考能支持实现选择，仍不替代当前官方文档和手机实测。

## 完整清单

“通用”指域名规则可能拦第三方广告SDK，不表示已确认这个App使用该SDK；没有专项的条目也经过逐款名称检索和范围判断。下表不记录账号、版本、凭据或截图。

| 序号 | 图片名称 | 实现来源 / 状态 | 范围、依据或暂缓原因 |
|---|---|---|---|
| 1 | 阿里云盘 | [alipan](../modules/ads/alipan.stoverride) | 仅 onboard_list 的4种推广banner；不宣称阿里云盘开屏或全界面去广告；这是推广横幅处理，不是完整开屏控制；保留备份、功能入口、新闻、签到和权益。不应把四种横幅候选扩大成整App有效覆盖。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/Scripts/adrive/adrive.js)，GPL-3.0-only。 |
| 2 | App Store | 保留通用规则；未加专项 | 商店推广与正常App检索/产品展示共用服务；没有采用可保留正常商店功能的精确广告方案。 |
| 3 | Apple Store | 保留通用规则；未加专项 | 这是Apple硬件商店，不能套用App Store、淘宝或普通广告SDK规则；没有采用独立专项。 |
| 4 | Authenticator | 保留通用规则；未加专项 | 按图标可辨认为Google风格验证器；未发现已审核的独立广告端点，不解密验证与账号通信。 |
| 5 | 百度网盘 | [baidu-netdisk](../modules/ads/baidu-netdisk.stoverride) | 网盘独立 ad/adx 广告接口；不拦福利、会员、下载、分享；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 6 | 备忘录 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 7 | 哔哩哔哩 | [bilibili](../modules/ads/bilibili.stoverride) | 仅 JSON 开屏与推荐流广告；不处理会员权限、视频贴片或领券。已纳入整合入口，需设备验收；原源代码含2023年的JSON路径/结构；上游仓库有新提交不证明这些端点在当前iOS版本仍使用。现有文件保留候选，不能据此宣称B站全广告有效去除。 来源与许可见[既有专项说明](APP-SPLASH.md)及[来源记录](SOURCES.md)。 |
| 8 | 播客 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 9 | 菜鸟 | [cainiao](../modules/ads/cainiao.stoverride) | 仅 ads.show 的明确 adItemDetail 广告项；不包含 mshow 或完整首页净化；上游同时处理 ads.show 与 mshow，且删除部分券、裹酱积分、寄件和消息入口；本模块不采用这些业务删改，不能据此称菜鸟全广告已覆盖。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/Scripts/cainiao/cainiao.js)，GPL-3.0-only。 |
| 10 | 测距仪 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 11 | 查找 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 12 | ChatGPT | 保留通用规则；未加专项 | 已有海外AI分流（含OpenAI）；所检索资源没有可审核的当前App广告专项，不把分流当去广告。 |
| 13 | Chrome | 保留通用规则；未加专项 | 网页广告使用通用域名规则；Stash不提供浏览器CSS元素隐藏，不能保证同域广告或空白被移除。 |
| 14 | 大麦 | [damai](../modules/ads/damai.stoverride) | 专用 home.welcome 开屏；不屏蔽 HTTPDNS、票务或下单；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 15 | 大众点评 | [dianping](../modules/ads/dianping.stoverride) | 仅 loadsplashconfig 开屏配置；不删普通首页、优惠或评价；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 16 | 地图 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 17 | 滴滴 | 找到方案但暂缓采用 | 公开 didiAds.js 会删除安全中心/服务入口；部分合集端点与当前脚本分支不匹配，未作为可靠去广告实现接入。 [公开合集对应段落](https://github.com/fmz200/wool_scripts/blob/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet#L1349)（GPL-3.0）。 |
| 18 | 点点 | 保留通用规则；未加专项 | 名称与图标不足以唯一确定开发者；没有把“罗森点点”或“一点点”小程序规则冒充该App规则。 |
| 19 | 电话 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 20 | 东方财富 | [eastmoney](../modules/ads/eastmoney.stoverride) | 仅 emdcadvertise 独立广告主机；不代表行情页面全部推广；独立广告请求可按域名拦截；没有当前App请求与开屏效果的设备证据，不解密行情、交易或登录。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 21 | 抖音 | 保留通用规则；未加专项 | 检索到的规则只屏蔽 bds.snssdk.com、p3.pstatp.com 等共享主机；不采用图片CDN泛拦，未实现可确认的开屏/视频流专项。 [公开合集对应段落](https://github.com/fmz200/wool_scripts/blob/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet#L1513)（GPL-3.0）。 |
| 22 | 豆包 | 保留通用规则；未加专项 | 未审核到可识别独立广告且不影响会话/语音的公开方案。 |
| 23 | 翻译 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 24 | 放大器 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 25 | FaceTime通话 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 26 | Fantopia | 保留通用规则；未加专项 | 未在本次公开资源中找到可审核的同名App广告专项；身份与广告端点均需进一步证据。 |
| 27 | 高德地图 | [amap](../modules/ads/amap.stoverride) | 两个独立启动广告接口及 optimus 广告域名；保留路线、定位和普通地图图片；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 28 | 个人所得税 | 保留通用规则；未加专项 | 当前审核源没有发现同名、范围清晰的广告专项；不据此断言App没有广告。 |
| 29 | 股市 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 30 | Gmail | 保留通用规则；未加专项 | 邮件推广与邮箱内容在同一业务内，未审核到安全的独立Stash响应过滤方案，不解密邮箱。 |
| 31 | Google 翻译 | 保留通用规则；未加专项 | 检索源没有独立广告方案；保留翻译、语音和账号功能，不套用Google广告域名作为专项成功证据。 |
| 32 | Google Maps | 保留通用规则；未加专项 | 地点推广与地图/搜索内容可能混合；未审核到可保留导航和商家信息的精确方案。 |
| 33 | 鼾声分析器 | 保留通用规则；未加专项 | 同类睡眠App不能仅凭类型共用规则；未找到同名且范围明确的方案。 |
| 34 | 航旅纵横 | [umetrip](../modules/ads/umetrip.stoverride) | 仅 fs/advert/polite 广告素材候选；不包含开屏展示控制或航班业务；素材请求失败仍可能出现缓存、空白或倒计时。上游 gateway 脚本依赖请求头且规则/运行类型有疑点，未采用；不能据此承诺航旅纵横完整开屏去除。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 35 | 盒马 | 找到方案但暂缓采用 | 找到的方案会阻断整页渲染、推荐及购买后活动，外链脚本还需单独核实许可；为保留购物与正常权益暂缓。 [公开合集对应段落](https://github.com/fmz200/wool_scripts/blob/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet#L2097)（GPL-3.0）。 |
| 36 | 华住会 | [huazhu](../modules/ads/huazhu.stoverride) | 仅 getAppStartPage 开屏；保留酒店优惠、新客权益、更新和预订；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 37 | 换机助手 | 保留通用规则；未加专项 | 同名产品较多；不将跨品牌换机工具的传输或备份接口当广告阻断。 |
| 38 | iMovie剪辑 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 39 | Instagram | 保留通用规则；未加专项 | 未审核到当前iOS版可安全识别广告、保留正文/短视频的Stash方案；不能用Meta整域拦截替代。 |
| 40 | 计算器 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 41 | 健康 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 42 | 健身 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 43 | 交管12123 | 保留通用规则；未加专项 | 发现公开的 gab.122.gov.cn/eapp/m/sysquery/adver；本轮不加入政务业务主域名解密，SDK广告仅可能被通用规则覆盖。 [公开合集对应段落](https://github.com/fmz200/wool_scripts/blob/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet#L41)（GPL-3.0）。 |
| 44 | 京东 | [jingdong](../modules/ads/jingdong.stoverride) | 仅 URL 中 functionId=start 的历史开屏展示字段；不包含全部京东广告；AD-20261020.1按固定来源补充部分处理链，完整边界见AD-ARCHITECTURE第3部分；尚无真实iPhone效果验收。 来源：[blackmatrix7/ios_rule_script](https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/7dd06b44f5093dd5404e1e5f3bca5452d97146ef/script/startup/startup.js)，GPL-2.0。 |
| 45 | 京东金融 | [jingdong-finance](../modules/ads/jingdong-finance.stoverride) | 仅 bdsp-x/dsp-x 广告主机候选；不包含金融网关或完整开屏；上游证据只匹配这两个主机的 /adx/ 路径，本模块提升为整主机拦截，范围更大且需要排除误杀。不解密金融、登录或支付，不屏蔽普通图片或邮箱。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 46 | 肯德基 | [kfc](../modules/ads/kfc.stoverride) | 仅 advertisement 路径广告素材候选；不包含完整开屏控制、菜单或优惠券；修正上游域名拼写；不拦整个 apphome5/6，因为可能混有正常活动。素材拒绝不等于取消展示，仍可能等待、读缓存或出现空白；当前完整开屏没有已验证方案。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 47 | 库乐队 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 48 | 夸克 | 找到方案但暂缓采用 | 公开 quark.js 存在，但实际代码经过jsjiami混淆；没有运行或导入这份不可直接审计的脚本。 [公开合集对应段落](https://github.com/fmz200/wool_scripts/blob/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet#L2666)（GPL-3.0）。 |
| 49 | 快捷指令 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 50 | Keynote讲演 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 51 | 联系人 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 52 | 猎聘 | [liepin](../modules/ads/liepin.stoverride) | 明确命名的 live.get-ad-cards；不拦职位推荐或投递；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 53 | 麦当劳 | [mcdonalds](../modules/ads/mcdonalds.stoverride) | 专用 portal/home/splash；保留点餐、支付、领券；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 54 | 脉脉 | [maimai](../modules/ads/maimai.stoverride) | 仅 adshow；保留礼物、消息和普通推荐；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 55 | 每日英语听力 | 保留通用规则；未加专项 | 本次资源未找到同名、可审计且明确去广告的App方案；不混同欧路词典或会员解锁。 |
| 56 | 美团 | [meituan](../modules/ads/meituan.stoverride) | 外卖loadInfo已知startpicture广告数组；v7 openscreen/startpicture专用接口与限定开屏图片素材；不是主App完整覆盖；AD-20261020.1按固定来源补充部分处理链，完整边界见AD-ARCHITECTURE第3部分；尚无真实iPhone效果验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 57 | 米家 | [mijia](../modules/ads/mijia.stoverride) | 仅 openingBanner 两个端点；保留设备控制、普通推荐和自动化；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 58 | 密码 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 59 | 墨墨背单词 | 保留通用规则；未加专项 | 本次资源未找到可保留学习/词量真实权限的可靠广告专项，不改付费权限。 |
| 60 | Marshall | 保留通用规则；未加专项 | 耳机/音箱控制App未发现明确广告专项；不修改蓝牙、固件和设备配置。 |
| 61 | Notion | 保留通用规则；未加专项 | 未审核到独立广告规则；保留文档同步和账号，不把推荐或升级提示直接视为可拦广告。 |
| 62 | Numbers表格 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 63 | 欧路词典 | 保留通用规则；未加专项 | 未审核到可靠广告专项；不采用词库/会员权限解锁或屏蔽学习资源。 |
| 64 | 拼多多 | [pinduoduo](../modules/ads/pinduoduo.stoverride) | 仅 cappuccino/splash；保留首页、买菜、红包和领券；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 65 | Pages文稿 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 66 | Picsew | 保留通用规则；未加专项 | 未发现需要本项目拦截的独立广告端点；不修改购买状态或图片功能。 |
| 67 | 钱包 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 68 | 钱迹 | 保留通用规则；未加专项 | 同名和版本信息有限；未审核到独立广告专项，不解密账本同步。 |
| 69 | QQ | 保留通用规则；未加专项 | 普通消息、动态与广告接口可能混合，现有源未提供本轮可安全采用的精确方案；不拦整个QQ服务。 |
| 70 | 日历 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 71 | 瑞幸咖啡 | [luckin](../modules/ads/luckin.stoverride) | 仅 sys/app/adposNew 独立广告响应；保留点单、商品与优惠券；只在已成功 status=SUCCESS 的JSON上返回同源参考的空广告结果；不采用兑换页/商品弹窗过滤。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 72 | 时钟 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 73 | 手记 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 74 | Safari浏览器 | 保留通用规则；未加专项 | 网页广告使用通用域名规则；本项目不安装额外内容拦截器，不声称有CSS元素隐藏。 |
| 75 | Scriptable | 保留通用规则；未加专项 | 通用脚本工具自身不等于已启用某个广告脚本；不添加无明确目标的过滤。 |
| 76 | Shadowrocket | 保留通用规则；未加专项 | 仅识别出安装名称；本项目客户端仍只使用Stash，不导入或迁移到其他客户端。 |
| 77 | Sky Guide | 保留通用规则；未加专项 | 未在本次资源中找到明确广告专项，不将付费订阅提示当免费权益接口。 |
| 78 | SnapBridge | 保留通用规则；未加专项 | 相机连接工具未发现明确广告专项；不修改传图、蓝牙或固件服务。 |
| 79 | Speedtest | 保留通用规则；未加专项 | 未在审核源中找到可确定属于当前iOS版的独立广告端点；通用第三方SDK域名可能覆盖部分广告，不能保证全部。 |
| 80 | Spotify | 找到方案但暂缓采用 | 发现MIT公开原生模块，但源码修改Premium产品字段和多项权限；没有直接采用。单独阻断广告还需确认播放队列不会卡住。 [公开合集对应段落](https://github.com/fmz200/wool_scripts/blob/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet#L4348)（GPL-3.0）。 |
| 81 | Starbucks | 找到方案但暂缓采用 | 找到的是微信小程序UI精简，不是图中独立Starbucks App的可靠开屏方案；未套用。 |
| 82 | Stash | 保留通用规则；未加专项 | 代理工具本身无需加入无明确目标的广告过滤；保留更新、规则与证书管理。 |
| 83 | Steam | 保留通用规则；未加专项 | 商店促销/游戏内容与正常业务共用服务；未实现不影响购买和库同步的精确广告方案。 |
| 84 | 淘宝 | [taobao](../modules/ads/taobao.stoverride) | AD-20261020.1；专用开屏展示控制、明确tao_splash场景；通用视频/活动弹层未泛化屏蔽。待真机验收；AD-20261020.1按固定来源补充部分处理链，完整边界见AD-ARCHITECTURE第3部分；尚无真实iPhone效果验收。 来源与许可见[既有专项说明](APP-SPLASH.md)及[来源记录](SOURCES.md)。 |
| 85 | 淘票票 | [taopiaopiao](../modules/ads/taopiaopiao.stoverride) | 仅 queryloadingbanner 启动广告；保留普通活动、选座和购票；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 86 | 腾讯会议 | 保留通用规则；未加专项 | 本次公开资源未找到可审核的独立广告专项，保留入会、音视频与通知。 |
| 87 | 提示 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 88 | 提醒事项 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 89 | 体育 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 90 | 天气 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 91 | 铁路12306 | [railway12306](../modules/ads/railway12306.stoverride) | 仅 ad.12306.cn 独立广告主机；不保证取消客户端缓存开屏；只使用公开广告端点的主机事实，未复制外链脚本，不解密车票、身份信息或支付。广告请求被阻断后客户端是否读缓存或等待仍需设备确认。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 92 | 图书 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 93 | Telegram | 保留通用规则；未加专项 | 已有Telegram分流；原生频道赞助信息不能靠封禁整个消息服务处理，未审核到本轮可采用的Stash专项。 |
| 94 | TestFlight | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 95 | UC浏览器 | [uc](../modules/ads/uc.stoverride) | 仅 ads.uc.cn、adslot.uc.cn 独立广告主机；不包含网页同域广告；只拦独立广告请求，不提供网页元素隐藏，也不能清除与正文同域的广告；保留反诈、安全、语音和网页正文。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 96 | 王者荣耀 | 保留通用规则；未加专项 | 游戏活动、资源与公告共用接口；没有采用可能影响登录、更新和对局的泛拦。 |
| 97 | 网易邮箱大师 | [netease-mail](../modules/ads/netease-mail.stoverride) | mmad 素材和 searchMultiAds/showAds；保留邮件、搜索和同步；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 98 | 网易云音乐 | [netease-music](../modules/ads/netease-music.stoverride) | 仅3个精确主机的 api/ad 或 eapi/ad 路径候选；不解密 EAPI 正文；上游匹配 interface 加可选数字，本模块只列 interface、interface3、ipv4，其他编号主机不在范围。EAPI 加密正文不能假定接受空JSON；端点、响应语义和开屏效果均待设备确认。不改音乐权限、云贝或会员真实状态。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 99 | 微博 | [weibo](../modules/ads/weibo.stoverride) | AD-20261020.1；实时/预载空JSON、专用SDK与素材主机、话题/搜索明确广告项；不是首页全部信息流覆盖。待真机验收；AD-20261020.1按固定来源补充部分处理链，完整边界见AD-ARCHITECTURE第3部分；尚无真实iPhone效果验收。 来源与许可见[既有专项说明](APP-SPLASH.md)及[来源记录](SOURCES.md)。 |
| 100 | 微信 | [wechat-articles](../modules/ads/wechat-articles.stoverride) | 仅历史公众号 getappmsgad 的广告字段；不包含朋友圈、视频号或聊天；公开源仍保留这个历史端点，但没有当前微信版本调用证据；只能作为公众号候选，不称微信整体去广告。保留原 appid 与其他文章字段。 来源：[NobyDa/Script](https://raw.githubusercontent.com/NobyDa/Script/0b8d083d444f4476700cb9d5d059c07b42da85eb/QuantumultX/File/Wechat.js)，GPL-3.0-only。 |
| 101 | 微信读书 | 找到方案但暂缓采用 | Maasea WeRead模块删除评论/分享数字和阅读提示，属于UI精简，不是已确认广告过滤；不移除这些正常功能。 |
| 102 | 微信输入法 | 保留通用规则；未加专项 | 输入法主功能与广告证据不同，未找到可审核的独立广告规则；不解密输入/账号通信。 |
| 103 | 维基百科 | 保留通用规则；未加专项 | 未在本次资源中找到App广告专项；不将募捐提示或文章内容改写为广告。 |
| 104 | 文件 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 105 | 我的南京 | 保留通用规则；未加专项 | 未找到可靠的同名App广告专项；不解密政务/身份信息主域名，不套用其他城市政务App规则。 |
| 106 | 无边记 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 107 | Webex | 保留通用规则；未加专项 | 未发现可审核的独立广告方案；保留会议、通话和账号。 |
| 108 | WPS Office | [wps](../modules/ads/wps.stoverride) | 仅广告统计请求与 feeds_ad 素材；没有完整开屏或文档内广告去除证据；ad-statistics-service 拦截主要影响统计，不能证明界面广告消失；素材拒绝仍可能留下空白或等待。不处理会员、文档和云同步，当前覆盖不等于 WPS 整体去广告。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 109 | 下厨房 | [xiachufang](../modules/ads/xiachufang.stoverride) | 仅 vN/ad/ 专用广告路径；保留菜谱、购物和内容图片；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 110 | 闲鱼 | [xianyu](../modules/ads/xianyu.stoverride) | 仅 idlecommerce.splash.ads；保留聊天、交易、闲鱼币和搜索；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 111 | 小红书 | [xiaohongshu](../modules/ads/xiaohongshu.stoverride) | AD-20261020.1；开屏时间、启动配置splash、专用广告素材、v6首页明确赞助项；不改下载/水印/画质/用户信息。待真机验收；AD-20261020.1按固定来源补充部分处理链，完整边界见AD-ARCHITECTURE第3部分；尚无真实iPhone效果验收。 来源与许可见[既有专项说明](APP-SPLASH.md)及[来源记录](SOURCES.md)。 |
| 112 | 小米耳机 | 保留通用规则；未加专项 | 不能用米家/小爱音箱的规则代替耳机App专项；未发现同名可靠广告端点。 |
| 113 | 小米互联服务 | 保留通用规则；未加专项 | 跨设备互联与广告服务不是一回事；未采用可能干扰连接的泛拦。 |
| 114 | 小宇宙 | [xiaoyuzhou](../modules/ads/xiaoyuzhou.stoverride) | 仅 flash 开屏；保留节目推荐、AI总结、搜索和播客音频；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 115 | 携程旅行 | [ctrip](../modules/ads/ctrip.stoverride) | 仅 ma-adx 主机的广告/统计请求；没有完整开屏去除证据；上游证据仅 _ma.gif 端点，拦截可能主要减少统计，不能据此判断可见广告消失；将路径扩为主机需设备排除误杀。未采用 tripAds，因为上游明确警告8.47.0以上版本部分图片可能无法加载；不解密预订或支付。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 116 | 信息 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 117 | 遥控器 | 保留通用规则；未加专项 | 名称不能唯一确定开发者/版本；没有为未知设备控制接口添加拦截。 |
| 118 | 音乐 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 119 | 邮件 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 120 | 游戏 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 121 | 语音备忘录 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 122 | 预览 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 123 | 云闪付 | [unionpay](../modules/ads/unionpay.stoverride) | 仅 ads.95516.com 和 ads.cup.com.cn 广告请求；不代表云闪付全界面去广告；两个独立广告主机与扩展包重叠；基础模式可单独启用。保留推送和安全SDK，不解密支付；缓存和其他同域业务推广不在已知覆盖范围。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 124 | YouTube | 找到方案但暂缓采用 | 发现Apache-2.0的Maasea源码；涉及Protobuf、请求/响应配套与动态googlevideo主机，原模块基于Surge。尚未完成广告专用裁剪、Stash二进制适配和播放回归，不直接套用；不是断言无法适配。 [公开合集对应段落](https://github.com/fmz200/wool_scripts/blob/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet#L6462)（GPL-3.0）。 |
| 125 | YouTube Music | 找到方案但暂缓采用 | Maasea声明兼容Music，但二进制适配、广告与后台播放功能裁剪尚未完成；不把YouTube域名分流当作Music去广告。 |
| 126 | 照片 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 127 | 支付宝 | 保留通用规则；未加专项 | 未采用可审核且只处理广告的独立方案；不解密支付网关，不封禁安全、风控或正常领券服务。 |
| 128 | 知乎 | [zhihu](../modules/ads/zhihu.stoverride) | 仅开屏、顶部横幅与 ad-style-service 候选；不包含全部回答和信息流广告；上游其他脚本还处理回答与推荐流，但未整体引入。本模块只匹配明确广告端点，不把有限路径等同于知乎全界面去广告；普通回答、搜索与推荐保留。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 129 | 指南针 | 保留通用规则；未加专项 | 按截图名称/图标识别为Apple系统或配套App；当前审核源没有明确独立广告方案，保留核心功能。系统商店推广、股市赞助等同域内容不作已去除承诺。 |
| 130 | 智联招聘 | 保留通用规则；未加专项 | 本次资源未找到明确同名、许可与端点均可靠的广告专项；不套用猎聘规则。 |
| 131 | 中国建设银行 | 保留通用规则；未加专项 | 本次资源未找到不触碰银行业务的可靠广告方案；不解密银行主域名。 |
| 132 | 中国联通 | [unicom](../modules/ads/unicom.stoverride) | 专用启动/广告接口；保留 accountListData、客户端配置和缴费；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 133 | 中国移动 | [cmcc](../modules/ads/cmcc.stoverride) | 仅 explorePage/getAdverList 候选广告接口；没有完整启动广告去除证据；上游 startInit 是混合业务启动接口，不能整体阻断来换取开屏消失；本模块只保留窄广告端点，不包含全部开屏，不碰账号、缴费与权益。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |
| 134 | 中国银行 | 保留通用规则；未加专项 | 搜到“缤纷生活”规则，但与图中“中国银行”不是同一个App；不套用、不解密银行业务。 |
| 135 | 58同城 | [58tongcheng](../modules/ads/58tongcheng.stoverride) | 仅 home/advertising 和 appadv；保留职位、联系与发布；已将广告范围明确的部分纳入整合入口，无需单独导入；实际接口、缓存、证书与正常功能仍需设备验收。 来源：[fmz200/wool_scripts](https://raw.githubusercontent.com/fmz200/wool_scripts/5d5f63fcf98bc69d5f8f1b1bae6f86a01ee4bb97/QuantumultX/rewrite/rewrite.snippet)，GPL-3.0-only。 |

## 如何使用这些结果

不用继续从零报一遍名称。已有这份清单，后续沿用原模块路径更新；如有漏广告，只需说明App名、广告位置、App版本和现象。不要发送抓包、登录信息或带私人参数的完整URL。

日常只使用原[公共订阅入口](SUBSCRIBE.md)，已整合所有已有专项，无需逐个导入；逐App开关已从当前需求中移除。[实现目录](AD-MODULES.md)用于查范围和来源，不是额外安装步骤。仅已审阅的精确主机进入MITM，不是把135款App都进行MITM。自动签到继续暂停。
