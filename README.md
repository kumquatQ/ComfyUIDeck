# ComfyDeck — ComfyUI 云端工具箱

> 脚本文件：`comfydeck.py`

在 **JupyterLab** 里运行的图形化控制台,一个面板搞定云端 ComfyUI 的**安装 → 拉模型 → 跑 → 分析 → 备份 → 省盘**全流程。基于 `ipywidgets`,面向**云端 Linux 实例**(AutoDL / RunPod / 矩池云等)。

---

## 快速开始

在 JupyterLab 的一个单元格里运行:

```python
%run comfydeck.py
```

界面会显示一个 **6 标签页**的面板。6 个标签页的「ComfyUI 路径」**全局联动**——在任一页改路径或重新探测,其它页自动同步。

### 环境要求
- **JupyterLab + ipywidgets 8**。若界面显示成 `VBox(children=...)` 这类文字而不是控件,说明 ipywidgets 前端没就绪:
  ```python
  !pip install -U ipywidgets
  ```
  然后 **重启内核(Kernel → Restart)+ 刷新浏览器(Ctrl+Shift+R)**,再 `%run comfydeck.py`。
- **云端 Linux**(多数功能依赖 `apt` / `setsid` / `deadsnakes` 等;安装 Python、后台运行等仅适配 Ubuntu)。
- 路径会**自动探测** ComfyUI 位置;探测不准时手动改输入框即可(改一处,六页同步)。

---

## 六个标签页

### 🛠 1. ComfyUI 安装
从零搭好 ComfyUI,依赖与节点**全部装进 `<ComfyUI>/venv` 虚拟环境**,不污染系统。

- **基础 Python**:自动探测系统已装版本,下拉选择(默认优先 3.12/3.11/3.10)。
- **安装 Python**:系统缺 3.11/3.12 时,下拉选版本一键装(deadsnakes PPA,仅 Ubuntu)。
- **安装选项**:
  - PyTorch + **CUDA 版本**(`cu130` / `cu128` / `cu126` / `cu124`,默认 cu128);
    - **RTX 50 系(5090 等)选 `cu128` 或 `cu130`**;40 系及以下任意皆可。
  - xformers、requirements.txt。
- **🔎 检测当前 PyTorch / CUDA**:查看 venv 里 torch 版本、CUDA、GPU 是否可用。
- **自定义节点**:勾选常用 8 个一键克隆安装。
- **流程按钮**:`1.克隆 → 2.创建虚拟环境 → 3.安装依赖 → 4.安装节点 → ▶启动`。
- **后台运行 / 停止 / 日志**:`▶ 启动`为**后台常驻**(关掉 cell 也不停,端口 8188),PID 写入 `comfyui.pid`;`■ 停止`结束进程;`📜 查看日志`看 `<ComfyUI>/comfyui.log`。
  - PID 持久化后,**即使重跑 `%run comfydeck.py`,也能识别「已在运行」并正常停止**。

### ⬇ 2. 直链下载器
用 `aria2c` 多线程(16 线程)下载任意直链,**支持断点续传、批量**。

- **任务列表**:每行独立选「下载目录(模型类型)+ 二级目录 + 链接」,「+ 添加任务」加多条。
- **选项**:Token(鉴权直链)、强行覆盖。
- 下载到 `<ComfyUI>/models/<类型>/<二级目录>`。Civitai 等直链都能下。

### 🤗 3. HuggingFace 克隆
用新版 `hf download` 拉 HF 仓库(模型 / 数据集 / App空间)。

- **仓库地址**:完整 URL 或 `用户名/仓库名`。
- **克隆模式**:整个仓库 / 仅允许以下文件 / 排除以下文件。
- **选项**:
  - **使用 HF 镜像(hf-mirror)**:国内云端下载加速、防超时;
  - **整仓对齐下载(下到 ComfyUI 根)**:把仓库直接下到 ComfyUI 根目录,仓库内 `models/…` 自动归位(与上传配套,见下文「典型流程」);
  - 独立子文件夹、Token、强行覆盖。
- 步骤:`1.解析仓库`(看文件列表)→ `2.确认下载`。
- 文件**直接下到本地目录**(`--local-dir`),不占用全局 HF 缓存。私有库需勾 Token。

### 🔍 4. 工作流分析 + 缺失节点安装
上传一个 ComfyUI 工作流 `json`,列出它**用到的模型与节点**,并能**一键补齐缺失的自定义节点**。

- 自动识别 **UI 格式**(普通保存)和 **API 格式**(Save API Format)。
- **模型清单**:目录归类 + 来源节点 + 对照本地 `models/` 标 ✅已存在 / ❌缺失。
- **节点清单**:节点类型 + 出现次数。
- **🧩 缺失节点安装**(点「识别工作流节点」):拉取 ComfyUI-Manager 的官方节点映射,把节点分三类——
  - **匹配到的自定义节点仓库** → 勾选列表(标已装/未装),一键 `git clone` + 装依赖(**装进 venv**);
  - **ComfyUI 内置节点** → 归类、无需安装;
  - **未匹配(数据库未收录)** → **逐个列出节点名**,确认是自定义的就用「手动安装」**粘贴其 GitHub 链接** → clone 并自动装依赖。
  - 国内拉映射慢可勾「用 GitHub 镜像」。装完**重启 ComfyUI 生效**。

### ⬆ 5. 上传模型
把本地 `models/` 里的模型上传到你的 HuggingFace 仓库(备份 / 迁移)。

- **🔄 扫描本地模型** → 勾选(全选/全不选,显示大小)。
- **目标仓库 + Token(需 write 写权限)+ 类型**(model/dataset)。
- **私有仓库**:勾选后自动创建私有库(`--exist-ok`,已存在则跳过)。
- **上传加速**:`hf_transfer`,默认开。
- **目录对齐**:上传路径自动加 `models/` 前缀(如 `models/clip_vision/xxx.safetensors`),方便日后整仓还原。

### 🧰 6. 云端运维
关机前的「省盘 + 救产出」一站式。

- **💾 磁盘**:`📊 磁盘概况`(`df` + `models` 各类型占用排行);`🧹 一键清理`(pip 缓存 / HF 下载缓存 / `__pycache__`,可勾选)。
  - 清理 HF 缓存只清下载缓存,**不影响**已下到 `models/` 的模型。
- **🖼 产出**:
  - `🔄 扫描 output`(数量 + 大小);
  - `🖼 预览图片`(最近 12 张缩略图网格);
  - `📦 打包下载`(zip 到 ComfyUI 同级,去文件树右键 Download);
  - `⬆ 上传 output`(备份到 HF dataset);
  - `☁ 上传到网盘(rclone)`:支持 **OneDrive** 等,见下文配置。

---

## 典型流程

### A. 新实例从零搭好
1. **🛠 安装**:克隆 → 创建 venv(基础 Python 选 3.11/3.12)→ 装依赖(CUDA 按卡选)→ ▶ 后台启动。
2. **⬇/🤗 下载**:用直链或 HF 克隆把模型拉到 `models/`。
3. **🔍 分析 + 补节点**:上传工作流 json → 按「缺失」清单补模型 → 「识别工作流节点」一键装缺失的自定义节点 → 重启生效。

### B. 备份 / 迁移到新机器(上传↔下载闭环)
1. 旧机:**⬆ 上传模型** → 勾选 → 传到 `你的用户名/my-models`(可私有 + 加速)。仓库内结构为 `models/<类型>/<文件>`。
2. 新机:**🤗 HF 克隆** → 填 `你的用户名/my-models` → **勾「整仓对齐下载」** → 确认。
3. 所有模型**自动归位**到 `<ComfyUI>/models/对应类型/`,无需手动分目录。

### C. 关机前救产出
**🧰 运维 → 产出**:预览确认 → 打包下载 到本地,或 上传 HF / OneDrive 备份。

---

## OneDrive(rclone)配置一次

工具能装 rclone、能上传,但**授权必须你做一次**:

**方式 A(推荐,本地配好再传上去)**
1. 本地电脑装 rclone(rclone.org/downloads);
2. 运行 `rclone config` → `n` 新建 → 名字 `onedrive` → 选 `Microsoft OneDrive` → 一路默认 → 浏览器登录授权;
3. 把配置文件 `~/.config/rclone/rclone.conf`(Windows 在 `%USERPROFILE%\.config\rclone\` 或 `AppData\Roaming\rclone\`)上传到云端 `~/.config/rclone/rclone.conf`;
4. 工具里点「🔄 检测/刷新网盘」即可看到并选用。

**方式 B(云端无浏览器)**:云端 `rclone config` 走到授权步选 headless,按提示在**本地**跑 `rclone authorize "onedrive"`,把 token 粘回云端。

配好后一劳永逸;rclone 也支持 Google Drive / 百度网盘等,配了就能在下拉里选。

---

## 常见问题

| 现象 | 处理 |
|---|---|
| 界面显示成 `VBox(children=...)` 文字 | `!pip install -U ipywidgets` → 重启内核 + 刷新浏览器 |
| 5090 跑不了 / `sm_120` 报错 | PyTorch 选 `cu128` 或 `cu130`(cu124/cu126 不支持 5090) |
| 缺失节点识别里出现「ComfyUI(N 个节点)」 | 已修;那是内置节点,现归类为「内置」不再误列 |
| 不确定哪些节点没找到 | 看摘要的「未匹配」清单(逐个列出名字),自定义的用手动安装粘贴链接 |
| HF 私有库 / 上传失败 | 下载私有库勾 Token;上传需 **write** 权限的 Token |
| 国内下载慢 / 拉节点映射慢 | HF 克隆勾「使用 HF 镜像」;节点识别勾「用 GitHub 镜像」 |

---

## 说明与限制
- **平台**:为云端 Linux 设计;安装 Python(deadsnakes)、后台运行(setsid/killpg)、磁盘清理等**仅适配 Ubuntu**,本机 Windows 不适用。
- **隔离**:所有装依赖/装节点(含工作流缺失节点安装)**强制走 `<ComfyUI>/venv`**,venv 不存在会拒绝并提示,绝不污染主环境。
- **安全**:HF token 经 `HF_TOKEN` 环境变量传递,**不写进命令行、不打印明文**;命令里的用户输入(URL/仓库名/分支/文件名等)用 `shlex.quote` 转义,防特殊字符破坏命令。
- **目录对齐**:上传加 `models/` 前缀、下载用「整仓对齐」,二者配套才能自动归位。
- 所有耗时操作在后台线程执行,执行期间对应按钮禁用,防止重复点击。
