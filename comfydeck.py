"""
ComfyDeck — ComfyUI 云端工具箱（脚本文件: comfydeck.py）
使用方法: 在 JupyterLab 单元格中运行 %run comfydeck.py
"""

import ipywidgets as widgets
from IPython.display import display
import os, subprocess, threading, urllib.request, json, signal, shutil, shlex

# ─────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────
COMFY_MODEL_DIRS = [
    'checkpoints', 'clip', 'clip_vision', 'configs', 'controlnet',
    'diffusion_models', 'diffusers', 'embeddings', 'gligen', 'hypernetworks', 'loras',
    'model_patches', 'photomaker', 'style_models', 'text_encoders', 'unet',
    'upscale_models', 'vae', 'vae_approx', 'audio_encoders',
]
# 「自定义」选项放在列表末尾，选中后显示文本输入框
COMFY_MODEL_DIRS_WITH_CUSTOM = COMFY_MODEL_DIRS + ['自定义目录...']

# ─────────────────────────────────────────────
# 全局样式
# ─────────────────────────────────────────────
css = widgets.HTML("""
<style>
/* ===== 设计令牌（作用域 .ctk，避免污染同页其他 cell） ===== */
.ctk {
  --bg:#1a1b26; --panel:#24283b; --panel-2:#2a2e47;
  --border:#363b54; --border-2:#454b6b;
  --accent:#00bcd4; --accent-2:#3b82f6;
  --text:#c8d3f5; --text-dim:#7f8bb0;
  --ok:#4ade80; --warn:#fbbf24; --danger:#f87171;
  --radius:10px; --radius-sm:7px;
  color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;
}

/* ===== 顶层容器 & 卡片 ===== */
.ctk { background:var(--bg); padding:10px; border-radius:12px; }
.ctk .ctk-card {
  background:var(--panel); border:1px solid var(--border);
  border-radius:var(--radius); box-shadow:0 2px 10px rgba(0,0,0,.25);
}

/* ===== 标题 / 提示 ===== */
.ctk .tool-header{
  font-size:15px; font-weight:700; color:#fff;
  border-left:3px solid var(--accent); padding:6px 0 6px 10px; margin-bottom:10px;
}
.ctk .tool-tip { font-size:12px; color:var(--warn); margin-bottom:3px; }
.ctk .tool-tip2{ font-size:12px; color:var(--accent); margin-bottom:10px; }
.ctk .ctk-section{ font-size:12px; color:var(--text-dim); margin:10px 0 6px; letter-spacing:.3px; }

/* ===== 输入框 / 文本域 ===== */
.ctk .widget-text input, .ctk .widget-textarea textarea{
  background:var(--panel-2)!important; color:var(--text)!important;
  border:1px solid var(--border)!important; border-radius:var(--radius-sm)!important;
  padding:6px 10px!important; box-shadow:none!important;
}
.ctk .widget-text input:focus, .ctk .widget-textarea textarea:focus{
  border-color:var(--accent)!important; box-shadow:0 0 0 2px rgba(0,188,212,.25)!important;
}
.ctk .widget-text input::placeholder, .ctk .widget-textarea textarea::placeholder{ color:var(--text-dim); }

/* ===== 下拉 ===== */
.ctk .widget-dropdown select{
  background:var(--panel-2)!important; color:var(--text)!important;
  border:1px solid var(--border)!important; border-radius:var(--radius-sm)!important; padding:5px 8px!important;
}
.ctk .widget-dropdown select:focus{ border-color:var(--accent)!important; }

/* ===== 标签 / 复选框 ===== */
.ctk .widget-label, .ctk .widget-checkbox label, .ctk label{ color:var(--text)!important; }

/* ===== 按钮 ===== */
.ctk .jupyter-button, .ctk .widget-button{
  color:#fff!important; border:none!important; border-radius:var(--radius-sm)!important;
  font-weight:600!important; box-shadow:0 1px 3px rgba(0,0,0,.3)!important;
  transition:filter .15s ease, transform .1s ease!important;
}
.ctk .jupyter-button:hover, .ctk .widget-button:hover{ filter:brightness(1.12); transform:translateY(-1px); }
.ctk .jupyter-button:active, .ctk .widget-button:active{ filter:brightness(.95); transform:none; }
/* FileUpload 上传按钮：补深色背景，避免被全局白字规则变成「浅底白字」看不清 */
.ctk .widget-upload{ background:var(--accent-2)!important; color:#fff!important; }

/* ===== 输出区 ===== */
.ctk .widget-output{ background:#15161f!important; border-radius:var(--radius)!important; overflow:auto!important; }
.ctk .widget-output pre, .ctk .jp-OutputArea-output pre{
  color:var(--text); font-family:ui-monospace,"Cascadia Code",Consolas,monospace; font-size:12px;
}

/* ===== Tab 栏（兼容 phosphor / lumino 类名） ===== */
.ctk .p-TabBar-tab, .ctk .lm-TabBar-tab{
  color:var(--text-dim); background:transparent; border:none!important;
  padding:8px 16px; margin-right:4px; border-radius:8px 8px 0 0;
  flex:0 0 auto!important; min-width:auto!important; max-width:none!important;
  transition:color .15s ease, background .15s ease;
}
.ctk .p-TabBar-tabLabel, .ctk .lm-TabBar-tabLabel{ overflow:visible!important; text-overflow:clip!important; }
.ctk .p-TabBar-tab:hover, .ctk .lm-TabBar-tab:hover{ color:var(--text); background:rgba(255,255,255,.05); }
.ctk .p-TabBar-tab.p-mod-current, .ctk .lm-TabBar-tab.lm-mod-current{
  color:#fff!important;
  background:linear-gradient(180deg, rgba(0,188,212,.20), rgba(0,188,212,.04))!important;
  border-bottom:2px solid var(--accent)!important;
}

/* ===== 滚动条 ===== */
.ctk ::-webkit-scrollbar{ width:9px; height:9px; }
.ctk ::-webkit-scrollbar-track{ background:transparent; }
.ctk ::-webkit-scrollbar-thumb{ background:var(--border-2); border-radius:5px; }
.ctk ::-webkit-scrollbar-thumb:hover{ background:var(--accent); }
</style>
""")

W    = '760px'   # 内容区总宽
LBSW = '90px'    # 左侧 label 宽

def lbl(text, w=LBSW):
    return widgets.Label(text, layout=widgets.Layout(width=w, flex_shrink='0'))

# ─────────────────────────────────────────────
# ComfyUI 路径自动探测
# ─────────────────────────────────────────────
def detect_comfyui_path():
    """
    按优先级依次探测 ComfyUI 安装路径：
      1. 环境变量 COMFYUI_PATH
      2. 当前工作目录（若包含 main.py + models/）
      3. 常见候选路径
      4. 兜底：/root/ComfyUI
    返回 (path, source) 两元组
    """
    def is_comfyui(p):
        return (os.path.isfile(os.path.join(p, 'main.py')) and
                os.path.isdir(os.path.join(p, 'models')))

    # 1. 环境变量
    env_val = os.environ.get('COMFYUI_PATH', '').strip()
    if env_val and is_comfyui(env_val):
        return env_val, '环境变量 $COMFYUI_PATH'

    # 2. 当前工作目录
    cwd = os.getcwd()
    if is_comfyui(cwd):
        return cwd, '当前工作目录'

    # 3. 候选路径列表（云端 / 本地常见位置）
    candidates = [
        '/root/ComfyUI',
        '/root/autodl-tmp/ComfyUI',
        '/workspace/ComfyUI',
        '/home/user/ComfyUI',
        os.path.expanduser('~/ComfyUI'),
        os.path.expanduser('~/Desktop/ComfyUI'),
        '/opt/ComfyUI',
    ]
    for p in candidates:
        if is_comfyui(p):
            return p, '自动发现'

    # 4. 兜底
    return '/root/ComfyUI', '默认路径（未检测到安装）'

# 全局共享的 ComfyUI 路径：各 Tab 的路径输入框都联动到它，改一处全同步
_shared_path = widgets.Text(value=detect_comfyui_path()[0])

def make_path_row(label='ComfyUI路径:'):
    """「路径输入 + 来源 + 重新探测」一行，并联动到全局 _shared_path。返回 (row, input)。"""
    _p, _src = detect_comfyui_path()
    inp = widgets.Text(value=_p, layout=widgets.Layout(width='400px'))
    hint = widgets.HTML(f'<span style="font-size:11px;color:#7f8bb0;">来源：{_src}</span>')
    btn = widgets.Button(description='🔍 重新探测',
                         layout=widgets.Layout(width='100px', height='28px'),
                         style={'button_color': '#374151', 'font_size': '11px'})
    def on_re(b):
        p, src = detect_comfyui_path()
        inp.value = p
        hint.value = f'<span style="font-size:11px;color:#7f8bb0;">来源：{src}</span>'
    btn.on_click(on_re)
    widgets.link((_shared_path, 'value'), (inp, 'value'))
    row = widgets.VBox([
        widgets.HBox([lbl(label), inp, btn]),
        widgets.HBox([lbl(''), hint]),
    ])
    return row, inp

# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────
def stream_exec(cmd, out, indent='', env=None):
    """同步执行命令并流式打印输出，返回退出码。
    indent 非空时：逐行 rstrip、跳过空行并加缩进（用于子任务日志）。
    env 非空时：在当前环境基础上叠加（用于传 HF_TOKEN 等，避免写进命令行）。"""
    run_env = {**os.environ, **env} if env else None
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, env=run_env)
    for line in proc.stdout:
        if indent:
            line = line.rstrip()
            if not line:
                continue
            with out: print(f"{indent}{line}")
        else:
            with out: print(line, end='')
    proc.wait()
    return proc.returncode

def run_async(worker, *buttons):
    """后台线程运行 worker；执行期间禁用 buttons，结束后（含异常）恢复，防止重复点击。"""
    def _wrap():
        for b in buttons:
            if b is not None: b.disabled = True
        try:
            worker()
        finally:
            for b in buttons:
                if b is not None: b.disabled = False
    threading.Thread(target=_wrap, daemon=True).start()

def run_stream(cmd, out, *buttons, on_done=None, env=None):
    """后台执行单条命令并流式打印，完成后打印结果；可选完成回调 on_done(rc)。"""
    def worker():
        rc = stream_exec(cmd, out, env=env)
        with out:
            print("\n✅ 完成！" if rc == 0 else f"\n❌ 出错，退出码: {rc}")
        if on_done:
            on_done(rc)
    run_async(worker, *buttons)

def ensure_aria2c(out):
    if subprocess.run('which aria2c', shell=True, capture_output=True).returncode == 0:
        return True
    with out: print("⚙️ 未检测到 aria2c，正在安装...")
    subprocess.run('apt-get install -y aria2', shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = subprocess.run('which aria2c', shell=True, capture_output=True).returncode == 0
    with out:
        print("✅ aria2c 安装成功" if ok else "❌ 安装失败，请手动运行: apt-get install -y aria2")
    return ok

def ensure_hf_cli(out):
    """确保新版 hf 命令可用（huggingface_hub>=0.34 提供）。"""
    if subprocess.run('which hf', shell=True, capture_output=True).returncode == 0:
        return True
    with out: print('⚙️ 未检测到 hf 命令，正在安装/升级 huggingface_hub[cli] ...')
    subprocess.run('pip install -q -U "huggingface_hub[cli]"', shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = subprocess.run('which hf', shell=True, capture_output=True).returncode == 0
    with out:
        print('✅ hf CLI 就绪' if ok
              else '❌ 安装失败，请手动运行: pip install -U "huggingface_hub[cli]"')
    return ok

def ensure_hf_transfer(out):
    """确保 hf_transfer 已安装（开启后大文件传输显著加速）。"""
    if subprocess.run('pip show hf_transfer', shell=True, capture_output=True).returncode == 0:
        return True
    with out: print("⚙️ 正在安装 hf_transfer（传输加速）...")
    subprocess.run('pip install -q hf_transfer', shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = subprocess.run('pip show hf_transfer', shell=True, capture_output=True).returncode == 0
    with out: print("✅ hf_transfer 就绪" if ok else "⚠️ hf_transfer 安装失败，将以普通速度上传")
    return ok

def ensure_rclone(out):
    """确保 rclone 已安装（云盘同步，支持 OneDrive 等）。"""
    if subprocess.run('which rclone', shell=True, capture_output=True).returncode == 0:
        return True
    with out: print("⚙️ 正在安装 rclone ...")
    subprocess.run('curl -fsSL https://rclone.org/install.sh | bash', shell=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = subprocess.run('which rclone', shell=True, capture_output=True).returncode == 0
    with out: print("✅ rclone 就绪" if ok
                    else "❌ 安装失败，请手动: curl https://rclone.org/install.sh | sudo bash")
    return ok

def rclone_remotes():
    """列出 rclone 已配置的网盘名（去掉冒号）。"""
    r = subprocess.run('rclone listremotes', shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        return []
    return [x.strip().rstrip(':') for x in r.stdout.split('\n') if x.strip()]

HF_API_TYPES = {'model': 'models', 'dataset': 'datasets', 'space': 'spaces'}

def hf_list_files(repo_id, repo_type='model', token=None, endpoint='https://huggingface.co'):
    api_seg = HF_API_TYPES.get(repo_type, 'models')
    url = f"{endpoint.rstrip('/')}/api/{api_seg}/{repo_id}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "comfydeck/1.0")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return [s["rfilename"] for s in data.get("siblings", [])]


# ─────────────────────────────────────────────
# Python 解释器探测 & 虚拟环境
# ─────────────────────────────────────────────
def detect_pythons():
    """扫描系统可用的 Python 解释器，返回 [(label, cmd), ...]，按版本号去重。"""
    candidates = ['python3.13', 'python3.12', 'python3.11', 'python3.10',
                  'python3.9', 'python3', 'python']
    found, seen = [], set()
    for c in candidates:
        r = subprocess.run(f'{c} --version', shell=True, capture_output=True, text=True)
        if r.returncode == 0:
            ver = (r.stdout + r.stderr).strip()      # 如 "Python 3.12.3"
            if ver in seen:
                continue
            seen.add(ver)
            found.append((f'{c}  ({ver})', c))
    return found

def pick_default_python(found):
    """从 detect_pythons() 结果挑默认：优先 3.12 / 3.11 / 3.10，否则第一个。"""
    for pref in ('3.12', '3.11', '3.10'):
        for label, cmd in found:
            if pref in label:
                return cmd
    return found[0][1] if found else 'python3'

def venv_dir(comfy_path):
    """虚拟环境目录：<ComfyUI>/venv"""
    return os.path.join(comfy_path, 'venv')

def venv_python(comfy_path):
    """虚拟环境内的 python 可执行文件（Linux: <ComfyUI>/venv/bin/python）"""
    return os.path.join(venv_dir(comfy_path), 'bin', 'python')

def runtime_python(comfy_path):
    """venv 内 python（带引号）；无 venv 时回退 python3。供装依赖用。"""
    vp = venv_python(comfy_path)
    return f'"{vp}"' if os.path.exists(vp) else 'python3'

def comfy_pidfile(comfy_path):
    return os.path.join(comfy_path, 'comfyui.pid')

def read_running_pid(comfy_path):
    """读 pid 文件，返回仍存活的 PID，否则 None（顺带清理失效的 pid 文件）。"""
    pf = comfy_pidfile(comfy_path)
    if not os.path.exists(pf):
        return None
    try:
        pid = int(open(pf).read().strip())
        os.kill(pid, 0)   # 不抛异常 = 进程存活
        return pid
    except (ValueError, OSError):
        return None


# ─────────────────────────────────────────────
# 工作流（workflow json）解析
# ─────────────────────────────────────────────
# 模型文件扩展名
MODEL_EXTS = ('.safetensors', '.ckpt', '.pt', '.pth', '.bin', '.gguf',
              '.onnx', '.sft', '.vae', '.pkl', '.npz')

# API 格式 inputs 字段名 → 模型目录
MODEL_FIELD_DIRS = {
    'ckpt_name': 'checkpoints', 'vae_name': 'vae',
    'lora_name': 'loras', 'unet_name': 'unet',
    'clip_name': 'clip', 'clip_name1': 'clip', 'clip_name2': 'clip', 'clip_name3': 'clip',
    'control_net_name': 'controlnet', 'controlnet_name': 'controlnet',
    'style_model_name': 'style_models', 'upscale_model_name': 'upscale_models',
    'clip_vision_name': 'clip_vision', 'gligen_name': 'gligen',
    'photomaker_model_name': 'photomaker',
}

# 节点 class_type → 模型目录（UI 格式归类主用）
NODE_TYPE_DIRS = {
    'CheckpointLoaderSimple': 'checkpoints', 'CheckpointLoader': 'checkpoints',
    'unCLIPCheckpointLoader': 'checkpoints', 'ImageOnlyCheckpointLoader': 'checkpoints',
    'VAELoader': 'vae',
    'LoraLoader': 'loras', 'LoraLoaderModelOnly': 'loras',
    'UNETLoader': 'unet', 'UnetLoaderGGUF': 'unet', 'UnetLoaderGGUFAdvanced': 'unet',
    'CLIPLoader': 'clip', 'DualCLIPLoader': 'clip', 'TripleCLIPLoader': 'clip',
    'CLIPLoaderGGUF': 'clip', 'DualCLIPLoaderGGUF': 'clip',
    'ControlNetLoader': 'controlnet', 'ControlNetLoaderAdvanced': 'controlnet',
    'DiffControlNetLoader': 'controlnet',
    'CLIPVisionLoader': 'clip_vision',
    'StyleModelLoader': 'style_models',
    'UpscaleModelLoader': 'upscale_models',
    'GLIGENLoader': 'gligen',
    'PhotoMakerLoader': 'photomaker',
}

def _is_model_str(s):
    return isinstance(s, str) and s.lower().endswith(MODEL_EXTS)

def analyze_workflow(data):
    """解析 ComfyUI 工作流 dict，返回 {'fmt','nodes','models'}。
    fmt    : 'ui' | 'api' | 'unknown'
    nodes  : [(class_type, count), ...]   按次数降序
    models : [{'name','dir','node'}, ...] 已去重，按目录+名称排序"""
    node_counts = {}
    models = {}          # (name, dir) -> node

    def add_node(t):
        if t:
            node_counts[t] = node_counts.get(t, 0) + 1

    def add_model(name, mdir, node):
        if name:
            models.setdefault((name, mdir), node)

    if isinstance(data, dict) and isinstance(data.get('nodes'), list):
        fmt = 'ui'
        for n in data['nodes']:
            if not isinstance(n, dict):
                continue
            t = n.get('type')
            add_node(t)
            wv = n.get('widgets_values')
            vals = wv.values() if isinstance(wv, dict) else (wv if isinstance(wv, list) else [])
            for v in vals:
                if _is_model_str(v):
                    add_model(v, NODE_TYPE_DIRS.get(t, '?'), t)
    elif isinstance(data, dict) and any(
            isinstance(v, dict) and 'class_type' in v for v in data.values()):
        fmt = 'api'
        for node in data.values():
            if not isinstance(node, dict):
                continue
            ct = node.get('class_type')
            add_node(ct)
            inputs = node.get('inputs', {})
            if isinstance(inputs, dict):
                for k, v in inputs.items():
                    if isinstance(v, str) and (k in MODEL_FIELD_DIRS or _is_model_str(v)):
                        mdir = MODEL_FIELD_DIRS.get(k) or NODE_TYPE_DIRS.get(ct, '?')
                        add_model(v, mdir, ct)
    else:
        fmt = 'unknown'

    nodes_sorted = sorted(node_counts.items(), key=lambda x: (-x[1], x[0]))
    models_list = [{'name': k[0], 'dir': k[1], 'node': v} for k, v in models.items()]
    models_list.sort(key=lambda m: (m['dir'], m['name']))
    return {'fmt': fmt, 'nodes': nodes_sorted, 'models': models_list}

def read_upload(upload):
    """兼容 ipywidgets 7/8 的 FileUpload.value，返回 (filename, text)；无文件返回 (None, None)。"""
    val = upload.value
    if not val:
        return None, None
    if isinstance(val, dict):                 # ipywidgets 7: {filename: {'content': bytes}}
        name = next(iter(val))
        content = val[name].get('content')
    else:                                      # ipywidgets 8: (dict, ...)
        item = val[0]
        name = item.get('name')
        content = item.get('content')
    if isinstance(content, memoryview):
        content = content.tobytes()
    if isinstance(content, (bytes, bytearray)):
        content = content.decode('utf-8')
    return name, content

def scan_local_models(comfy_path):
    """收集 <comfy_path>/models 下所有文件 basename 到 set；models 目录不存在返回 None。"""
    mroot = os.path.join(comfy_path, 'models')
    if not os.path.isdir(mroot):
        return None
    names = set()
    for _root, _dirs, files in os.walk(mroot):
        names.update(files)
    return names

def list_local_models(comfy_path):
    """列出 <comfy_path>/models 下所有模型文件，返回 [{'full','rel','size'}]；models 不存在返回 None。"""
    mroot = os.path.join(comfy_path, 'models')
    if not os.path.isdir(mroot):
        return None
    items = []
    for root, _dirs, files in os.walk(mroot):
        for f in files:
            if f.lower().endswith(MODEL_EXTS):
                full = os.path.join(root, f)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                items.append({'full': full,
                              'rel': os.path.relpath(full, mroot).replace('\\', '/'),
                              'size': size})
    items.sort(key=lambda x: x['rel'])
    return items

def human_size(n):
    """字节数转可读字符串。"""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"

def fetch_node_map(out, mirror=False):
    """拉取 ComfyUI-Manager 的 extension-node-map.json（节点→仓库映射），失败返回 None。"""
    base = 'https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main/extension-node-map.json'
    url = ('https://ghfast.top/' + base) if mirror else base
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'comfydeck/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        with out: print(f"❌ 拉取节点映射失败：{e}")
        return None

def build_node_index(node_map):
    """节点类名 -> 仓库 URL（取第一个匹配）。"""
    idx = {}
    for repo, val in node_map.items():
        names = val[0] if isinstance(val, list) and val and isinstance(val[0], list) else []
        for n in names:
            if n not in idx:
                idx[n] = repo
    return idx

def github_clone_url(u):
    """从映射 key 提取 (clone_url, 目录名)；非 github 返回 (None, None)。"""
    if 'github.com/' in u:
        parts = u.split('github.com/')[-1].split('/')
        if len(parts) >= 2:
            user, repo = parts[0], parts[1].replace('.git', '')
            return f'https://github.com/{user}/{repo}.git', repo
    return None, None

def clone_and_install_node(url, nodes_dir, py, out):
    """git clone 节点仓库到 nodes_dir 并装依赖（install.py / requirements.txt）。返回 True/False。"""
    name = url.rstrip('/').split('/')[-1].replace('.git', '')
    dest = os.path.join(nodes_dir, name)
    if os.path.isdir(dest):
        with out: print(f"  ⏭ {name} 已存在，跳过克隆")
    else:
        with out: print(f"  📦 克隆 {name} ...")
        r = subprocess.run(f'git clone --depth 1 {shlex.quote(url)} {shlex.quote(dest)}', shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if r.returncode != 0:
            with out: print(f"  ❌ 克隆失败：\n{r.stdout}")
            return False
        with out: print(f"  ✅ 克隆完成")
    install_py = os.path.join(dest, 'install.py')
    req = os.path.join(dest, 'requirements.txt')
    if os.path.exists(install_py):
        with out: print(f"  ⚙️ 运行 install.py ...")
        stream_exec(f'cd "{dest}" && {py} install.py', out, indent='    ')
    if os.path.exists(req):
        with out: print(f"  ⚙️ 安装 requirements.txt ...")
        stream_exec(f'{py} -m pip install -r "{req}"', out, indent='    ')
    if not os.path.exists(install_py) and not os.path.exists(req):
        with out: print(f"  ℹ️ 无需额外依赖")
    return True


# ═══════════════════════════════════════════════════════
# Tab 1：直链下载器（任务列表版）
# ═══════════════════════════════════════════════════════
def make_downloader_tab():

    header = widgets.HTML("""
        <div class="tool-header">▼ 云绕直链下载器（适用于大部分网站）</div>
        <div class="tool-tip">提示：使用 aria2c 下载，支持断点续传、16线程加速、批量下载</div>
        <div class="tool-tip2">每条任务独立指定下载目录，点击「+ 添加任务」增加条目</div>
    """)

    # ── ComfyUI 基础路径（自动探测）──
    row_base, base_path_input = make_path_row()

    # ── 全局选项 ──
    cb_token     = widgets.Checkbox(value=False, description='使用 Token', indent=False,
                                    layout=widgets.Layout(width='130px'))
    cb_overwrite = widgets.Checkbox(value=False, description='强行覆盖',   indent=False,
                                    layout=widgets.Layout(width='110px'))
    row_opts = widgets.HBox([cb_token, cb_overwrite], layout=widgets.Layout(margin='4px 0'))

    token_input   = widgets.Text(placeholder='Bearer Token (hf_xxx …)',
                                 layout=widgets.Layout(width='500px'))
    row_token_val = widgets.HBox([lbl('Token:'), token_input])
    token_area    = widgets.VBox([])

    def toggle_token(change=None):
        token_area.children = [row_token_val] if cb_token.value else []
    cb_token.observe(toggle_token, names='value')

    # ── 任务列表 ──
    # 表头
    col_widths = {'dir': '180px', 'sub': '130px', 'url': '310px'}

    task_header = widgets.HTML(f"""
    <div style="display:flex;align-items:center;padding:5px 8px;
                background:#2a2e47;border-radius:4px 4px 0 0;
                font-size:12px;color:#7f8bb0;border-bottom:1px solid #363b54;
                box-sizing:border-box;">
      <span style="width:{col_widths['dir']};flex-shrink:0;">下载目录（模型类型）</span>
      <span style="width:{col_widths['sub']};flex-shrink:0;margin-left:6px;">二级目录（可选）</span>
      <span style="width:{col_widths['url']};flex-shrink:0;margin-left:6px;">下载链接</span>
      <span style="width:32px;"></span>
    </div>""")

    tasks_vbox = widgets.VBox([], layout=widgets.Layout(
        border='1px solid #363b54', border_radius='0 0 4px 4px'))

    def make_task_row():
        """创建一行任务控件"""
        dir_dd = widgets.Dropdown(
            options=COMFY_MODEL_DIRS_WITH_CUSTOM, value='checkpoints',
            layout=widgets.Layout(width=col_widths['dir'])
        )
        # 自定义目录输入框（默认隐藏）
        custom_dir_txt = widgets.Text(
            placeholder='输入目录名，如 my_models',
            layout=widgets.Layout(width=col_widths['dir'], display='none')
        )
        sub_txt = widgets.Text(
            placeholder='可选，如 flux',
            layout=widgets.Layout(width=col_widths['sub'])
        )
        url_txt = widgets.Text(
            placeholder='粘贴下载链接，如 https://example.com/model.safetensors',
            layout=widgets.Layout(width=col_widths['url'])
        )
        del_btn = widgets.Button(
            description='✕',
            layout=widgets.Layout(width='32px', height='32px'),
            style={'button_color': '#ef4444', 'font_weight': 'bold'}
        )

        def on_dir_change(change=None):
            if dir_dd.value == '自定义目录...':
                dir_dd.layout.display = 'none'
                custom_dir_txt.layout.display = ''
            else:
                dir_dd.layout.display = ''
                custom_dir_txt.layout.display = 'none'
        dir_dd.observe(on_dir_change, names='value')

        # 自定义框按 Enter / 失焦时切回下拉（显示已输入内容作为提示）
        def on_custom_blur(change=None):
            val = custom_dir_txt.value.strip()
            if not val:          # 用户清空了 → 回到下拉
                custom_dir_txt.layout.display = 'none'
                dir_dd.layout.display = ''
                dir_dd.value = 'checkpoints'
        custom_dir_txt.observe(on_custom_blur, names='value')

        row = widgets.HBox(
            [dir_dd, custom_dir_txt, sub_txt, url_txt, del_btn],
            layout=widgets.Layout(
                padding='5px 8px', gap='6px',
                border_bottom='1px solid #363b54',
                align_items='center'
            )
        )
        # 暴露一个方法给下载逻辑使用
        def get_dir():
            if dir_dd.layout.display == 'none':
                return custom_dir_txt.value.strip() or 'checkpoints'
            return dir_dd.value
        row._get_dir = get_dir
        row._get_url = lambda: url_txt.value.strip()
        row._get_sub = lambda: sub_txt.value.strip()

        def on_delete(b):
            current = list(tasks_vbox.children)
            if row in current:
                current.remove(row)
                tasks_vbox.children = current
        del_btn.on_click(on_delete)
        return row

    def add_task(b=None):
        tasks_vbox.children = list(tasks_vbox.children) + [make_task_row()]

    # 初始添加一条
    add_task()

    btn_add = widgets.Button(
        description='+ 添加任务',
        layout=widgets.Layout(width='120px', height='32px'),
        style={'button_color': '#374151'}
    )
    btn_add.on_click(add_task)

    # ── 下载按钮 & 输出 ──
    btn_dl = widgets.Button(
        description='开始下载',
        layout=widgets.Layout(width='120px', height='34px'),
        style={'button_color': '#00bcd4'}
    )
    out = widgets.Output(layout=widgets.Layout(
        width=W, border='1px solid #363b54', min_height='60px', max_height='300px',
        overflow='auto', padding='6px', margin='6px 0 0 0'
    ))

    def on_download(b):
        out.clear_output()
        base = base_path_input.value.strip().rstrip('/')

        # 收集任务
        tasks = []
        for row in tasks_vbox.children:
            url = row._get_url()
            if not url:
                continue
            model_dir = row._get_dir()
            sub       = row._get_sub()
            # 拼接完整目录
            dest = os.path.join(base, 'models', model_dir)
            if sub:
                dest = os.path.join(dest, sub)
            tasks.append((url, dest))

        if not tasks:
            with out: print("⚠️ 请至少填写一条下载链接")
            return
        if not ensure_aria2c(out):
            return

        hdr = (f'--header="Authorization: Bearer {token_input.value.strip()}"'
               if cb_token.value and token_input.value.strip() else '')
        ow  = ('--allow-overwrite=true --auto-file-renaming=false'
               if cb_overwrite.value else '--auto-file-renaming=false')

        def _dl():
            for url, dest in tasks:
                os.makedirs(dest, exist_ok=True)
                cmd = f'aria2c -c -x 16 -s 16 {hdr} {ow} --dir={shlex.quote(dest)} {shlex.quote(url)}'
                with out:
                    print(f"▶ {url}")
                    print(f"  → {dest}")
                    print('─' * 60)
                rc = stream_exec(cmd, out)
                with out:
                    print("\n✅ 完成\n" if rc == 0
                          else f"\n❌ 失败 (退出码 {rc})\n")
        run_async(_dl, btn_dl)

    btn_dl.on_click(on_download)

    return widgets.VBox([
        header,
        row_base,
        widgets.HTML('<div style="height:6px"></div>'),
        task_header,
        tasks_vbox,
        widgets.HBox([btn_add], layout=widgets.Layout(margin='6px 0')),
        widgets.HTML('<div style="height:2px;border-top:1px solid #363b54;margin:4px 0"></div>'),
        row_opts,
        token_area,
        btn_dl,
        out,
    ], layout=widgets.Layout(padding='12px'))


# ═══════════════════════════════════════════════════════
# Tab 2：HuggingFace 仓库克隆
# ═══════════════════════════════════════════════════════
def make_hf_tab():

    header = widgets.HTML("""
        <div class="tool-header">▼ HuggingFace 仓库克隆</div>
        <div class="tool-tip">提示：支持克隆模型 / App空间 / 数据集，支持断点续传</div>
        <div class="tool-tip2">如遇网络超时，勾选下方「使用 HF 镜像」即可走国内 hf-mirror.com 加速</div>
    """)

    # ── ComfyUI 基础路径（自动探测）──
    row_base, base_path_input = make_path_row()

    # ── 仓库地址 ──
    repo_url_input = widgets.Text(
        placeholder='https://huggingface.co/用户名/仓库名  或  用户名/仓库名',
        layout=widgets.Layout(width='560px'))
    row_url = widgets.HBox([lbl('仓库地址:'), repo_url_input])

    # ── 下载目录（模型类型）+ 二级目录 ──
    dir_dd = widgets.Dropdown(
        options=COMFY_MODEL_DIRS_WITH_CUSTOM, value='checkpoints',
        layout=widgets.Layout(width='200px'))
    custom_dir_txt = widgets.Text(
        placeholder='输入目录名，如 my_models',
        layout=widgets.Layout(width='200px', display='none'))
    sub_txt = widgets.Text(
        placeholder='可选，如 flux',
        layout=widgets.Layout(width='160px'))

    def on_hf_dir_change(change=None):
        if dir_dd.value == '自定义目录...':
            dir_dd.layout.display = 'none'
            custom_dir_txt.layout.display = ''
        else:
            dir_dd.layout.display = ''
            custom_dir_txt.layout.display = 'none'
        update_preview()
    dir_dd.observe(on_hf_dir_change, names='value')
    custom_dir_txt.observe(lambda c: update_preview(), names='value')

    def get_hf_dir():
        if dir_dd.layout.display == 'none':
            return custom_dir_txt.value.strip() or 'checkpoints'
        return dir_dd.value

    row_dir = widgets.HBox([lbl('下载目录:'), dir_dd, custom_dir_txt,
                            widgets.Label('  二级目录:', layout=widgets.Layout(width='70px')),
                            sub_txt])

    # ── 克隆模式 ──
    clone_mode = widgets.Dropdown(
        options=['克隆整个仓库', '仅允许以下文件', '排除以下文件'],
        value='克隆整个仓库',
        layout=widgets.Layout(width='220px'))
    row_mode = widgets.HBox([lbl('克隆模式:'), clone_mode])

    filenames_input = widgets.Textarea(
        placeholder='每行填写一个文件名，如：\nmodel.safetensors\nconfig.json',
        layout=widgets.Layout(width='560px', height='90px'))
    row_files  = widgets.HBox([lbl('文件名:'), filenames_input])
    files_area = widgets.VBox([])

    def toggle_files(change=None):
        files_area.children = [row_files] if clone_mode.value != '克隆整个仓库' else []
    clone_mode.observe(toggle_files, names='value')

    # ── 选项 ──
    cb_subfolder = widgets.Checkbox(value=False, description='创建仓库名独立子文件夹',
                                    indent=False, layout=widgets.Layout(width='200px'))
    cb_token     = widgets.Checkbox(value=False, description='使用 HuggingFace Token',
                                    indent=False, layout=widgets.Layout(width='200px'))
    cb_overwrite = widgets.Checkbox(value=False, description='强行覆盖',
                                    indent=False, layout=widgets.Layout(width='110px'))
    cb_mirror    = widgets.Checkbox(value=False, description='使用 HF 镜像(hf-mirror)',
                                    indent=False, layout=widgets.Layout(width='220px'))
    cb_align     = widgets.Checkbox(value=False, description='整仓对齐下载（下到 ComfyUI 根）',
                                    indent=False, layout=widgets.Layout(width='280px'))
    row_opts = widgets.HBox([cb_subfolder, cb_token, cb_overwrite, cb_mirror, cb_align],
                            layout=widgets.Layout(margin='4px 0', flex_flow='row wrap'))

    def get_endpoint():
        return 'https://hf-mirror.com' if cb_mirror.value else 'https://huggingface.co'

    token_input   = widgets.Text(placeholder='hf_xxxxxxxxxxxxxxxxxxxx',
                                 layout=widgets.Layout(width='560px'))
    row_token_val = widgets.HBox([lbl('填写Token:'), token_input])
    token_area    = widgets.VBox([])

    def toggle_token(change=None):
        token_area.children = [row_token_val] if cb_token.value else []
    cb_token.observe(toggle_token, names='value')

    # ── 目标路径预览 ──
    path_preview = widgets.HTML('')

    def update_preview(change=None):
        base = base_path_input.value.strip().rstrip('/')
        if cb_align.value:
            path_preview.value = (
                f'<div style="font-size:12px;color:#7f8bb0;margin:2px 0 6px {LBSW};">'
                f'整仓对齐下载到：<span style="color:#4fc3f7">{base}</span>'
                f' <span style="color:#7f8bb0;">（仓库内 models/… 自动归位，已忽略上方目录选择）</span></div>'
            )
            return
        model_dir = get_hf_dir()
        sub = sub_txt.value.strip()
        dest = os.path.join(base, 'models', model_dir)
        if sub:
            dest = os.path.join(dest, sub)
        path_preview.value = (
            f'<div style="font-size:12px;color:#7f8bb0;margin:2px 0 6px {LBSW};">'
            f'下载到：<span style="color:#4fc3f7">{dest}</span></div>'
        )

    base_path_input.observe(update_preview, names='value')
    # dir_dd 和 custom_dir_txt 已在 on_hf_dir_change 中触发 update_preview
    sub_txt.observe(update_preview, names='value')

    def on_align_change(change=None):
        # 对齐模式下隐藏「下载目录」行（直接下到 ComfyUI 根）
        row_dir.layout.display = 'none' if cb_align.value else ''
        update_preview()
    cb_align.observe(on_align_change, names='value')
    update_preview()

    # ── 按钮 ──
    btn_parse = widgets.Button(description='1. 解析仓库',
                               layout=widgets.Layout(width='130px', height='34px'),
                               style={'button_color': '#3b82f6'})
    btn_dl    = widgets.Button(description='2. 确认下载',
                               layout=widgets.Layout(width='130px', height='34px'),
                               style={'button_color': '#00bcd4'})
    row_btns = widgets.HBox([btn_parse, btn_dl],
                            layout=widgets.Layout(gap='10px', margin='6px 0'))

    out = widgets.Output(layout=widgets.Layout(
        width=W, border='1px solid #363b54', min_height='60px', max_height='320px',
        overflow='auto', padding='6px', margin='4px 0 0 0'))

    _state = {'repo_id': None, 'repo_type': 'model'}

    def get_repo_id(raw):
        """解析为 (repo_id, repo_type)；无法解析返回 (None, None)。
        支持 https://huggingface.co/[datasets|spaces/]user/repo、
        datasets/user/repo、spaces/user/repo、user/repo"""
        raw = raw.strip().rstrip('/')
        if not raw:
            return None, None
        if 'huggingface.co/' in raw:
            tail = raw.split('huggingface.co/')[-1]
        elif raw.startswith('http'):
            return None, None          # 非 HuggingFace 的 http 链接
        else:
            tail = raw
        parts = [p for p in tail.split('/') if p]
        repo_type = 'model'
        if parts and parts[0] in ('datasets', 'spaces'):
            repo_type = 'dataset' if parts[0] == 'datasets' else 'space'
            parts = parts[1:]
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}", repo_type
        return None, None

    def build_dest():
        base = base_path_input.value.strip().rstrip('/')
        if cb_align.value:
            return base   # 整仓对齐：下到 ComfyUI 根，仓库内 models/… 自动归位
        sub  = sub_txt.value.strip()
        dest = os.path.join(base, 'models', get_hf_dir())
        if sub:
            dest = os.path.join(dest, sub)
        return dest

    def on_parse(b):
        out.clear_output()
        raw = repo_url_input.value.strip()
        if not raw:
            with out: print("⚠️ 请填写仓库地址"); return
        repo_id, repo_type = get_repo_id(raw)
        if not repo_id:
            with out: print("❌ 无法解析仓库地址，请检查格式"); return

        token = token_input.value.strip() if cb_token.value else None
        type_label = {'model': '模型', 'dataset': '数据集', 'space': 'App空间'}[repo_type]
        with out: print(f"🔍 正在请求{type_label}仓库信息：{repo_id} ...")

        def _fetch():
            try:
                files = hf_list_files(repo_id, repo_type, token, get_endpoint())
                _state['repo_id']   = repo_id
                _state['repo_type'] = repo_type
                dest = build_dest()
                if cb_subfolder.value and not cb_align.value:
                    dest = os.path.join(dest, repo_id.split('/')[-1])
                with out:
                    out.clear_output()
                    print(f"✅ 解析成功：{repo_id}（{type_label}）")
                    print(f"克隆模式：{clone_mode.value}")
                    print(f"下载到：{dest}")
                    if token:
                        print(f"🔑 Token: {token[:8]}***")
                    print(f"\n{'─'*50}")
                    print(f"仓库共 {len(files)} 个文件：")
                    for f in files:
                        print(f"  📄 {f}")
            except Exception as e:
                with out:
                    out.clear_output()
                    print(f"❌ 解析失败：{e}")
                    print("提示：私有仓库需要勾选「使用 Token」并填写 Token")
        run_async(_fetch, btn_parse)

    def on_confirm(b):
        out.clear_output()
        repo_id   = _state.get('repo_id')
        repo_type = _state.get('repo_type', 'model')
        if not repo_id:
            with out: print("⚠️ 请先点击「解析仓库」并等待解析完成"); return
        if not ensure_hf_cli(out):
            return

        token = token_input.value.strip() if cb_token.value else ''
        dest  = build_dest()
        if cb_subfolder.value and not cb_align.value:
            dest = os.path.join(dest, repo_id.split('/')[-1])
        os.makedirs(dest, exist_ok=True)

        cmd_parts = ['hf', 'download', shlex.quote(repo_id)]
        if repo_type != 'model':
            cmd_parts += ['--type', repo_type]
        if clone_mode.value == '仅允许以下文件':
            for f in [x.strip() for x in filenames_input.value.strip().split('\n') if x.strip()]:
                cmd_parts += ['--include', shlex.quote(f)]
        elif clone_mode.value == '排除以下文件':
            for f in [x.strip() for x in filenames_input.value.strip().split('\n') if x.strip()]:
                cmd_parts += ['--exclude', shlex.quote(f)]
        cmd_parts += ['--local-dir', shlex.quote(dest)]

        # token 经 HF_TOKEN、镜像经 HF_ENDPOINT 用环境变量传递，不进命令行
        cmd = ' '.join(cmd_parts)
        env = {'HF_ENDPOINT': get_endpoint()}
        if token:
            env['HF_TOKEN'] = token
        ep_note = '（镜像）' if cb_mirror.value else ''
        with out: print(f"▶ 执行{ep_note}：{cmd}\n{'─'*60}")
        run_stream(cmd, out, btn_parse, btn_dl, env=env)

    btn_parse.on_click(on_parse)
    btn_dl.on_click(on_confirm)

    return widgets.VBox([
        header,
        row_base,
        widgets.HTML('<div style="height:6px"></div>'),
        row_url,
        row_dir,
        path_preview,
        row_mode,
        files_area,
        row_opts,
        token_area,
        row_btns,
        out,
    ], layout=widgets.Layout(padding='12px'))


# ═══════════════════════════════════════════════════════
# Tab 3：ComfyUI 安装
# ═══════════════════════════════════════════════════════
def make_comfyui_tab():

    header = widgets.HTML("""
        <div class="tool-header">▼ ComfyUI 克隆 & 安装</div>
        <div class="tool-tip">提示：从 GitHub 克隆 ComfyUI 并自动安装依赖，支持自定义安装路径</div>
        <div class="tool-tip2">依赖与节点均安装在 &lt;ComfyUI&gt;/venv 虚拟环境中，避免污染主环境</div>
    """)

    # ── 安装路径 ──
    row_path, install_path = make_path_row(label='安装路径:')

    # ── Git 分支 ──
    branch_input = widgets.Text(
        value='master',
        layout=widgets.Layout(width='200px')
    )
    row_branch = widgets.HBox([lbl('分支:'), branch_input])

    # ── 基础 Python 解释器（仅用于创建虚拟环境）──
    _pythons = detect_pythons()
    py_dd = widgets.Dropdown(
        options=([(lb, cm) for lb, cm in _pythons] or [('未探测到 python', 'python3')]),
        value=pick_default_python(_pythons),
        layout=widgets.Layout(width='300px')
    )
    btn_py_redetect = widgets.Button(
        description='🔄 重新探测',
        layout=widgets.Layout(width='110px', height='28px'),
        style={'button_color': '#374151', 'font_size': '11px'}
    )
    def on_py_redetect(b):
        found = detect_pythons()
        py_dd.options = [(lb, cm) for lb, cm in found] or [('未探测到 python', 'python3')]
        py_dd.value = pick_default_python(found)
    btn_py_redetect.on_click(on_py_redetect)
    row_python = widgets.HBox([lbl('基础Python:'), py_dd, btn_py_redetect])

    # ── 安装 Python（系统缺 3.11/3.12 时，经 deadsnakes PPA 安装，仅 Ubuntu）──
    pyver_dd = widgets.Dropdown(
        options=[('Python 3.12', '3.12'), ('Python 3.11', '3.11')],
        value='3.12', layout=widgets.Layout(width='150px'))
    btn_install_py = widgets.Button(
        description='⬇ 安装此版本',
        layout=widgets.Layout(width='130px', height='28px'),
        style={'button_color': '#374151', 'font_size': '11px'})
    row_install_py = widgets.HBox([
        lbl('安装Python:'), pyver_dd, btn_install_py,
        widgets.HTML('<span style="font-size:11px;color:#7f8bb0;">&nbsp;系统缺 3.11/3.12 时用（仅 Ubuntu）</span>')
    ])

    # ── 虚拟环境状态（随安装路径联动）──
    venv_status = widgets.HTML('')
    def refresh_venv_status(change=None):
        path = install_path.value.strip().rstrip('/')
        vdir = venv_dir(path)
        if os.path.exists(venv_python(path)):
            mark = '<span style="color:#4CAF50">✅ 已就绪</span>'
        else:
            mark = '<span style="color:#f5a623">⚠️ 未创建（点「2. 创建虚拟环境」）</span>'
        venv_status.value = (
            f'<div style="font-size:12px;color:#7f8bb0;margin:2px 0;">'
            f'虚拟环境：<span style="color:#4fc3f7">{vdir}</span> &nbsp;{mark}</div>'
        )
    install_path.observe(refresh_venv_status, names='value')
    refresh_venv_status()
    row_venv_status = widgets.HBox([lbl(''), venv_status])

    # ── 安装选项 ──
    cb_torch        = widgets.Checkbox(value=True,  description='安装 PyTorch',
                                       indent=False, layout=widgets.Layout(width='120px'))
    cuda_dd         = widgets.Dropdown(
        options=[('CUDA 13.0（5090/最新）', 'cu130'), ('CUDA 12.8（40/50 系推荐）', 'cu128'),
                 ('CUDA 12.6', 'cu126'), ('CUDA 12.4', 'cu124')],
        value='cu128', layout=widgets.Layout(width='200px'))
    cb_xformers     = widgets.Checkbox(value=True,  description='安装 xformers',
                                       indent=False, layout=widgets.Layout(width='140px'))
    cb_deps         = widgets.Checkbox(value=True,  description='安装 requirements.txt',
                                       indent=False, layout=widgets.Layout(width='190px'))

    row_opts1 = widgets.HBox([cb_torch, cuda_dd, cb_xformers, cb_deps],
                             layout=widgets.Layout(margin='4px 0', flex_flow='row wrap'))

    # ── 检测当前 PyTorch / CUDA ──
    btn_check_torch = widgets.Button(
        description='🔎 检测当前 PyTorch / CUDA',
        layout=widgets.Layout(width='230px', height='30px'),
        style={'button_color': '#374151'})
    row_check = widgets.HBox([btn_check_torch], layout=widgets.Layout(margin='2px 0'))

    # ── 自定义节点 ──
    CUSTOM_NODES = {
        'ComfyUI-Manager':       'https://github.com/ltdrdata/ComfyUI-Manager.git',
        'ComfyUI-GGUF':          'https://github.com/city96/ComfyUI-GGUF.git',
        'ComfyUI-Impact-Pack':   'https://github.com/ltdrdata/ComfyUI-Impact-Pack.git',
        'rgthree-comfy':         'https://github.com/rgthree/rgthree-comfy.git',
        'ComfyUI_IPAdapter_plus':'https://github.com/cubiq/ComfyUI_IPAdapter_plus.git',
        'ComfyUI-VideoHelperSuite':'https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git',
        'ComfyUI-Advanced-ControlNet':'https://github.com/Kosinkadink/ComfyUI-Advanced-ControlNet.git',
        'efficiency-nodes-comfyui':'https://github.com/jags111/efficiency-nodes-comfyui.git',
    }

    node_checks = []
    node_rows   = []
    for name, url in CUSTOM_NODES.items():
        cb = widgets.Checkbox(value=False, description=name, indent=False,
                              layout=widgets.Layout(width='300px'))
        node_checks.append((cb, url))

    # 每两个排一行
    for i in range(0, len(node_checks), 2):
        pair = [node_checks[i][0]]
        if i + 1 < len(node_checks):
            pair.append(node_checks[i+1][0])
        node_rows.append(widgets.HBox(pair))

    nodes_section = widgets.VBox([
        widgets.HTML('<div style="font-size:12px;color:#7f8bb0;margin:8px 0 4px 0;">📦 自定义节点（可选）：</div>'),
        *node_rows
    ])

    # ── 分隔线 ──
    divider = widgets.HTML('<div style="height:1px;background:#363b54;margin:10px 0;"></div>')

    # ── 按钮区 ──
    btn_clone   = widgets.Button(description='1. 克隆 ComfyUI',
                                 layout=widgets.Layout(width='150px', height='34px'),
                                 style={'button_color': '#3b82f6'})
    btn_venv    = widgets.Button(description='2. 创建虚拟环境',
                                 layout=widgets.Layout(width='150px', height='34px'),
                                 style={'button_color': '#3b82f6'})
    btn_install = widgets.Button(description='3. 安装依赖',
                                 layout=widgets.Layout(width='130px', height='34px'),
                                 style={'button_color': '#3b82f6'})
    btn_nodes   = widgets.Button(description='4. 安装自定义节点',
                                 layout=widgets.Layout(width='160px', height='34px'),
                                 style={'button_color': '#3b82f6'})
    btn_launch  = widgets.Button(description='▶ 启动 ComfyUI',
                                 layout=widgets.Layout(width='140px', height='34px'),
                                 style={'button_color': '#00bcd4'})
    btn_stop    = widgets.Button(description='■ 停止',
                                 layout=widgets.Layout(width='90px', height='34px'),
                                 style={'button_color': '#ef4444'})
    btn_log     = widgets.Button(description='📜 查看日志',
                                 layout=widgets.Layout(width='120px', height='34px'),
                                 style={'button_color': '#374151'})

    row_btns = widgets.HBox([btn_clone, btn_venv, btn_install, btn_nodes, btn_launch, btn_stop, btn_log],
                            layout=widgets.Layout(gap='8px', margin='8px 0', flex_flow='row wrap'))

    # ── 输出 ──
    out = widgets.Output(layout=widgets.Layout(
        width=W, border='1px solid #363b54', min_height='80px', max_height='400px',
        overflow='auto', padding='8px', margin='6px 0 0 0'
    ))

    # ── 状态指示 ──
    status_html = widgets.HTML('')

    def set_status(msg, color='#4fc3f7'):
        status_html.value = (
            f'<div style="font-size:12px;color:{color};margin:4px 0;">{msg}</div>'
        )

    # ── 逻辑 ──
    def get_path():
        return install_path.value.strip().rstrip('/')

    def get_python():
        """优先返回 venv 内解释器（带引号）；无 venv 时回退基础解释器下拉值。"""
        vp = venv_python(get_path())
        if os.path.exists(vp):
            return f'"{vp}"'
        return py_dd.value or 'python3'

    def on_clone(b):
        out.clear_output()
        path   = get_path()
        branch = branch_input.value.strip() or 'master'

        if os.path.isdir(os.path.join(path, '.git')):
            with out:
                print(f"⚠️  {path} 已存在 git 仓库，跳过克隆")
                print("如需重新克隆，请先删除该目录")
            set_status(f'⚠️ 目录已存在，跳过克隆', '#f5a623')
            return

        parent = os.path.dirname(path)
        os.makedirs(parent, exist_ok=True)
        cmd = f'git clone -b {shlex.quote(branch)} --depth 1 https://github.com/comfyanonymous/ComfyUI.git {shlex.quote(path)}'
        with out:
            print(f"▶ 克隆 ComfyUI → {path}")
            print(f"  分支: {branch}\n{'─'*60}")
        set_status('⏳ 正在克隆...', '#f5a623')

        def _done(rc):
            if rc == 0: set_status('✅ 克隆完成', '#4CAF50')
            else:       set_status('❌ 克隆失败', '#ef5350')
        run_stream(cmd, out, btn_clone, on_done=_done)

    def on_venv(b):
        out.clear_output()
        path = get_path()
        if not os.path.isdir(path):
            with out: print(f"❌ 目录不存在：{path}\n请先执行「1. 克隆 ComfyUI」")
            return
        base_py = py_dd.value or 'python3'
        vdir = venv_dir(path)
        vpy  = venv_python(path)

        if os.path.exists(vpy):
            with out: print(f"ℹ️  虚拟环境已存在：{vdir}\n如需重建请先删除该目录")
            set_status('✅ 虚拟环境已就绪', '#4CAF50')
            refresh_venv_status()
            return

        cmd = f'{base_py} -m venv "{vdir}" && "{vpy}" -m pip install -U pip'
        with out:
            print(f"▶ 创建虚拟环境 → {vdir}")
            print(f"  基础解释器: {base_py}\n{'─'*60}")
        set_status('⏳ 正在创建虚拟环境...', '#f5a623')

        def _done(rc):
            if rc == 0: set_status('✅ 虚拟环境创建完成', '#4CAF50')
            else:       set_status('❌ 虚拟环境创建失败', '#ef5350')
            refresh_venv_status()
        run_stream(cmd, out, btn_venv, on_done=_done)

    def on_install(b):
        out.clear_output()
        path   = get_path()
        py     = get_python()

        if not os.path.isdir(path):
            with out: print(f"❌ 目录不存在：{path}\n请先执行「1. 克隆 ComfyUI」")
            return
        if not os.path.exists(venv_python(path)):
            with out: print("❌ 未找到虚拟环境，请先执行「2. 创建虚拟环境」")
            return

        cmds = []
        if cb_torch.value:
            cmds.append(
                f'{py} -m pip install torch torchvision torchaudio '
                f'--index-url https://download.pytorch.org/whl/{cuda_dd.value}'
            )
        if cb_xformers.value:
            cmds.append(f'{py} -m pip install xformers')
        if cb_deps.value:
            req = os.path.join(path, 'requirements.txt')
            if os.path.exists(req):
                cmds.append(f'{py} -m pip install -r "{req}"')
            else:
                with out: print(f"⚠️  未找到 {req}，跳过")

        if not cmds:
            with out: print("⚠️  未选择任何安装项")
            return

        set_status('⏳ 正在安装依赖...', '#f5a623')
        full_cmd = ' && '.join(cmds)
        with out:
            print(f"▶ 安装依赖\n{'─'*60}")

        def _done(rc):
            if rc == 0: set_status('✅ 依赖安装完成', '#4CAF50')
            else:       set_status('❌ 安装出错', '#ef5350')
        run_stream(full_cmd, out, btn_install, on_done=_done)

    def on_nodes(b):
        out.clear_output()
        path = get_path()
        py   = get_python()
        nodes_dir = os.path.join(path, 'custom_nodes')

        if not os.path.isdir(path):
            with out: print(f"❌ 目录不存在：{path}\n请先执行「1. 克隆 ComfyUI」")
            return
        if not os.path.exists(venv_python(path)):
            with out: print("❌ 未找到虚拟环境，请先执行「2. 创建虚拟环境」")
            return

        selected = [(cb.description, url) for cb, url in node_checks if cb.value]
        if not selected:
            with out: print("⚠️  未勾选任何自定义节点")
            return

        os.makedirs(nodes_dir, exist_ok=True)
        set_status('⏳ 正在安装自定义节点...', '#f5a623')
        with out:
            print(f"▶ 安装 {len(selected)} 个自定义节点 → {nodes_dir}\n{'─'*60}")

        def _run():
            for name, url in selected:
                dest = os.path.join(nodes_dir, name)

                # ── 克隆 ──
                if os.path.isdir(dest):
                    with out: print(f"\n⏭  {name} 已存在，跳过克隆")
                else:
                    with out: print(f"\n{'─'*60}\n📦 克隆 {name} ...")
                    r = subprocess.run(
                        f'git clone --depth 1 "{url}" "{dest}"',
                        shell=True, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True
                    )
                    if r.returncode != 0:
                        with out:
                            print(f"  ❌ 克隆失败：")
                            print(r.stdout)
                        continue
                    with out: print(f"  ✅ 克隆完成")

                # ── 安装依赖：优先 install.py，否则 requirements.txt ──
                install_py = os.path.join(dest, 'install.py')
                req_txt    = os.path.join(dest, 'requirements.txt')

                if os.path.exists(install_py):
                    with out: print(f"  ⚙️  运行 install.py ...")
                    rc = stream_exec(f'cd "{dest}" && {py} install.py', out, indent='    ')
                    with out:
                        if rc == 0: print(f"  ✅ install.py 完成")
                        else:       print(f"  ⚠️  install.py 退出码 {rc}，继续尝试 requirements.txt")

                if os.path.exists(req_txt):
                    with out: print(f"  ⚙️  安装 requirements.txt ...")
                    rc = stream_exec(f'{py} -m pip install -r "{req_txt}"', out, indent='    ')
                    with out:
                        if rc == 0: print(f"  ✅ 依赖安装完成")
                        else:       print(f"  ❌ 依赖安装失败（退出码 {rc}）")
                elif not os.path.exists(install_py):
                    with out: print(f"  ℹ️  无需额外依赖")

            with out: print(f"\n{'─'*60}\n✅ 全部节点处理完毕！")
            set_status('✅ 自定义节点安装完成', '#4CAF50')
        run_async(_run, btn_nodes)

    _proc = {'p': None, 'log': None}

    def on_launch(b):
        out.clear_output()
        path = get_path()
        py   = get_python()
        main = os.path.join(path, 'main.py')

        if not os.path.exists(main):
            with out: print(f"❌ 未找到 {main}\n请先完成克隆和安装步骤")
            return
        if not os.path.exists(venv_python(path)):
            with out: print("❌ 未找到虚拟环境，请先执行「2. 创建虚拟环境」")
            return
        p = _proc.get('p')
        running = (p.pid if (p and p.poll() is None) else None) or read_running_pid(path)
        if running:
            with out: print(f"ℹ️ ComfyUI 已在后台运行（PID {running}），如需重启请先「■ 停止」")
            set_status(f'🟢 运行中（PID {running}）', '#4CAF50')
            return

        logf = os.path.join(path, 'comfyui.log')
        cmd = f'cd "{path}" && {py} main.py --listen 0.0.0.0 --port 8188'
        with out:
            print(f"▶ 后台启动 ComfyUI")
            print(f"  访问地址：http://<服务器IP>:8188")
            print(f"  日志文件：{logf}\n{'─'*60}")
        try:
            lf = open(logf, 'w')
            proc = subprocess.Popen(cmd, shell=True, stdout=lf, stderr=subprocess.STDOUT,
                                    preexec_fn=os.setsid)
            _proc['p'] = proc
            _proc['log'] = logf
            try:
                with open(comfy_pidfile(path), 'w') as pf:
                    pf.write(str(proc.pid))
            except OSError:
                pass
            with out: print(f"✅ 已在后台启动（PID {proc.pid}）；点「📜 查看日志」看启动进度")
            set_status(f'🟢 运行中（PID {proc.pid}）', '#4CAF50')
        except Exception as e:
            with out: print(f"❌ 启动失败：{e}")
            set_status('❌ 启动失败', '#ef5350')

    def on_stop(b):
        out.clear_output()
        path = get_path()
        p = _proc.get('p')
        pid = p.pid if (p and p.poll() is None) else read_running_pid(path)
        if not pid:
            with out: print("ℹ️ 当前没有运行中的 ComfyUI 进程")
            set_status('⚪ 已停止', '#7f8bb0')
            return
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception as e:
                with out: print(f"❌ 停止失败：{e}（可在终端手动 kill {pid}）")
                return
        _proc['p'] = None
        try:
            os.remove(comfy_pidfile(path))
        except OSError:
            pass
        with out: print(f"🛑 已停止 ComfyUI（PID {pid}）")
        set_status('⚪ 已停止', '#7f8bb0')

    def on_log(b):
        out.clear_output()
        logf = _proc.get('log') or os.path.join(get_path(), 'comfyui.log')
        if not os.path.exists(logf):
            with out: print(f"ℹ️ 暂无日志文件：{logf}")
            return
        p = _proc.get('p')
        running = '🟢 运行中' if (p and p.poll() is None) else '⚪ 未运行'
        with out:
            print(f"📜 {logf}  [{running}]\n{'─'*60}")
            try:
                with open(logf, 'r', errors='replace') as f:
                    tail = f.readlines()[-100:]
                for line in tail:
                    print(line, end='')
            except Exception as e:
                print(f"读取失败：{e}")

    def on_install_py(b):
        out.clear_output()
        ver = pyver_dd.value
        cmd = ('apt-get update && apt-get install -y software-properties-common && '
               'add-apt-repository ppa:deadsnakes/ppa -y && apt-get update && '
               f'apt-get install -y python{ver} python{ver}-venv python{ver}-dev')
        with out:
            print(f"▶ 安装 Python {ver}（deadsnakes PPA）")
            print("  注：依赖 Ubuntu + apt；其它系统请手动安装\n" + '─' * 60)
        set_status(f'⏳ 正在安装 Python {ver}...', '#f5a623')

        def _done(rc):
            if rc == 0:
                found = detect_pythons()
                py_dd.options = [(lb, cm) for lb, cm in found] or [('未探测到 python', 'python3')]
                for _lb, _cm in found:
                    if _cm == f'python{ver}':
                        py_dd.value = _cm
                        break
                with out: print(f"\n✅ Python {ver} 安装完成，已加入「基础Python」下拉并选中")
                set_status(f'✅ Python {ver} 已安装', '#4CAF50')
            else:
                with out: print(f"\n❌ 安装失败（退出码 {rc}）；该功能仅支持 Ubuntu")
                set_status('❌ Python 安装失败', '#ef5350')
        run_stream(cmd, out, btn_install_py, on_done=_done)

    def on_check_torch(b):
        out.clear_output()
        path = get_path()
        py   = get_python()
        where = 'venv' if os.path.exists(venv_python(path)) else '基础解释器'
        with out:
            print(f"🔎 检测 PyTorch / CUDA（{where}: {py}）\n{'─' * 60}")
        code = ('import torch;'
                'print("PyTorch 版本 :", torch.__version__);'
                'print("编译 CUDA   :", torch.version.cuda);'
                'print("CUDA 可用   :", torch.cuda.is_available());'
                'print("GPU         :", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "无/不可用")')

        def _run():
            chk = subprocess.run(f'{py} -c "import torch"', shell=True, capture_output=True)
            if chk.returncode != 0:
                with out: print("ℹ️  该环境尚未安装 PyTorch（请先用「3. 安装依赖」安装）")
                return
            stream_exec(f"{py} -c '{code}'", out)
        run_async(_run, btn_check_torch)

    btn_clone.on_click(on_clone)
    btn_venv.on_click(on_venv)
    btn_install.on_click(on_install)
    btn_nodes.on_click(on_nodes)
    btn_launch.on_click(on_launch)
    btn_stop.on_click(on_stop)
    btn_log.on_click(on_log)
    btn_install_py.on_click(on_install_py)
    btn_check_torch.on_click(on_check_torch)

    return widgets.VBox([
        header,
        row_path,
        row_branch,
        row_python,
        row_install_py,
        row_venv_status,
        divider,
        widgets.HTML('<div style="font-size:12px;color:#7f8bb0;margin:0 0 4px 0;">⚙️ 安装选项：</div>'),
        row_opts1,
        row_check,
        nodes_section,
        divider,
        row_btns,
        status_html,
        out,
    ], layout=widgets.Layout(padding='12px'))


# ═══════════════════════════════════════════════════════
# Tab 4：工作流分析（上传 json → 模型 & 节点）
# ═══════════════════════════════════════════════════════
def make_analyzer_tab():

    header = widgets.HTML("""
        <div class="tool-header">▼ 工作流分析（上传 json → 模型 & 节点）</div>
        <div class="tool-tip">提示：支持 UI 格式（普通保存）与 API 格式（Save API Format）两种工作流</div>
        <div class="tool-tip2">列出工作流用到的模型（含目录归类、本地是否存在）与全部节点</div>
    """)

    # ── ComfyUI 基础路径（自动探测，用于本地缺失检测）──
    row_base, base_path_input = make_path_row()

    # ── 上传工作流 ──
    uploader = widgets.FileUpload(accept='.json', multiple=False,
                                  description='选择工作流 json',
                                  layout=widgets.Layout(width='220px'))
    btn_analyze = widgets.Button(
        description='🔍 分析',
        layout=widgets.Layout(width='120px', height='34px'),
        style={'button_color': '#00bcd4'}
    )
    row_upload = widgets.HBox([lbl('工作流文件:'), uploader, btn_analyze],
                              layout=widgets.Layout(margin='6px 0', align_items='center', gap='8px'))

    out = widgets.Output(layout=widgets.Layout(
        width=W, border='1px solid #363b54', min_height='80px', max_height='420px',
        overflow='auto', padding='8px', margin='6px 0 0 0'
    ))

    _an = {'nodes': None}

    def on_analyze(b):
        out.clear_output()
        name, text = read_upload(uploader)
        if not text:
            with out: print("⚠️ 请先选择一个工作流 json 文件")
            return
        try:
            data = json.loads(text)
        except Exception as e:
            with out: print(f"❌ json 解析失败：{e}")
            return

        result = analyze_workflow(data)
        if result['fmt'] == 'unknown':
            with out: print("❌ 无法识别的工作流格式（既非 UI 格式也非 API 格式）")
            return

        local = scan_local_models(base_path_input.value.strip().rstrip('/'))
        fmt_label = {'ui': 'UI 格式', 'api': 'API 格式'}[result['fmt']]
        models = result['models']
        nodes  = result['nodes']
        _an['nodes'] = [t for t, _c in nodes]

        with out:
            print(f"📄 文件：{name}    格式：{fmt_label}")
            print('═' * 64)

            # 模型
            print(f"📦 模型（{len(models)} 个）")
            print('─' * 64)
            if not models:
                print("  （未发现模型引用）")
            else:
                missing = []
                for m in models:
                    basename = m['name'].replace('\\', '/').split('/')[-1]
                    if local is None:
                        mark = '  '
                    elif basename in local:
                        mark = '✅'
                    else:
                        mark = '❌'; missing.append(m)
                    print(f"  {mark} {m['dir']}/  {m['name']}   [{m['node']}]")
                if local is None:
                    print("\n  ⚠️ 未找到本地 models 目录，跳过缺失检测（请确认 ComfyUI 路径）")
                elif missing:
                    print(f"\n  ❌ 本地缺失 {len(missing)} 个：")
                    for m in missing:
                        print(f"     {m['dir']}/{m['name']}")
                else:
                    print("\n  ✅ 全部模型本地已存在")

            # 节点
            total = sum(c for _, c in nodes)
            print(f"\n🧩 节点（{len(nodes)} 种 / {total} 个）")
            print('─' * 64)
            for t, c in nodes:
                print(f"  {t}  ×{c}")

    btn_analyze.on_click(on_analyze)

    # ── 缺失节点安装（基于 ComfyUI-Manager 节点→仓库映射）──
    sec_nodes = widgets.HTML('<div class="ctk-section">🧩 缺失节点安装</div>')
    btn_identify = widgets.Button(description='🧩 识别工作流节点',
                                  layout=widgets.Layout(width='160px', height='32px'),
                                  style={'button_color': '#374151'})
    cb_node_mirror = widgets.Checkbox(value=False, description='用 GitHub 镜像', indent=False,
                                      layout=widgets.Layout(width='150px'))
    row_node1 = widgets.HBox([btn_identify, cb_node_mirror],
                             layout=widgets.Layout(gap='8px', margin='4px 0', align_items='center'))
    nodes_box = widgets.VBox([], layout=widgets.Layout(
        border='1px solid #363b54', border_radius='6px', max_height='220px', overflow='auto',
        padding='6px', margin='4px 0'))
    btn_install_sel = widgets.Button(description='⬇ 安装勾选节点',
                                     layout=widgets.Layout(width='150px', height='32px'),
                                     style={'button_color': '#3b82f6'})
    manual_url = widgets.Text(placeholder='找不到的节点：粘贴 GitHub 仓库链接',
                              layout=widgets.Layout(width='400px'))
    btn_manual = widgets.Button(description='⬇ clone 并安装',
                                layout=widgets.Layout(width='140px', height='32px'),
                                style={'button_color': '#00bcd4'})
    row_manual = widgets.HBox([lbl('手动安装:'), manual_url, btn_manual],
                              layout=widgets.Layout(gap='6px', margin='4px 0', align_items='center', flex_flow='row wrap'))

    _nrows = []   # [(checkbox, clone_url)]

    def on_identify(b):
        out.clear_output()
        nodes_box.children = []
        _nrows.clear()
        types = _an.get('nodes')
        if not types:
            with out: print("⚠️ 请先在上方上传工作流并「分析」"); return
        path = base_path_input.value.strip().rstrip('/')
        nodes_dir = os.path.join(path, 'custom_nodes')
        installed = set(os.listdir(nodes_dir)) if os.path.isdir(nodes_dir) else set()
        with out: print("🔍 正在拉取 ComfyUI-Manager 节点映射 ...")
        nm = fetch_node_map(out, cb_node_mirror.value)
        if nm is None:
            with out: print("提示：可勾选「用 GitHub 镜像」重试"); return
        idx = build_node_index(nm)
        repos = {}        # (clone_url, dirname) -> set(node types)
        builtin = []      # 映射到 ComfyUI 本体的节点（内置，无需安装）
        unmatched = []    # 映射表里完全找不到的节点（可能是未收录的自定义节点）
        for nt in types:
            repo = idx.get(nt)
            if not repo:
                unmatched.append(nt)
                continue
            cu, dn = github_clone_url(repo)
            if not cu or dn.lower() == 'comfyui':   # ComfyUI 本体 = 内置节点
                builtin.append(nt)
                continue
            repos.setdefault((cu, dn), set()).add(nt)
        out.clear_output()
        with out:
            print(f"🧩 工作流共 {len(types)} 种节点：")
            print(f"  • 匹配到 {len(repos)} 个自定义节点仓库（下方勾选安装）")
            print(f"  • {len(builtin)} 种 ComfyUI 内置节点（无需安装）")
            print(f"  • {len(unmatched)} 种未匹配（数据库未收录）")
            if unmatched:
                print(f"\n  ⚠️ 未匹配的节点（若其中有自定义节点，复制名字去搜其 GitHub 仓库，用下方「手动安装」粘贴链接）：")
                for nt in sorted(unmatched):
                    print(f"     · {nt}")
        cbs = []
        for (cu, dn), nts in sorted(repos.items(), key=lambda x: x[0][1].lower()):
            done = dn in installed
            cb = widgets.Checkbox(value=not done,
                                  description=f"{dn}  （本工作流 {len(nts)} 个节点）{'  ✅已装' if done else ''}",
                                  indent=False, layout=widgets.Layout(width='620px'))
            _nrows.append((cb, cu))
            cbs.append(cb)
        nodes_box.children = cbs

    def on_install_sel(b):
        out.clear_output()
        sel = [(cb, cu) for cb, cu in _nrows if cb.value]
        if not sel:
            with out: print("⚠️ 请先「识别工作流节点」并勾选要装的"); return
        path = base_path_input.value.strip().rstrip('/')
        if not os.path.exists(venv_python(path)):
            with out: print("❌ 未找到虚拟环境，请先到「🛠 ComfyUI 安装」页执行「2. 创建虚拟环境」（否则会装进主环境）")
            return
        nodes_dir = os.path.join(path, 'custom_nodes')
        os.makedirs(nodes_dir, exist_ok=True)
        py = runtime_python(path)

        def _run():
            with out: print(f"⬇ 安装 {len(sel)} 个节点 → {nodes_dir}\n{'─' * 60}")
            for cb, cu in sel:
                with out: print(f"\n▶ {cu}")
                clone_and_install_node(cu, nodes_dir, py, out)
            with out: print(f"\n{'─' * 60}\n✅ 处理完毕（重启 ComfyUI 生效）")
        run_async(_run, btn_install_sel)

    def on_manual(b):
        out.clear_output()
        url = manual_url.value.strip()
        if not url or 'github.com' not in url:
            with out: print("⚠️ 请粘贴有效的 GitHub 仓库链接"); return
        path = base_path_input.value.strip().rstrip('/')
        if not os.path.exists(venv_python(path)):
            with out: print("❌ 未找到虚拟环境，请先到「🛠 ComfyUI 安装」页执行「2. 创建虚拟环境」（否则会装进主环境）")
            return
        nodes_dir = os.path.join(path, 'custom_nodes')
        os.makedirs(nodes_dir, exist_ok=True)
        py = runtime_python(path)
        cu = url if url.endswith('.git') else url.rstrip('/') + '.git'

        def _run():
            with out: print(f"⬇ 手动安装 → {nodes_dir}\n{'─' * 60}\n▶ {cu}")
            clone_and_install_node(cu, nodes_dir, py, out)
            with out: print(f"\n{'─' * 60}\n✅ 处理完毕（重启 ComfyUI 生效）")
        run_async(_run, btn_manual)

    btn_identify.on_click(on_identify)
    btn_install_sel.on_click(on_install_sel)
    btn_manual.on_click(on_manual)

    return widgets.VBox([
        header,
        row_base,
        widgets.HTML('<div style="height:6px"></div>'),
        row_upload,
        out,
        widgets.HTML('<div style="height:1px;background:#363b54;margin:10px 0;"></div>'),
        sec_nodes, row_node1, nodes_box, btn_install_sel, row_manual,
    ], layout=widgets.Layout(padding='12px'))


# ═══════════════════════════════════════════════════════
# Tab 5：上传模型到 HuggingFace
# ═══════════════════════════════════════════════════════
def make_uploader_tab():

    header = widgets.HTML("""
        <div class="tool-header">▼ 上传模型到 HuggingFace</div>
        <div class="tool-tip">提示：扫描本地 models 目录，勾选后用 hf upload 上传到你的仓库（需 write 写权限 Token）</div>
        <div class="tool-tip2">仓库不存在会自动创建（默认公开；私有请先在网页建好仓库）；上传固定走 huggingface.co，不走镜像</div>
    """)

    # ── ComfyUI 基础路径（自动探测）──
    row_base, base_path_input = make_path_row()

    # ── 目标仓库 / Token / 类型 ──
    repo_input = widgets.Text(placeholder='目标仓库：用户名/仓库名',
                              layout=widgets.Layout(width='360px'))
    row_repo = widgets.HBox([lbl('目标仓库:'), repo_input])
    token_input = widgets.Text(placeholder='hf_xxx（需 write 写权限）',
                               layout=widgets.Layout(width='360px'))
    row_token = widgets.HBox([lbl('Token:'), token_input])
    repotype_dd = widgets.Dropdown(options=[('模型库 model', 'model'), ('数据集 dataset', 'dataset')],
                                   value='model', layout=widgets.Layout(width='160px'))
    cb_private  = widgets.Checkbox(value=False, description='私有仓库', indent=False,
                                   layout=widgets.Layout(width='110px'))
    cb_speed    = widgets.Checkbox(value=True, description='上传加速', indent=False,
                                   layout=widgets.Layout(width='110px'))
    row_type = widgets.HBox([lbl('仓库类型:'), repotype_dd, cb_private, cb_speed],
                            layout=widgets.Layout(align_items='center'))

    # ── 扫描 & 模型勾选列表 ──
    btn_scan = widgets.Button(description='🔄 扫描本地模型',
                              layout=widgets.Layout(width='150px', height='32px'),
                              style={'button_color': '#374151'})
    btn_all  = widgets.Button(description='全选',
                              layout=widgets.Layout(width='64px', height='28px'),
                              style={'button_color': '#374151', 'font_size': '11px'})
    btn_none = widgets.Button(description='全不选',
                              layout=widgets.Layout(width='64px', height='28px'),
                              style={'button_color': '#374151', 'font_size': '11px'})
    row_scan = widgets.HBox([btn_scan, btn_all, btn_none],
                            layout=widgets.Layout(gap='8px', margin='6px 0', align_items='center'))

    scan_hint = widgets.HTML('<span style="font-size:12px;color:#7f8bb0;">点「扫描本地模型」列出 models 目录下的模型</span>')
    models_box = widgets.VBox([], layout=widgets.Layout(
        border='1px solid #363b54', border_radius='6px',
        max_height='240px', overflow='auto', padding='6px', margin='4px 0'))

    btn_upload = widgets.Button(description='⬆ 上传所选',
                                layout=widgets.Layout(width='130px', height='34px'),
                                style={'button_color': '#00bcd4'})
    out = widgets.Output(layout=widgets.Layout(
        width=W, border='1px solid #363b54', min_height='60px', max_height='320px',
        overflow='auto', padding='8px', margin='6px 0 0 0'))

    _rows = []   # [(checkbox, item)]

    def on_scan(b):
        out.clear_output()
        _rows.clear()
        path = base_path_input.value.strip().rstrip('/')
        items = list_local_models(path)
        if items is None:
            models_box.children = []
            scan_hint.value = '<span style="font-size:12px;color:#f5a623;">未找到 models 目录，请确认 ComfyUI 路径</span>'
            return
        if not items:
            models_box.children = []
            scan_hint.value = '<span style="font-size:12px;color:#f5a623;">models 目录下没有模型文件</span>'
            return
        cbs, total = [], 0
        for it in items:
            total += it['size']
            cb = widgets.Checkbox(value=False,
                                  description=f"{it['rel']}  ({human_size(it['size'])})",
                                  indent=False, layout=widgets.Layout(width='690px'))
            _rows.append((cb, it))
            cbs.append(cb)
        models_box.children = cbs
        scan_hint.value = (f'<span style="font-size:12px;color:#7f8bb0;">'
                           f'共 {len(items)} 个模型，合计 {human_size(total)}；勾选后点「上传所选」</span>')

    btn_scan.on_click(on_scan)

    def _set_all(v):
        for cb, _ in _rows:
            cb.value = v
    btn_all.on_click(lambda b: _set_all(True))
    btn_none.on_click(lambda b: _set_all(False))

    def on_upload(b):
        out.clear_output()
        repo  = repo_input.value.strip()
        token = token_input.value.strip()
        if not repo or '/' not in repo:
            with out: print("⚠️ 请填写正确的目标仓库（用户名/仓库名）"); return
        if not token:
            with out: print("⚠️ 上传必须填写 Token（需 write 写权限）"); return
        selected = [(cb, it) for cb, it in _rows if cb.value]
        if not selected:
            with out: print("⚠️ 请先勾选要上传的模型"); return
        if not ensure_hf_cli(out):
            return
        rtype = repotype_dd.value
        private = cb_private.value
        speed = cb_speed.value

        def _run():
            run_env = {'HF_TOKEN': token}
            if speed:
                if ensure_hf_transfer(out):
                    run_env['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
                else:
                    with out: print("（加速不可用，转普通速度）")
            tags = rtype + ('，私有' if private else '') + ('，加速' if 'HF_HUB_ENABLE_HF_TRANSFER' in run_env else '')
            with out:
                print(f"⬆ 上传 {len(selected)} 个文件 → {repo}（{tags}）\n{'─' * 60}")
            # 私有仓库：先创建（已存在则无操作）
            if private:
                with out: print("🔒 创建/确认私有仓库 ...")
                stream_exec(f'hf repos create {shlex.quote(repo)} --repo-type {rtype} --private --exist-ok',
                            out, indent='  ', env=run_env)
            ok = 0
            for cb, it in selected:
                full, rel = it['full'], it['rel']
                path_in_repo = f'models/{rel}'
                cmd = f'hf upload {shlex.quote(repo)} {shlex.quote(full)} {shlex.quote(path_in_repo)} --repo-type {rtype}'
                with out:
                    print(f"\n▶ {rel}  ({human_size(it['size'])})  →  {path_in_repo}")
                rc = stream_exec(cmd, out, env=run_env)
                with out:
                    if rc == 0:
                        print("  ✅ 完成")
                    else:
                        print(f"  ❌ 失败（退出码 {rc}）")
                if rc == 0:
                    ok += 1
            with out:
                print(f"\n{'─' * 60}\n✅ 完成 {ok}/{len(selected)} 个")
                print("💡 已按 models/<类型>/<文件> 对齐：日后把整个仓库克隆到 ComfyUI 根目录即可自动归位")
        run_async(_run, btn_upload)

    btn_upload.on_click(on_upload)

    return widgets.VBox([
        header,
        row_base,
        widgets.HTML('<div style="height:6px"></div>'),
        row_repo,
        row_token,
        row_type,
        row_scan,
        scan_hint,
        models_box,
        btn_upload,
        out,
    ], layout=widgets.Layout(padding='12px'))


# ═══════════════════════════════════════════════════════
# Tab 6：云端运维（磁盘 / 产出）
# ═══════════════════════════════════════════════════════
def make_ops_tab():

    header = widgets.HTML("""
        <div class="tool-header">▼ 云端运维（磁盘 / 产出）</div>
        <div class="tool-tip">提示：查看磁盘占用、清理缓存、备份/下载 output 产出</div>
        <div class="tool-tip2">云端盘满前及时清理；关机前记得把 output 打包下载或上传备份</div>
    """)

    # ── ComfyUI 基础路径（自动探测）──
    row_base, base_path_input = make_path_row()

    out = widgets.Output(layout=widgets.Layout(
        width=W, border='1px solid #363b54', min_height='80px', max_height='420px',
        overflow='auto', padding='8px', margin='6px 0 0 0'))

    # ── 磁盘占用 & 清理 ──
    sec_disk = widgets.HTML('<div class="ctk-section">💾 磁盘占用 &amp; 清理</div>')
    btn_disk = widgets.Button(description='📊 磁盘概况',
                              layout=widgets.Layout(width='130px', height='32px'),
                              style={'button_color': '#374151'})
    cb_pip   = widgets.Checkbox(value=True, description='pip 缓存', indent=False, layout=widgets.Layout(width='100px'))
    cb_hf    = widgets.Checkbox(value=True, description='HF 缓存', indent=False, layout=widgets.Layout(width='100px'))
    cb_pyc   = widgets.Checkbox(value=True, description='__pycache__', indent=False, layout=widgets.Layout(width='130px'))
    btn_clean = widgets.Button(description='🧹 一键清理',
                               layout=widgets.Layout(width='120px', height='32px'),
                               style={'button_color': '#ef4444'})
    row_disk = widgets.HBox([btn_disk, cb_pip, cb_hf, cb_pyc, btn_clean],
                            layout=widgets.Layout(gap='8px', margin='4px 0', align_items='center', flex_flow='row wrap'))

    def on_disk(b):
        out.clear_output()
        mroot = os.path.join(base_path_input.value.strip().rstrip('/'), 'models')
        with out: print(f"📊 磁盘整体：\n{'─' * 60}")
        stream_exec('df -h', out)
        with out: print(f"\n📦 models 各类型占用：\n{'─' * 60}")
        if os.path.isdir(mroot):
            stream_exec(f'du -h --max-depth=1 "{mroot}" 2>/dev/null | sort -rh', out)
        else:
            with out: print(f"  （未找到 {mroot}）")

    def on_clean(b):
        out.clear_output()
        path = base_path_input.value.strip().rstrip('/')
        cmds = []
        if cb_pip.value:
            cmds.append('pip cache purge')
        if cb_hf.value:
            cmds.append('rm -rf ~/.cache/huggingface/hub')
        if cb_pyc.value and os.path.isdir(path):
            cmds.append(f'find "{path}" -type d -name __pycache__ -prune -exec rm -rf {{}} +')
        if not cmds:
            with out: print("⚠️ 未选择任何清理项"); return
        with out: print(f"🧹 开始清理\n{'─' * 60}")

        def _run():
            for c in cmds:
                with out: print(f"\n▶ {c}")
                stream_exec(c, out, indent='  ')
            with out: print(f"\n{'─' * 60}\n✅ 清理完成（HF 缓存只清下载缓存，不影响已下载到 models 的模型）")
        run_async(_run, btn_clean)

    # ── 输出产出（output）──
    sec_out = widgets.HTML('<div class="ctk-section">🖼 输出产出（output）</div>')
    btn_scan_out = widgets.Button(description='🔄 扫描 output',
                                  layout=widgets.Layout(width='130px', height='32px'),
                                  style={'button_color': '#374151'})
    btn_zip = widgets.Button(description='📦 打包下载',
                             layout=widgets.Layout(width='120px', height='32px'),
                             style={'button_color': '#3b82f6'})
    btn_preview = widgets.Button(description='🖼 预览图片',
                                 layout=widgets.Layout(width='120px', height='32px'),
                                 style={'button_color': '#374151'})
    row_out1 = widgets.HBox([btn_scan_out, btn_preview, btn_zip], layout=widgets.Layout(gap='8px', margin='4px 0'))
    preview_box = widgets.Box([], layout=widgets.Layout(flex_flow='row wrap', margin='6px 0'))

    up_repo  = widgets.Text(placeholder='备份到：用户名/仓库名（建议 dataset）', layout=widgets.Layout(width='320px'))
    up_token = widgets.Text(placeholder='hf_xxx（write）', layout=widgets.Layout(width='200px'))
    btn_up_out = widgets.Button(description='⬆ 上传 output',
                                layout=widgets.Layout(width='130px', height='32px'),
                                style={'button_color': '#00bcd4'})
    row_out2 = widgets.HBox([lbl('备份到HF:'), up_repo, up_token, btn_up_out],
                            layout=widgets.Layout(gap='6px', margin='4px 0', align_items='center', flex_flow='row wrap'))

    # ── rclone 上传网盘（OneDrive 等）──
    sec_rclone = widgets.HTML('<div class="ctk-section">☁ 上传到网盘（rclone，支持 OneDrive）</div>')
    btn_rclone_detect = widgets.Button(description='🔄 检测/刷新网盘',
                                       layout=widgets.Layout(width='150px', height='32px'),
                                       style={'button_color': '#374151'})
    remote_dd = widgets.Dropdown(options=[('（先检测）', '')], value='',
                                 layout=widgets.Layout(width='170px'))
    rpath_input = widgets.Text(value='ComfyUI-backup/output',
                               placeholder='网盘内目标路径',
                               layout=widgets.Layout(width='220px'))
    btn_rclone_up = widgets.Button(description='☁ 上传 output',
                                   layout=widgets.Layout(width='130px', height='32px'),
                                   style={'button_color': '#00bcd4'})
    row_rclone = widgets.HBox([btn_rclone_detect, remote_dd, lbl('路径:', '40px'), rpath_input, btn_rclone_up],
                              layout=widgets.Layout(gap='6px', margin='4px 0', align_items='center', flex_flow='row wrap'))
    rclone_hint = widgets.HTML(
        '<div style="font-size:11px;color:#7f8bb0;margin:2px 0;">'
        '未配置网盘？在有浏览器的电脑装 rclone 后运行 <code>rclone config</code> 添加 OneDrive，'
        '把生成的 <code>~/.config/rclone/rclone.conf</code> 传到云端同路径；'
        '或在云端跑 <code>rclone authorize "onedrive"</code> 按提示授权。</div>')

    def _output_dir():
        return os.path.join(base_path_input.value.strip().rstrip('/'), 'output')

    def on_scan_out(b):
        out.clear_output()
        odir = _output_dir()
        if not os.path.isdir(odir):
            with out: print(f"ℹ️ 未找到 output 目录：{odir}"); return
        n, total = 0, 0
        for root, _d, files in os.walk(odir):
            for f in files:
                n += 1
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        with out:
            print(f"🖼 output：{odir}\n{'─' * 60}")
            print(f"  共 {n} 个文件，合计 {human_size(total)}")

    def on_zip(b):
        out.clear_output()
        odir = _output_dir()
        if not os.path.isdir(odir):
            with out: print(f"ℹ️ 未找到 output 目录：{odir}"); return
        with out: print("📦 正在打包 output ...")

        def _run():
            try:
                base = os.path.join(os.path.dirname(odir), 'comfyui_output')
                zip_path = shutil.make_archive(base, 'zip', odir)
                with out:
                    print(f"✅ 打包完成：{zip_path}（{human_size(os.path.getsize(zip_path))}）")
                    print("  在 JupyterLab 左侧文件树找到该 zip → 右键 Download 下载")
                    try:
                        from IPython.display import FileLink
                        display(FileLink(zip_path))
                    except Exception:
                        pass
            except Exception as e:
                with out: print(f"❌ 打包失败：{e}")
        run_async(_run, btn_zip)

    def on_up_out(b):
        out.clear_output()
        odir  = _output_dir()
        repo  = up_repo.value.strip()
        token = up_token.value.strip()
        if not os.path.isdir(odir):
            with out: print(f"ℹ️ 未找到 output 目录：{odir}"); return
        if not repo or '/' not in repo:
            with out: print("⚠️ 请填写正确的目标仓库（用户名/仓库名）"); return
        if not token:
            with out: print("⚠️ 上传需要 write 权限的 Token"); return
        if not ensure_hf_cli(out):
            return
        env = {'HF_TOKEN': token}
        cmd = f'hf upload "{repo}" "{odir}" output --repo-type dataset'
        with out: print(f"⬆ 上传 output → {repo}（dataset）\n{'─' * 60}")
        run_stream(cmd, out, btn_up_out, env=env)

    PREVIEW_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')

    def on_preview(b):
        out.clear_output()
        preview_box.children = []
        odir = _output_dir()
        if not os.path.isdir(odir):
            with out: print(f"ℹ️ 未找到 output 目录：{odir}"); return
        imgs, vids = [], []
        for root, _d, files in os.walk(odir):
            for f in files:
                full = os.path.join(root, f)
                low = f.lower()
                if low.endswith(PREVIEW_EXTS):
                    try: imgs.append((os.path.getmtime(full), full, f))
                    except OSError: pass
                elif low.endswith(('.mp4', '.webm', '.mov')):
                    vids.append(f)
        imgs.sort(reverse=True)
        show = imgs[:12]
        with out:
            extra = f"；另有 {len(vids)} 个视频（去文件树查看）" if vids else ""
            print(f"🖼 最近 {len(show)}/{len(imgs)} 张图片{extra}")
        tiles = []
        for _mt, full, name in show:
            try:
                with open(full, 'rb') as fp:
                    data = fp.read()
            except OSError:
                continue
            ext = name.rsplit('.', 1)[-1].lower()
            ext = 'jpeg' if ext == 'jpg' else ext
            img = widgets.Image(value=data, format=ext,
                                layout=widgets.Layout(width='170px', height='auto', object_fit='contain'))
            cap = widgets.HTML(f'<div style="font-size:10px;color:#7f8bb0;width:170px;'
                               f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{name}</div>')
            tiles.append(widgets.VBox([img, cap], layout=widgets.Layout(margin='4px')))
        preview_box.children = tiles

    def on_rclone_detect(b):
        out.clear_output()
        if not ensure_rclone(out):
            return
        remotes = rclone_remotes()
        if remotes:
            remote_dd.options = [(f'{r}:', r) for r in remotes]
            remote_dd.value = remotes[0]
            with out: print(f"✅ 已配置网盘：{', '.join(remotes)}")
        else:
            remote_dd.options = [('（未配置）', '')]
            remote_dd.value = ''
            with out: print("ℹ️ 未检测到已配置的网盘，请按下方提示先用 rclone config 添加 OneDrive")

    def on_rclone_up(b):
        out.clear_output()
        odir   = _output_dir()
        remote = remote_dd.value
        rpath  = rpath_input.value.strip().strip('/')
        if not os.path.isdir(odir):
            with out: print(f"ℹ️ 未找到 output 目录：{odir}"); return
        if not remote:
            with out: print("⚠️ 请先「检测/刷新网盘」并选择一个网盘"); return
        if not ensure_rclone(out):
            return
        cmd = f'rclone copy "{odir}" "{remote}:{rpath}" -P --transfers=4'
        with out: print(f"☁ 上传 output → {remote}:{rpath}\n{'─' * 60}")
        run_stream(cmd, out, btn_rclone_up)

    btn_disk.on_click(on_disk)
    btn_clean.on_click(on_clean)
    btn_scan_out.on_click(on_scan_out)
    btn_preview.on_click(on_preview)
    btn_zip.on_click(on_zip)
    btn_up_out.on_click(on_up_out)
    btn_rclone_detect.on_click(on_rclone_detect)
    btn_rclone_up.on_click(on_rclone_up)

    return widgets.VBox([
        header, row_base,
        widgets.HTML('<div style="height:6px"></div>'),
        sec_disk, row_disk,
        widgets.HTML('<div style="height:1px;background:#363b54;margin:10px 0;"></div>'),
        sec_out, row_out1, preview_box, row_out2,
        sec_rclone, row_rclone, rclone_hint,
        out,
    ], layout=widgets.Layout(padding='12px'))


# ─────────────────────────────────────────────
# 组装 Tab 并显示
# ─────────────────────────────────────────────
_tab_children = [
    make_comfyui_tab(),
    make_downloader_tab(),
    make_hf_tab(),
    make_analyzer_tab(),
    make_uploader_tab(),
    make_ops_tab(),
]
for _c in _tab_children:
    _c.add_class('ctk-card')

tab = widgets.Tab(children=_tab_children)
tab.set_title(0, '🛠 ComfyUI 安装')
tab.set_title(1, '⬇ 直链下载器')
tab.set_title(2, '🤗 HuggingFace 克隆')
tab.set_title(3, '🔍 工作流分析')
tab.set_title(4, '⬆ 上传模型')
tab.set_title(5, '🧰 云端运维')

app = widgets.VBox([tab])
app.add_class('ctk')
display(css, app)
