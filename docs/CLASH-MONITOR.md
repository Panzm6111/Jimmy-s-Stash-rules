# Clash Verge 实际使用观察

此工具只在 Windows 本机读取正在使用的 Clash Verge / Mihomo 生产内核。默认连续观察5个自然日，电脑休眠或关机期间不记录，恢复后续记；没有数据的时间不能当作正常。它不改变分流、分组、节点选择、日志级别、DNS或内置健康检查频率，也不发起额外节点探测或带宽测试。安装使用本项目已有 Python 环境和 Windows 任务计划，不安装新的代理服务。

## 记录与判断

- 每5秒读取实际连接链，按分钟保存实际经过节点的连接样本、观察到的上下行字节及有连接的时间；持续观察`Jimmy · 海外AI`与`Jimmy · ai`的当前选择。不会保存其他未使用节点的全量健康历史。
- 订阅已有info日志流，记录成功建连数量和错误类别，不落盘原始日志、请求正文、完整网址、IP地址、进程路径、节点地址、订阅URL或认证信息。如果用户把日志级别降低到warning，成功建连记录可能缺失，报告仍可使用采样连接和错误。日志或轮询本身也可能漏记短连接、最后一段流量及极短切换，因此不是完整请求审计。
- 节点切换保存原/新路径和已读取的探测结果。成员消失、选择项变更属于已观测事实；原节点探测不可用、新节点延迟优势超过容差、附近连接错误只是推断或时间相关。API不能区分用户手动操作与其他程序操作，不把它们伪称确定原因。
- 读取`/proxies`时，Mihomo可能依据已有探测结果重新计算自动池当前选择。这是内核读取行为，本工具不发起新探测或调用选择写入接口。记录时间是首次观察到变化的时刻。同一自动池变化可影响多个业务组，多个事件行不等于多次独立切换；分析AI频率时固定一个组统计。
- 2026-11-10起，后续切换补存前后组选择、固定状态、原/新节点在池内的位置、容差与最近探测时间/状态。只保存相关节点的位置，不存未使用节点的全量名单。报告直接展示原/新探测结果；旧样本没有的字段不能追补。原原因标签规则保持不变，新增状态用于复核，不把线索自动升级为确定原因。
- v1.19.33的URLTest实现中，`fastNotExist`初始为true，检查当前快节点是否仍在池内的循环从第二个成员开始；当现用节点恰为首项时，可因此跳过容差保护，转选较快节点。这是源码可见的边界；对历史事件仍须有当时顺序和固定状态才能逐次核实，不仅凭当前顺序断言全部命中。
- 只记录观察到节点被选中/实际使用之后发生的内置探测样本，不把API返回的既有历史导入质量统计；切换原因的证据仍可引用带原时间戳的旧探测。探测延迟不等于AI首字时间或完整请求耗时，不能判断回答内容、限流、服务封禁或用户主观感受。
- 实际流量不是带宽测试，低流量不代表低带宽；长连接可能在切换后仍用旧节点。采样间已结束连接的尾部流量会漏记。错误只按日志附近的组选择推断归属，不能把该节点的错误计数称为确认失败率。
- 报告按北京时间逐小时、日期、节点和AI/其他代理范围筛选，展示采集覆盖、活跃/选中时间、连接错误、内置探测P50/P95及流量。相同节点多天的数据更适合比较高低峰；不同接入网络、配置或内核上下文单独保留证据，不直接混作节点退化。

## 启动与恢复

```powershell
# 在项目根运行。用户授权监控后才安装此临时任务；不恢复旧规则维护任务。
.\tools\Install-ClashMonitor.ps1 -Days 5
```

任务名为`Jimmy-Clash-Usage-Monitor-<本次时间>`，以当前登录用户运行`pythonw.exe`，不弹出控制台、不保存Windows密码。5分钟周期仅用于进程异常退出/登录后的恢复；单实例锁及任务IgnoreNew防止重复采集。不会主动唤醒电脑，截止时间到达后进程自动结束，任务触发边界同时到期。停止记录不会删除数据。

输出在Git忽略的`.local/clash-monitor/<本次时间>/`，所有个人监控数据只留本机：

| 文件 | 用途 |
|---|---|
| `session.json` / `installation.json` | 本轮起止时间、临时任务登记与运行入口 |
| `status.json` | 最近采集状态、日志流在线状态和AI路径 |
| `monitor.sqlite` | 本地事件和分钟数据；有运行中的WAL时不要只复制单一DB文件 |
| `report.html` | 无外部资源的本地交互报告，每5分钟重新生成；打开后刷新页面看新数据 |
| `minutes.csv` / `health.csv` / `switches.csv` | 本地完整结构化导出 |

无需刷新公开订阅。当前入口索引在`.local/clash-monitor/current.json`。以下命令默认使用这一轮：

```powershell
.\.venv\Scripts\python.exe -X utf8 tools/clash_monitor.py status
.\.venv\Scripts\python.exe -X utf8 tools/clash_monitor.py report
.\.venv\Scripts\python.exe -X utf8 tools/clash_monitor.py mark --kind stall
.\.venv\Scripts\python.exe -X utf8 tools/clash_monitor.py mark --kind disconnect
.\.venv\Scripts\python.exe -X utf8 tools/clash_monitor.py mark --kind good
.\.venv\Scripts\python.exe -X utf8 tools/clash_monitor.py stop
```

体验标记不是必需操作；遇到AI卡顿时记一次，可在报告里把时间与节点切换、错误对应起来。停止后`stop.request`会阻止恢复任务重新采集。卸载时先停止，再只删除`installation.json`中精确记录的本轮任务名；不要清理其他Clash任务或个人数据。

250MiB数据库预算触发时提前停止，并在事件中记录。截止后需要延长时另建一轮；不静默延长本轮。日志流/API不可用时记录缺测并自动重连，不改控制端口、不暴露本地监听服务。

技术依据：[Mihomo API](https://wiki.metacubex.one/api/)、[URLTest容差](https://wiki.metacubex.one/config/proxy-groups/url-test/)、[v1.19.33选择实现](https://github.com/MetaCubeX/mihomo/blob/v1.19.33/adapter/outboundgroup/urltest.go)。
