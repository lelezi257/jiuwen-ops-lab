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

## 三次独立重置结果

固定运行平台为 `36d2f71`；[平台容器与版本](evidence/clean-trials-platform.json)、[实际下载的官方源码清单](evidence/framework-source-manifest.json)、[三轮完整摘要](evidence/real-model-three-clean-trials.json)。

三轮均由真实 Alertmanager 自动创建新事件，修复与只读复核各一个独立 SDK 会话，均零人工重试。每轮恢复可信业务源码与测试，再提交并部署新的同类故障；工作区和会话重新建立，VM 与数据库保留，以继续验证旧订单。干净重置的范围是业务源码、故障提交、工作区及会话；缓存用量按框架实际报告记录。

| 轮次 | PR | 窗口1：券/无券 | 窗口2：券/无券 | 修复/复核会话 | 结果 |
|---|---|---|---|---|---|
| 1 | [#4](https://github.com/lelezi257/jiuwen-ops-lab/pull/4) | 107/107 | 106/106 | 1/1 | RESOLVED_FIXED |
| 2 | [#5](https://github.com/lelezi257/jiuwen-ops-lab/pull/5) | 106/106 | 107/107 | 1/1 | RESOLVED_FIXED |
| 3 | [#6](https://github.com/lelezi257/jiuwen-ops-lab/pull/6) | 107/107 | 106/106 | 1/1 | RESOLVED_FIXED |

每一窗口均为60秒，所有请求成功、金额正确，实际 PostgreSQL 记录匹配；旧订单可读，非法输入保持拒绝。各轮的故障 SHA、候选 head、test-merge、merge SHA、实际构建 run、制品哈希、发布 digest 和验证身份都在摘要中串联。

### 阶段耗时与上报用量

耗时依据控制中心真实状态时间线，单位为秒；“构建/接收”包含远端构建和制品传输。“事件到结案”从实际告警事件创建计时，故障部署到发现另记。上报 total_cost 是框架/模型报告的数值，不替代供应商账单；未知字段保留 null。

| 轮次 | 故障部署→事件 | 首次模型请求→PR | CI_PENDING | 构建/接收 | 部署 | 业务窗口 | 模型复核 | 事件到结案 | tokens | 上报 total_cost |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 32.2 | 50.8 | 34.6 | 470.4 | 5.0 | 124.4 | 48.6 | 762.2 | 585863 | 0.164042 |
| 2 | 32.4 | 59.2 | 29.1 | 805.8 | 5.2 | 124.4 | 44.5 | 1093.8 | 607682 | 0.170151 |
| 3 | 31.3 | 58.2 | 36.0 | 172.5 | 5.2 | 124.5 | 41.7 | 463.2 | 440891 | 0.123449 |

首条集成调通案例含3次显式人工重试（修复2次、只读复核1次），单独保留在[集成案例证据](evidence/real-model-integration-case.json)，不混入以上干净复跑。其 SDK allowlist/输出格式失败、控制结果接收错误，以及构建轮询的观察超时均保留。轮询超时不会重派构建或把未完成状态改成成功，后续依据同一真实账本继续。

这证明本机、所配置模型、这一类可对照已知正常版本的订单回归闭环；不推导未知根因、其他业务或生产可用性。
