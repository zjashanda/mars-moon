# marsMoon 工作流

## 1. 目标

`mars-moon` 是一套可迁移的本地 bundle，用来把以下输入收敛成完整测试闭环：

- `需求文档.md`
- `词条处理.xlsx`
- `tone.h`
- 可选的待测固件 `firmware.bin`

工作原则：

- `assets/` 中的内容视为固定随包资源。
- `references/` 中的内容视为随包说明文档。
- `tools/`、`scripts/`、`sample/` 中的内容视为实际执行依赖。
- 串口默认值集中存放在 `tools/serial_ports.json`，后续长期改口时优先改这一处。
- 声卡默认值集中存放在 `tools/audio_devices.json`，后续长期改口时优先改这一处。
- 指定声卡播报依赖外部 Codex skill `listenai-play` / `listenai-laid-installer`；当前 bundle 会在缺失时自动从 Git 安装到 `~/.codex/skills/`，不需要把这两个 skill 再手工打包进 `mars-moon`。
- 运行时允许从任意路径读取“本次任务的输入文件”。
- 一旦执行 `prepare`，后续 `build / burn / run / probe` 都只依赖当前 workspace 内已经复制好的文件。

## 2. 目录说明

```text
mars-moon/
├─ assets/
│  └─ reference/
├─ references/
├─ scripts/
├─ tools/
│  └─ burn_bundle/
│     ├─ windows/
│     └─ linux/
├─ sample/
├─ wavSource/
├─ work/
└─ SKILL.md
```

标准 workspace 结构如下：

```text
<workspace>/
├─ 需求/
│  ├─ 需求文档.md
│  ├─ 词条处理.xlsx
│  ├─ tone.h
│  └─ 需求和用例补充说明.txt
├─ 用例skill参考/
│  └─ CSK5062_杜亚窗帘_测试用例v2.xlsx
├─ tools/
│  └─ burn_bundle/
│     ├─ windows/
│     └─ linux/
├─ sample/
├─ generated/
├─ work/
├─ result/
├─ wavSource/
├─ artifacts/
│  ├─ firmware/
│  └─ burn/
└─ .marsmoon_workspace.json
```

## 3. 推荐顺序

### 3.0 可选：先检查或刷新外部播报 skill

首次迁移到新机器，或怀疑外部声卡 skill 版本过旧时，先执行：

```bash
python3 ./scripts/mars_moon_pipeline.py skills --mode ensure
python3 ./scripts/mars_moon_pipeline.py skills --mode refresh
```

说明：

- `ensure`：本地缺失时自动安装。
- `refresh`：将已安装 skill 拉到 Git 远端最新版本。
- 正式测试默认建议只做 `ensure`，不要每次都自动 `refresh`。

### 3.1 准备 workspace

Windows / PowerShell 示例：

```powershell
python .\scripts\mars_moon_pipeline.py prepare `
  --workspace .\work\marsmoon-demo `
  --requirement-doc .\demo-input\需求文档.md `
  --word-table .\demo-input\词条处理.xlsx `
  --tone-file .\demo-input\tone.h `
  --firmware-bin .\demo-input\firmware.bin
```

Linux / bash 示例：

```bash
python3 ./scripts/mars_moon_pipeline.py prepare \
  --workspace ./work/marsmoon-demo \
  --requirement-doc ./demo-input/需求文档.md \
  --word-table ./demo-input/词条处理.xlsx \
  --tone-file ./demo-input/tone.h \
  --firmware-bin ./demo-input/firmware.bin
```

说明：

- `demo-input` 只是示例目录名，可以替换成任意输入路径。
- 如果不提供 `--firmware-bin`，后续仍然可以先做 `build` 和 `run --dry-run`。

### 3.2 生成测试资产

Windows / PowerShell 示例：

```powershell
python .\scripts\mars_moon_pipeline.py build `
  --workspace .\work\marsmoon-demo
```

Linux / bash 示例：

```bash
python3 ./scripts/mars_moon_pipeline.py build \
  --workspace ./work/marsmoon-demo
```

生成结果位于：

- `generated/cases.json`
- `generated/deviceInfo_dooya.json`
- `generated/CSK5062_杜亚窗帘_测试用例.xlsx`
- `work/normalized_spec.json`
- `work/tone_map.json`
- `work/source_inventory.md`

### 3.3 先做 dry-run

Windows / PowerShell 示例：

```powershell
python .\scripts\mars_moon_pipeline.py run `
  --workspace .\work\marsmoon-demo `
  --dry-run `
  --limit 5
```

Linux / bash 示例：

```bash
python3 ./scripts/mars_moon_pipeline.py run \
  --workspace ./work/marsmoon-demo \
  --dry-run \
  --limit 5
```

用途：

- 先校验 `cases.json`、`deviceInfo`、音频资源、动作结构是否齐全。
- 不接设备时也能先验证生成链路是否合理。

### 3.4 烧录固件

Windows / PowerShell 示例：

```powershell
python .\scripts\mars_moon_pipeline.py burn `
  --workspace .\work\marsmoon-demo `
  --ctrl-port COM15 `
  --burn-port COM14
```

Linux / bash 示例：

```bash
python3 ./scripts/mars_moon_pipeline.py burn \
  --workspace ./work/marsmoon-demo \
  --ctrl-port /dev/ttyACM0 \
  --burn-port /dev/ttyACM1
```

默认硬件口径：

- Windows
  - 控制口：`COM15 @ 115200`
  - 日志口：`COM14 @ 115200`
  - 协议口：`COM13 @ 9600`
- Linux
  - 控制口：`/dev/ttyACM0 @ 115200`
  - 日志口：`/dev/ttyACM1 @ 115200`
  - 协议口：`/dev/ttyACM2 @ 9600`
- 烧录波特率：`1500000`

说明：

- `tools/serial_ports.json` 负责平台默认端口，以及“没有需求文档/没有 build 产物时”的回退波特率。
- `tools/audio_devices.json` 负责平台默认播报声卡，以及“指定声卡失效时是否允许回退默认声卡”的基础策略。
- 只要 workspace 是通过需求文档完成 `build` 生成，日志口波特率和协议口波特率就会写入 `work/normalized_spec.json` 与 `generated/deviceInfo_dooya.json`，后续 `burn` / `run` / `probe` 在未显式传 `--log-baud` / `--uart1-baud` 时会自动跟随需求文档解析值。
- 烧录基础工具应随 `mars-moon/tools/burn_bundle/windows/` 或 `mars-moon/tools/burn_bundle/linux/` 一起迁移。
- `prepare` 后，workspace 内会有 `tools/burn_bundle/` 副本，`burn` 阶段会按当前操作系统优先选择对应子目录，再复制到 `artifacts/burn/` 作为实际执行目录。
- 当前 `windows/` 与 `linux/` 两套烧录目录都已就位；运行时按当前平台自动选择。
- 播报链路允许依赖 `~/.codex/skills/listenai-play` 与 `~/.codex/skills/listenai-laid-installer`；缺失时由 `tools/codex_skill_bootstrap.py` 自动安装。

### 3.5 正式执行 runner

Windows / PowerShell 示例：

```powershell
python .\scripts\mars_moon_pipeline.py run `
  --workspace .\work\marsmoon-demo `
  --log-port COM14 `
  --uart1-port COM13
```

Linux / bash 示例：

```bash
python3 ./scripts/mars_moon_pipeline.py run \
  --workspace ./work/marsmoon-demo \
  --log-port /dev/ttyACM1 \
  --uart1-port /dev/ttyACM2
```

说明：

- 如果这个 workspace 是根据需求文档执行过 `build` 生成的，上面可以不写 `--log-baud` / `--uart1-baud`，runner 会自动取需求文档中的日志口、协议口波特率。
- 只有在临时联调、想覆盖需求文档值时，才手工传 `--log-baud` / `--uart1-baud`。
- 如果要在本次 `run` 前同步 Git 上最新的外部播报 skill，可额外加 `--refresh-codex-skills`。
- 结果目录默认会输出 `execution_summary.md`、`requirement_status.md`、`testResult.xlsx`、`tool.log`、串口原始日志，正式回归时应以这些文件为准做需求级回写。

### 3.5A 已确认口径变化时，先改 spec 再重跑

如果用户、产品或研发明确确认“实际行为才是正确口径”，不要只在口头上解释，要按下面顺序处理：

1. 先把需求口径写回 `tools/dooya_spec_builder.py`，必要时标记成 `user_confirmed` 来源。
2. 再改 `tools/dooya_case_builder.py`，让 case 的动作和断言与新口径一致。
3. 然后重新执行 `build -> burn -> run`，不要直接沿用旧结果目录。

典型例子：

- 设置窗口里的普通控制词本来就允许响应，就不能继续把 `打开窗帘` 当“无效词”负例。
- 新口径应该改成“普通控制词可执行，且设置窗口仍可继续完成后续设置”。

### 3.6 执行 probe

Windows / PowerShell 示例：

```powershell
python .\scripts\mars_moon_pipeline.py probe `
  --workspace .\work\marsmoon-demo `
  --mode audio-probe `
  -- --log-port COM14 --log-baud 115200 --word 你好杜亚 `
     --audio-file .\work\marsmoon-demo\wavSource\你好杜亚.mp3 `
     --repeat 2 --observe-s 3.0 --ensure-loglevel
```

Linux / bash 示例：

```bash
python3 ./scripts/mars_moon_pipeline.py probe \
  --workspace ./work/marsmoon-demo \
  --mode audio-probe \
  -- --log-port /dev/ttyACM1 --log-baud 115200 --word 你好杜亚 \
     --audio-file ./work/marsmoon-demo/wavSource/你好杜亚.mp3 \
     --repeat 2 --observe-s 3.0 --ensure-loglevel
```

### 3.7 一步完成

Windows / PowerShell 示例：

```powershell
python .\scripts\mars_moon_pipeline.py full `
  --workspace .\work\marsmoon-demo `
  --requirement-doc .\demo-input\需求文档.md `
  --word-table .\demo-input\词条处理.xlsx `
  --tone-file .\demo-input\tone.h `
  --firmware-bin .\demo-input\firmware.bin
```

Linux / bash 示例：

```bash
python3 ./scripts/mars_moon_pipeline.py full \
  --workspace ./work/marsmoon-demo \
  --requirement-doc ./demo-input/需求文档.md \
  --word-table ./demo-input/词条处理.xlsx \
  --tone-file ./demo-input/tone.h \
  --firmware-bin ./demo-input/firmware.bin
```

## 4. 串口变化时怎么修改

后续如果设备枚举变化、换了 USB 口、或 Linux 下 `/dev/tty*` 名称变化，可以按下面三种层级修改。

### 4.1 只改本次执行，优先用命令行覆盖

这是最推荐的方式，不改 bundle 默认值，也不影响别人。

Windows 示例：

```powershell
python .\scripts\mars_moon_pipeline.py run `
  --workspace .\work\marsmoon-demo `
  --ctrl-port COM21 `
  --log-port COM22 `
  --uart1-port COM23
```

Linux 示例：

```bash
python3 ./scripts/mars_moon_pipeline.py run \
  --workspace ./work/marsmoon-demo \
  --ctrl-port /dev/ttyUSB0 \
  --log-port /dev/ttyUSB1 \
  --uart1-port /dev/ttyUSB2
```

常用覆盖参数：

- `burn` 阶段
  - `--ctrl-port`
  - `--burn-port`
  - `--log-baud`（仅临时覆盖需求文档/默认值）
- `run` 阶段
  - `--ctrl-port`
  - `--log-port`
  - `--uart1-port`
  - `--log-baud`
  - `--uart1-baud`
- `probe` 阶段
  - 透传参数中的 `--log-port`
  - 透传参数中的 `--uart-port`
  - 透传参数中的 `--log-baud`

### 4.2 想让某个 workspace 固化新串口，改生成后的配置文件

如果一个 workspace 会被重复执行，可以直接改它自己的配置文件：

- `generated/deviceInfo_dooya.json`
- `work/normalized_spec.json`

常见字段：

- `generated/deviceInfo_dooya.json`
  - `pretestConfig.ctrlPort`
  - `deviceListInfo.cskApLog.port`
  - `deviceListInfo.uart1.port`
  - `powerControl.port`
- `work/normalized_spec.json`
  - `runtime.log_port.port`
  - `runtime.log_port.baudrate`
  - `runtime.protocol_port.port`
  - `runtime.protocol_port.baudrate`
  - `requirement.defaults.log_uart`
  - `requirement.defaults.log_baudrate`
  - `requirement.defaults.protocol_uart`
  - `requirement.defaults.protocol_baudrate`

注意：

- 这种方式只影响当前 workspace。
- 如果你重新执行一次 `build`，这些内容可能会被重新生成覆盖。

### 4.3 想让后续所有新 workspace 都默认使用新串口，优先改集中配置文件

如果你们的硬件环境长期变了，比如以后 Linux 默认不是 `/dev/ttyACM0~2`，而是另一组固定口，就应该改 bundle 默认值。

优先修改：

- `tools/serial_ports.json`
- `tools/audio_devices.json`
- `tools/codex_skill_bootstrap.py`（管理外部声卡 skill 的 Git 来源与同步方式）

示例结构：

```json
{
  "windows": {
    "ctrl_port": "COM15",
    "burn_port": "COM14",
    "log_port": "COM14",
    "protocol_port": "COM13"
  },
  "linux": {
    "ctrl_port": "/dev/ttyACM0",
    "burn_port": "/dev/ttyACM1",
    "log_port": "/dev/ttyACM1",
    "protocol_port": "/dev/ttyACM2"
  }
}
```

这一份配置会被以下脚本统一读取：

- `scripts/mars_moon_pipeline.py`
- `tools/dooya_spec_builder.py`
- `tools/dooya_link_probe.py`
- `sample/voiceTestLite.py`

改完后建议至少重新验证一次：

```text
prepare -> build -> run --dry-run
```

## 5. 执行阶段口径

- `prepare` 之后，所有运行都基于 workspace 内的输入副本，不再依赖原始输入目录。
- 设置类命令必须走完整闭环：唤醒设备 -> 进入设置模式 -> 播报目标词 -> 校验设置结果生效。
- 每次检测到设备重启后，无论是主动还是被动，都要重新设置日志等级并确认日志恢复，再继续测试。
- 主动 `reboot` / 主动上下电不计入异常重启阈值；正常语音执行过程中的被动重启才计入。
- 如果连续 3 条用例都因唤醒失败而失败，应立即停止本轮执行并保留现场。

## 6. 结果归档

每次 `run` 都会在 workspace 下生成新的结果目录，例如：

```text
result/<MMDDHHMMSS>/
├─ tool.log
├─ serial_raw.log
├─ protocol_raw.log
├─ execution_summary.md
└─ testResult.xlsx
```

建议最少保留：

- `generated/` 中的用例和设备配置
- `work/` 中的规格化中间产物
- `artifacts/` 中的固件副本和烧录日志
- `result/` 中的正式执行证据

### 6.1 源码与结果分离

`mars-moon` 仓库默认只保存 skill 主体，不直接提交本地运行产物。

默认忽略的本地产物包括：

- `.venv/`
- `tmp/`
- `result/`
- `work/*/` 下的单次 workspace、调试目录和全链路结果目录
- 各类串口原始日志、tool log、临时文件

保留在仓库内的内容应以“可复用资产”为主：

- `SKILL.md`
- `references/`
- `scripts/`
- `tools/`
- `sample/`
- `assets/`
- `generated/` 中需要随 skill 一起保留的基线生成物
- `work/` 根目录下少量长期方法文档或分析文档

### 6.2 结果怎么归档

如果某一轮执行结果需要长期保留或发给别人复盘，建议按下面方式处理：

1. 先保留原始结果目录，不改动其中的 `execution_summary.md`、`requirement_status.md`、`testResult.xlsx`、`tool.log`、`serial_raw.log`、`protocol_raw.log`。
2. 以“单轮结果目录”为单位做归档，不要把多轮结果混在一起。
3. 优先把结果目录导出到仓库外的独立归档位置，或打包成单独压缩包分享，而不是直接提交到 skill 主分支。
4. 若必须在仓库内留痕，优先只提交摘要文档或结论 Markdown，不提交整轮原始日志和大体积结果目录。

Linux 示例：

```bash
tar -czf marsmoon-result-20260420-174910.tgz \
  -C ./work/fullchain-protocol-uart2-20260420-1456 \
  .
```

Windows PowerShell 示例：

```powershell
Compress-Archive `
  -Path .\work\fullchain-protocol-uart2-20260420-1456\* `
  -DestinationPath .\marsmoon-result-20260420-174910.zip
```

### 6.3 发布到 GitHub 前的建议

发布 `mars-moon` skill 到 GitHub 前，建议先确认：

- `.gitignore` 已覆盖 `.venv/`、`tmp/`、`result/`、`work/*/`
- 待发布目录里没有单次调试结果、递归 `artifacts/`、大体积日志
- 要共享的测试结果已经单独归档

如果本地目录已经积累了很多实机结果，优先先做一个“干净发布副本”再推送，避免把历史结果目录和递归归档一并带上云端。

## 7. 迁移建议

把整个 `mars-moon` 目录复制到新机器后，只需要保证：

- Python 运行环境可用。
- 构建依赖与串口依赖已安装。
- 新机器能访问本次任务的输入文件和目标串口。

除此之外，不应再要求新机器访问旧机器上的绝对路径。若文档、脚本或说明中仍出现旧机器盘符路径，应视为待清理项。
