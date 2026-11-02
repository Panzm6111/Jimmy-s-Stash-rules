# 淘宝、小红书、微博与天猫：当前专项范围

当前配置与脚本修订 **AD-20261020.5**，在原入口补齐fmz200部分广告分支，具体新增、未采用内容及来源见[接入明细](FMZ-INTEGRATION.md)。`.4`已有部分手机脚本执行记录，但没有开屏效果通过记录；`.5`尚待手机验收。静态检查和模拟结构不能代替实际广告效果。

| App | 当前已实现范围 | 仍未证明覆盖 |
|---|---|---|
| 淘宝 | 原专用splash响应中的展示字段/素材URL；新增带明确tao_splash场景的noah.query空JSON及advertisementservice.getadv广告接口 | 通用cloudvideo视频无法单凭接口名区分商品视频，poplayer可能是正常活动/领券，未整域/整接口封禁 |
| 微博 | 实时/预载开屏原生空JSON；4个专用SDK/素材主机；话题/搜索、热搜和评论的明确广告标记（4个精确API主机） | 首页friends_timeline全部信息流、国际版、所有备用链路 |
| 小红书 | 原开屏时间；启动配置splash；4个广告素材主机；edith/rec/www的v6首页非空ads_info赞助项、www的ads/resource | 其他版本/私有结构；不改下载、水印、画质、用户信息，不删除普通带货/直播笔记 |
| 美团 | 原外卖loadInfo已知字段；v7 openscreen/startpicture；限定开屏GIF/JPG素材及同目录MP4空正文 | 美团主App所有启动链；不把MP4返回成空GIF，不拦正常领券/商品素材 |
| 京东 | 唯一查询functionId=start；二维/平铺已知广告展示控制与有效日期 | 只在POST正文或加密结构里的新接口/函数；保留原倒计时、订单和券 |
| 独立天猫 | 仍只有通用域名规则，未虚构专项 | 淘宝内共用接口不能代表独立天猫App已经适配 |

用户已有可信自建CA可沿用，保持HTTP/MITM开启。推荐主入口已整合上述专项、扩展域名包和响应JS；刷新原config/stash.yaml即可取得当前配置，无需添加App覆写或expanded。停用已有额外同款覆写及旧整合广告增强以免重复。用户已取消逐App独立开关要求，现有专项随整合主配置共同启用。关闭额外同名覆写不能撤销内置处理；广告组DIRECT只控制域名拦截，HTTP处理需通过HTTP/MITM设置暂停。

以下原三款地址仅为维护源文件及旧安装兼容地址，便于核查来源；日常使用不要另行导入：

```text
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/taobao.stoverride
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/xiaohongshu.stoverride
https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/modules/ads/weibo.stoverride
```

整合模式刷新原主配置会更新精确主机、handler及JS来源地址，脚本正文由Stash按URL联网取得。主配置建议每周手动刷新一次，发布修复后立即刷新；JS、广告规则集与机场节点分别保留24小时自动尝试刷新。纯JS修复可刷新脚本资源取得，新增主机或handler仍须更新主配置，详见[更新教程](UPDATES.md)。MITM解密的是列出整个主机，即使脚本只匹配广告路径也须理解这个范围。不解密全域或银行支付，不安装他人CA、不关闭TLS验证。

预加载素材可保存在App私有目录，没有新请求也可能出现广告。先做多次冷启动、后台返回和使用后再启动的对照，优先App自带清缓存，网络规则不会删除本地文件。临时无敏感诊断、失败状态和最小反馈步骤见[去广告教程](ADBLOCKING.md)。自动签到继续暂停。
