# 启动、学习和诊断

按 README 启动。Mac 用专用 Lima VM，项目代码复制到 VM 的 `~/jiuwen-ops-lab`，没有共享可写宿主目录。订单容器由工程交付服务独立管理，Compose 管理其余支撑服务；重新启动支撑服务不会把已修复应用重置为旧基线。

VM 名固定 `jiuwen-ops-lab`，现有其他 VM 不复用、不修改。

## 模型稍后配置

```bash
cp config/model.env.example .local/model.env  # 仅在文件还没有时；不要覆盖已有 Key
chmod 600 .local/model.env
# 编辑 API_BASE、API_KEY、MODEL_NAME、MODEL_PROVIDER、ENDPOINT_PROFILE
scripts/lab configure-model
```

`API_BASE` 必须是供应商提供的基础 API 地址。OpenAI 兼容服务使用 `MODEL_PROVIDER=OpenAI`，并按官方支持选择 endpoint profile；具体供应商配置后先运行真实接线验收。不要借用其他项目已经配置的 Key。

页面 runner 显示 WAITING_MODEL 是预期状态；模型完整配置之后会开始领取排队事件。工具/模型异常会真实返回失败并保留记录，不会退回 fake model。

## GitHub

默认实验分支 `lab-live`；第一次注入会创建它。仓库 Actions 必须启用，当前登录需要代码写入、PR/合并、Actions dispatch/read 权限。`scripts/lab init --github` 从当前 gh 登录读取 Token 到忽略文件，不输出 Token。也可自己把专用凭证写入 `.local/secrets/github_token`。

GitHub Actions 不需要模型 Key，不接入本地 VM，不配置公网回调。控制中心主动轮询真实 CI；构建产物由工程服务通过 GitHub API 获取。默认只需要仓库 Token，无须 GHCR Token。实验合并/发布仅限自己的演示仓库。

## 查看后台

```bash
scripts/lab vm-status
limactl shell jiuwen-ops-lab
cd ~/jiuwen-ops-lab
sudo scripts/lab status
sudo scripts/lab logs runner
sudo scripts/lab logs delivery
```

查看运行 Web：`http://127.0.0.1:18780`；业务 Swagger：`http://127.0.0.1:18080/docs`。

## 网络

Lima 会传播宿主代理地址；专用 VM 的 Docker daemon 可由 `scripts/configure_guest_proxy.py` 配置该代理。该脚本不输出凭证，不在已有容器运行时自行重启 Docker。仅在本项目新 VM 使用，不在共享 Docker 主机随意执行。

若当前网络无法访问 Docker Hub，可在 VM 的 `.local/runtime.env` 设置：

```dotenv
PYTHON_BASE=mirror.gcr.io/library/python:3.11-slim-bookworm
DOCKER_CLI_IMAGE=mirror.gcr.io/library/docker:29.1.3-cli
REGISTRY_MIRROR_PREFIX=mirror.gcr.io/
```

Python 包和 Debian apt 也可分别通过 `PIP_INDEX_URL` / `UV_INDEX_URL` / `APT_MIRROR_SITE` 选择受信镜像；配置只作用于本项目构建。参见 [TUNA 官方 PyPI 帮助](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)。

这是可选下载通道，不降低 TLS 校验。CI 默认使用标准官方仓库。在 VM 中 Docker daemon 的 registry mirror 也可能需要按网络环境配置。Google 镜像缓存不保证每个镜像都有，失败时检查具体镜像和出口。

## 学习顺序

1. `apps/order_api/pricing.py` 与 HTTP/数据库路径。
2. `compose.yaml` 看独立服务、网络和凭证。
3. `lab/control.py` 看产品事件状态。
4. `lab/runner.py` 看官方 SDK 的请求、事件、工具回调和取消。
5. `lab/tools.py` 与 `lab/evidence.py` 看模型可见的工具。
6. `lab/delivery.py` 看真实工作区、测试、PR、版本门槛。
7. `contracts/check_http.py` 与 `lab/probe.py` 看“修复成功”的独立判据。

## 停止与重置

工作台“停止后续动作”取消事件；已发生的 PR/合并/发布保留。VM 内 `sudo scripts/lab stop` 停止服务，`limactl stop jiuwen-ops-lab` 停止专用 VM。数据卷保留。重新注入故障前，应先确保已有事件已完成或取消，且已知正常基线仍可部署。注入器先用新提交把实验分支的业务源码/测试目录恢复到所选可信健康基线，再提交故障；不强推分支，既有修复 PR 和提交历史都保留。

不提供默认的 `down -v`、删除 VM、强推实验分支或清理全部 Docker 缓存。需要从零重做时先导出事件/动作/验证材料，再明确选择要删除的本项目资源。

## 验收分层

无模型 smoke：独立组件、健康订单/DB、官方 CLI 能力查询、凭证边界。真实故障：B 返回500、日志指标与告警形成事件。工程链：实际 PR/CI/构建/部署。真实 Agent：必须有外部模型调用、实际 host tool、模型生成 diff 与完整恢复。各层结果单独保留，不能互相替代。


## 单独验证工程交付链（不算 Agent 验收）

在正常基线已验证、受控故障已部署后，可在专用 VM 内执行：

```bash
cd ~/jiuwen-ops-lab
sudo python3 scripts/engineering_acceptance.py
```

脚本明确使用人工编写的案例补丁，经真实工具接口创建真实 PR，等待实际 CI、合并、两平台构建、digest 发布和独立业务验证。它会取消当前排队事件以独占这次工程实验；只应在本项目专用 VM 使用。结果状态为 `DELIVERY_ACCEPTANCE_PASSED`，时间线明确 `model_calls=0`，从不伪造 SDK 输出或冒充模型修复。

完成后可再次制造故障，为后续真实模型验收准备新事件。


代码同步会核对已有 VM 的数据库身份。换一个 clone 后若 `.local` 是新生成的，不能直接覆盖旧 VM 的配置；恢复原配置后再同步。模型 Key 只更新使用 `scripts/lab configure-model`，不需要覆盖整个 VM 配置。
