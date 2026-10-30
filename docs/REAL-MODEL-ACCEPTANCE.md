# 真实模型验收

实际验收日期：2026-10-30（Asia/Shanghai）。用户配置的模型标识为 `DeepSeek-V4.1-Flash-1017`，通过 OpenAI 兼容接口访问。Key、接口地址和完整配置只保留在本地，不进入公开证据。

## 执行归属

`lab/runner.py` 调用官方 Process SDK，由官方 CLI/Swarm Runtime/Core 执行真实模型与工具循环。模型使用 host tools 读取实际 Prometheus/Loki、运行版本和源码，自己写业务修复与新增测试，再提交真实 PR。模型没有合并、部署或任意 shell 权限。

控制中心依据独立 CI、精确提交与运行版本授权工程服务完成合并、构建、发布。独立 probe 按两条下单路径分别计数，并直接读取 PostgreSQL；模型在独立新会话中复核恢复证据。只有独立合同和版本校验通过，产品才记为 `RESOLVED_FIXED`。

## 接线资格

[真实 SDK/模型/host tool/取消/清理证据](evidence/real-model-sdk.json)：实际工具读到了运行版本；SDK 完成并返回结构化输出；另一轮真实模型运行取消后返回 `cancelled/130`；随后观察到官方 CLI 子进程数为0。没有更换官方 Agent 实现。

## 首次接线中的失败与修正

事件 `case-812a384054014495` 的首次尝试中，模型生成了真实修复、新增回归测试并创建 [PR #3](https://github.com/lelezi257/jiuwen-ops-lab/pull/3)。但它将真实 `test-*` 回执一同放入证据列表；当时控制中心只会向取证服务查 `ev-*`，接收结果失败，最终租约超时进入 `NEEDS_HUMAN`，没有合并发布。

[2c255f0](https://github.com/lelezi257/jiuwen-ops-lab/commit/2c255f0aebd02c926d80693fb7e55f89838b1b66) 修正了产品接线：测试证据必须由工程服务核对 case 和当前测试记录，不能仅凭编号相信；在任何外部校验前保存官方 SDK 回执；验证错误进入人工终态；runner 在传输前落盘真实结果并重试结果投递，不重放业务工具。新增边界测试与原有测试共13项通过。

第二次模型尝试调用未授权的 `bash`，官方九问 allowlist 拒绝执行，产品进入 `NEEDS_HUMAN`。没有扩大权限。[d4b2314](https://github.com/lelezi257/jiuwen-ops-lab/commit/d4b2314d007ddf0b17706728ea3cd65e38e590ff) 仅补充领域任务说明：业务文件在独立工程服务中，检查已有修改使用 `get_diff`，重试可复用已有 PR。第三次由真实模型重新检查、测试和提交；早期失败与重试全部保留，不计为干净首次成功。

首轮发布后，独立业务验证已通过，但只读模型复核在 JSON 前输出了说明文字，官方 SDK 以 `OUTPUT_SCHEMA_MISMATCH` 拒收，产品保持 `NEEDS_HUMAN`。没有自行截取 JSON 或把失败改成完成。[36d2f71](https://github.com/lelezi257/jiuwen-ops-lab/commit/36d2f7112dbf4734fbee86d7fa1b8369251ef060) 明确了只输出 JSON 的要求，并增加只读复核重试：必须仍是独立报告所验证的同一个 release/source/digest，保留原有合并与发布事实，只创建新的验证 Agent 会话。

结果投递允许重试，但迟到或重复的 SDK 结果不能将 CI/合并/构建状态倒退回去；相关边界测试与原有测试合计15项通过。

## 如何复核结果

`scripts/lab agent-acceptance --trials 3` 只制造真实故障、观察真实状态和保存原始报告，不生成修复、不伪造 SDK 结果。没有模型配置时，它在制造故障前退出。

`scripts/summarize_acceptance.py --case CASE_ID --output REPORT.json` 从实际 case 和事件中导出发布链、业务窗口、模型运行、阶段耗时与已报告的用量。它不修改事件或触发动作。多个 case 可重复传入 `--case`；模型回执按 request_id 去重，未知用量保留为 `null`。

完整原始事件、测试输出和逐请求数据库证据保存在专用 VM 与本地 `.local/evidence/`。公开摘要只用于验证受控订单案例，不能推导其他故障或生产环境的成功率。
