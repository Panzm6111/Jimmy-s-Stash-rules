# 当前维护流程

日常只使用两份最新主订阅：[Stash](../config/stash.yaml)、[Clash](../config/clash-verge-auto.yaml)。旧Windows任务登记已移除，安装脚本、旧自动发布程序及其专属测试已删除，不再重新安装电脑定时任务。

## 自动执行

每端17份兼容规则由客户端直接订阅上游，24小时尝试刷新。6份必要转换由[必要规则云端更新](../.github/workflows/refresh-rules.yml)每天北京时间12:17计划执行，也可在Actions页面手动运行。GitHub调度可能延迟，长期无活动可能停用，不能承诺准点。

云端只检查核准来源、许可、语法与变化量，生成并运行回归后精确提交。未知格式、许可变化、大差量或验证失败停止发布；没有实际变化不提交。私人机场和节点不进入这个流程。普通后续维护仍使用正常Git提交，不对每日任务启用强制推送。

## 项目开发

维护源、模块、规则快照、许可证和测试是生成当前两个入口所需内容，不是旧发布版本。功能修改后运行对应生成器和现有验证：

```text
python -X utf8 tools/build_ads.py
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
python -X utf8 tools/validate.py
```

Windows使用项目`.venv`内的Python并启用UTF-8；JS验证还需要Node。全库检查应在仅含受控文件的隔离副本执行，避免读取`.local`内的私人备份。上游专项HTTP/JS和Adobe官方补充仍需人工审查，不盲目整包覆盖。

保留`PROGRESS.md`为唯一状态主文件，每次重要变更原位记录证据和未验收边界。需求和沟通过程、历史研究数据继续保存；源码删减前先核对实际生成/导入依赖。详情见[协作入口](../AGENTS.md)、[来源](SOURCES.md)和[更新说明](UPDATES.md)。

## 本次历史整理

2026-11-02用户明确要求删除旧版本并清空Git提交历史，只留整理后的新起点。整理前公开main已在本机`.local/cleanup-20261102/`备份并校验，备份不上传。GitHub保留main与两份最新入口；历史文档中的旧路径、提交号和旧教程只作为过程记录，不再是当前下载入口。
