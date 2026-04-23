---
name: mars-moon
description: 自包含的离线语音用例编写与执行 skill。用于把需求文档、词表 Excel、tone.h 与待测固件整合成同一套可迁移 bundle，在本目录或准备出的 workspace 内完成 spec/cases/deviceInfo 生成、dry-run、烧录、runner 执行与结果归档。用户明确提到 `marsMoon`、`$mars-moon`、用例编写、用例执行、需求文档、词表、tone、串口测试、`COM8`、`COM10`、`COM13`、`COM14`、`COM15`、语音 runner 等关键词时应触发。
---

# Mars Moon

当你需要把“需求理解 + 用例生成 + 烧录 + 执行验证”收敛成一套可直接迁移到其他机器的本地 bundle 时，使用这个 skill。

当前 bundle 面向杜亚窗帘类离线语音项目，核心原则是：

- `assets/` 是固定随包资源。
- `references/` 是随包方法文档，不应依赖 `mars-moon` 目录外文件。
- `tools/`、`scripts/`、`sample/` 是实际执行入口与运行依赖。
- 播报链路允许在运行时按需引入两个外部 Codex skill：`listenai-play`、`listenai-laid-installer`；缺失时由当前 bundle 自动从 Git 安装到 `~/.codex/skills/`。
- 烧录基础工具应随 `tools/burn_bundle/windows/` 与 `tools/burn_bundle/linux/` 一起迁移，并从 bundle 复制到 workspace 内使用。
- 允许运行时从外部路径读入“本次任务的输入文件”，但一旦执行 `prepare`，后续生成、烧录、测试都应只依赖当前 workspace 内的副本。

## 何时使用

满足以下任一场景就直接使用本 skill：

- 根据 `需求文档.md`、`词条处理.xlsx`、`tone.h` 生成测试资产。
- 在同一链路内完成 `prepare / build / burn / run / probe / full`。
- 需要在当前平台默认串口基线上执行实机验证：Windows 默认 `COM15/COM14/COM13`，Linux 默认 `/dev/ttyACM0`、`/dev/ttyACM1`、`/dev/ttyACM2`。
- 需要把单次执行的输入、副本、生成物、烧录日志、串口日志、结果汇总统一归档。

## 启动后先做什么

1. 读取 `references/workflow.md`，确认当前执行目标与命令形式。
2. 读取 `references/mind.md`，理解需求拆解、状态机分析和用例生成方法。
3. 读取 `references/需求功能验证设计方法.md`，确认当前需求应如何拆成功能点、验证方案、断言和归因。
4. 若需要参考“需求提炼 + 测试方案”的完整样板，再读取 `references/masr-pillar.md`。
5. 根据用户目标选择 `prepare`、`build`、`burn`、`run`、`probe` 或 `full`。
6. 优先调用 `scripts/mars_moon_pipeline.py`，不要绕回其他 skill 或外部仓库脚本。
7. 如果要提前检查或刷新外部播报 skill，优先使用 `python3 scripts/mars_moon_pipeline.py skills --mode ensure|refresh`。

## 标准闭环

标准顺序是：`prepare -> build -> burn -> run`。
如需静态自检，可先执行：`prepare -> build -> run --dry-run`。
如需链路预检，可在 `run` 前插入 `probe`。

各阶段职责：

- `prepare`
  - 创建独立 workspace。
  - 拷贝 `tools/`、`sample/`、参考 Excel、补充说明及本次输入文件。
  - 将固件复制到 workspace 的 `artifacts/firmware/firmware.bin`。
- `build`
  - 生成 `normalized_spec.json`、`tone_map.json`、`cases.json`、`deviceInfo_dooya.json`、测试用例 Excel。
- `burn`
  - 在 workspace 内安装并执行当前 bundle 自带的烧录工具包。
  - 使用当前平台默认硬件口径：Windows 为 `COM15 @ 115200`、`COM14 @ 115200`、`COM13 @ 9600`；Linux 为 `/dev/ttyACM0 @ 115200`、`/dev/ttyACM1 @ 115200`、`/dev/ttyACM2 @ 9600`。
  - 若涉及新固件，烧录前必须把待烧录文件复制到实际烧录目录，先删除旧 `app.bin`，再将当前固件统一命名为 `app.bin`，确保目录内固件唯一。
  - 进入烧录模式时必须完整执行“断电 -> 进 boot -> 上电 -> 下 boot”；任一步失败都必须整套重来，不允许从中间续接。
  - 烧录完成后必须连接日志串口重新上电并观察 `20s`，确认无自动重启、重复启动、异常复位后，才能进入后续测试。
- `run`
  - 做串口预检、日志恢复、语音执行、失败重跑与结果归档。
  - 正式执行前必须先过最小可测性验证：设备无反复重启、默认唤醒词可唤醒、基础命令词可识别、有对应日志与响应播报；若该动作应下发主动协议，则协议串口上也应能观察到实收协议。
- `probe`
  - 将参数透传给 workspace 内的 `tools/dooya_link_probe.py` 做链路确认。

## 关键执行规则

- 所有 Mars 相关流程都应在当前 `mars-moon` bundle 或它准备出的 workspace 内执行。
- 不要把 `references/` 文档写成依赖其他机器绝对路径的说明。
- 正式测试前，先过两道门禁：
  1. 若涉及烧录，先完成烧录后 `20s` 健康检查；
  2. 再完成最小可测性验证。
- 如果烧录后健康检查失败，或最小可测性验证失败，都要立即停止测试并上报，不要继续跑全链路。
- 设置类命令的完整闭环应是：先唤醒设备，再进入设置模式，最后播报目标词完成设置，并校验设置结果已经生效。
- 已确认的设置态口径要优先于旧需求原文：在 `WAKEWORD / WORKMODE / CURTAINMODE` 设置窗口内，像 `打开窗帘` 这类普通控制词不能默认当成“无效词”；应优先验证“控制命令可执行，且设置窗口仍可继续完成后续设置”。
- 为避免假 PASS，正向控制命令默认要做“播报 + 协议”双命中校验；设置成功类步骤默认要补 `configSaved=save config success` 和后置行为验证，不能只看一条播报就判通过。
- 只要现场存在独立协议串口，主动协议和被动协议都优先用协议串口作为主断言来源；日志中的 `send msg` / `recv msg` 只作为辅助证据。
- 用例级 `setup_action` / `always_run` 恢复动作必须与主断言隔离，避免恢复默认状态的协议和播报污染主 case 结果摘要。
- 每次检测到设备重启后，都要先恢复日志等级并确认有日志输出，再继续后续测试。
- 主动 `reboot`、主动上下电不计入异常重启阈值；正常语音执行过程中发生的被动重启才计入异常重启。
- 任何非主动 `reboot`、非主动上下电、非用户明确要求的重启，一旦在用例执行过程中发生，当前用例直接判 `FAIL`，不允许容忍后继续算通过。
- `CFG-006 / CFG-007 / CFG-008 / CFG-010 / CFG-014` 当前按人工确认项管理，结果口径保持 `NO_METHOD / 人工确认`，不纳入自动化失败闭环。
- 结果目录必须保留生成物、日志、Excel 结果与执行摘要，保证后续复盘不依赖外部环境。
- `plan.md` 属于本机执行态文件，用于当前工位持续接手与回写进展；本地保留即可，不作为云端 skill 主体内容发布。

## 目录内资源

- `scripts/mars_moon_pipeline.py`
  - 当前 skill 的统一入口。
- `tools/`
  - `codex_skill_bootstrap.py`
  - `dooya_spec_builder.py`
  - `dooya_case_builder.py`
  - `dooya_deviceinfo_builder.py`
  - `dooya_link_probe.py`
  - `dooya_voice_runner.py`
  - `burn_bundle/windows/`
  - `burn_bundle/linux/`
- `sample/voiceTestLite.py`
  - runner 依赖的串口、音频和 TTS 辅助实现。
- `assets/reference/CSK5062_杜亚窗帘_测试用例v2.xlsx`
  - 随包参考用例模板。
- `assets/reference/需求和用例补充说明.txt`
  - 随包补充说明。
- `references/workflow.md`
  - 可迁移工作流说明。
- `references/current-baseline.md`
  - 当前 bundle 已验证基线。
- `references/mind.md`
  - 需求理解、逻辑分析和用例生成方法沉淀。
- `references/需求功能验证设计方法.md`
  - 当前最完整的方法论文档，包含：需求拆解、功能点验证方案、最小可测性门禁、烧录健康检查、结果归因模板。
- `references/masr-pillar.md`
  - 当前项目的“需求内容提炼 + 测试方案示例”组合样板，可供其他 skill 复用。
- `references/checkLogic.txt`
  - 用例生成时需要对齐的检查逻辑补充。
- `work/requirement-status-20260409.md`
  - 历史主需求状态汇总，可用于快速了解哪些需求已经通过、哪些仍异常或验证不足。
- `work/analysis-20260409-requirement-case-gap.md`
  - 历史需求/用例缺口分析，适合在重构用例前先复核问题归因。
- `work/analysis-20260416-functional-judgement-matrix.md`
  - 功能层 vs 数值层的断言口径矩阵，适合在调整 runner 断言前先对齐。
- `plan.md`
  - 当前机器、本轮验证结论和已确认业务口径；每次继续前都应先同步阅读并回写最新进展。

## 交付规则

- 对外展示名使用 `marsMoon`，目录名和显式调用名使用 `mars-moon` / `$mars-moon`。
- 迁移到其他机器时，直接复制整个 `mars-moon` 目录即可；不要再依赖目录外的参考脚本或参考文档。
- 若目标机器本地尚未安装 `listenai-play` / `listenai-laid-installer`，首次执行播报链路时会自动从 Git 下载到 `~/.codex/skills/`；也可以提前执行 `python3 scripts/mars_moon_pipeline.py skills --mode ensure`。
- 远端 skill 有更新时，默认不会在正式测试中自动拉最新；需要显式执行 `python3 scripts/mars_moon_pipeline.py skills --mode refresh` 或在 `run/full/probe` 时加 `--refresh-codex-skills`。
- 修改 skill 后，至少完成一次本地 `prepare + build` 验证；影响 runner 或串口链路时，再补一次 `run --dry-run` 或实机验证。
- Git 发布默认只同步 skill 主体内容，不把 `.venv/`、`tmp/`、`result/`、`work/*/` 这类本地运行产物混到主仓库里。
- `plan.md` 默认视为本地状态文件，发布 skill 到 GitHub 时不上传；新机器接手时若缺失可按 `AGENTS.md` 自动创建。
- 单轮测试结果应按 `references/workflow.md` 的“结果归档”说明单独保存；默认保留在本地 workspace/result 目录，分享时优先导出成独立归档，不直接混入源码提交。
