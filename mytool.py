"""
mytool.py - 云端工具箱
使用方法: 在 JupyterLab 单元格中运行 %run mytool.py
"""

import ipywidgets as widgets
from IPython.display import display
import os, subprocess, threading, urllib.request, json

# ─────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────
COMFY_MODEL_DIRS = [
    'checkpoints', 'clip', 'clip_vision', 'configs', 'controlnet',
    'diffusion_models', 'diffusers', 'embeddings', 'gligen', 'hypernetworks', 'loras',
    'photomaker', 'style_models', 'unet', 'upscale_models', 'vae',
    'vae_approx',
]
# 「自定义」选项放在列表末尾，选中后显示文本输入框
COMFY_MODEL_DIRS_WITH_CUSTOM = COMFY_MODEL_DIRS + ['自定义目录...']

# ─────────────────────────────────────────────
# 全局样式
# ─────────────────────────────────────────────
css = widgets.HTML("""
<style>
.tool-header {
    font-size: 15px; font-weight: bold; color: #e0e0e0;
    border-left: 3px solid #00bcd4; padding: 6px 0 6px 10px;
    margin-bottom: 8px;
}
.tool-tip  { font-size: 12px; color: #f5a623; margin-bottom: 3px; }
.tool-tip2 { font-size: 12px; color: #4fc3f7; margin-bottom: 10px; }

/* 任务列表表头 */
.task-header-row {
    display: flex; align-items: center;
    padding: 4px 6px;
    background: #2a2a2a;
    border-radius: 4px 4px 0 0;
    font-size: 12px; color: #aaa;
    border-bottom: 1px solid #444;
}
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

# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────
def run_stream(cmd, out):
    def _run():
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1)
        for line in proc.stdout:
            with out: print(line, end='')
        proc.wait()
        with out:
            print("\n✅ 完成！" if proc.returncode == 0
                  else f"\n❌ 出错，退出码: {proc.returncode}")
    threading.Thread(target=_run, daemon=True).start()

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

def ensure_hf_hub(out):
    try:
        import huggingface_hub  # noqa
        return True
    except ImportError:
        with out: print("⚙️ 正在安装 huggingface_hub...")
        subprocess.run('pip install -q huggingface_hub', shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            import huggingface_hub  # noqa
            with out: print("✅ 安装成功")
            return True
        except ImportError:
            with out: print("❌ 安装失败")
            return False

def hf_list_files(repo_id, token=None):
    url = f"https://huggingface.co/api/models/{repo_id}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "mytool/1.0")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return [s["rfilename"] for s in data.get("siblings", [])]


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
    _detected_path, _detected_src = detect_comfyui_path()
    base_path_input = widgets.Text(
        value=_detected_path,
        layout=widgets.Layout(width='400px')
    )
    path_source_hint = widgets.HTML(
        f'<span style="font-size:11px;color:#888;">来源：{_detected_src}</span>'
    )
    btn_redetect = widgets.Button(
        description='🔍 重新探测',
        layout=widgets.Layout(width='100px', height='28px'),
        style={'button_color': '#37474f', 'font_size': '11px'}
    )
    def on_redetect(b):
        p, src = detect_comfyui_path()
        base_path_input.value = p
        path_source_hint.value = f'<span style="font-size:11px;color:#888;">来源：{src}</span>'
    btn_redetect.on_click(on_redetect)
    row_base = widgets.VBox([
        widgets.HBox([lbl('ComfyUI路径:'), base_path_input, btn_redetect]),
        widgets.HBox([lbl(''), path_source_hint]),
    ])

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
                background:#2a2a2a;border-radius:4px 4px 0 0;
                font-size:12px;color:#aaa;border-bottom:1px solid #444;
                box-sizing:border-box;">
      <span style="width:{col_widths['dir']};flex-shrink:0;">下载目录（模型类型）</span>
      <span style="width:{col_widths['sub']};flex-shrink:0;margin-left:6px;">二级目录（可选）</span>
      <span style="width:{col_widths['url']};flex-shrink:0;margin-left:6px;">下载链接</span>
      <span style="width:32px;"></span>
    </div>""")

    tasks_vbox = widgets.VBox([], layout=widgets.Layout(
        border='1px solid #444', border_radius='0 0 4px 4px'))

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
            style={'button_color': '#c0392b', 'font_weight': 'bold'}
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
                border_bottom='1px solid #333',
                align_items='center'
            )
        )
        # 暴露一个方法给下载逻辑使用
        def get_dir():
            if dir_dd.layout.display == 'none':
                return custom_dir_txt.value.strip() or 'checkpoints'
            return dir_dd.value
        row._get_dir = get_dir

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
        style={'button_color': '#37474f'}
    )
    btn_add.on_click(add_task)

    # ── 下载按钮 & 输出 ──
    btn_dl = widgets.Button(
        description='开始下载',
        layout=widgets.Layout(width='120px', height='34px'),
        style={'button_color': '#00bcd4'}
    )
    out = widgets.Output(layout=widgets.Layout(
        width=W, border='1px solid #444', min_height='60px', max_height='300px',
        overflow_y='auto', padding='6px', margin='6px 0 0 0'
    ))

    def on_download(b):
        out.clear_output()
        base = base_path_input.value.strip().rstrip('/')

        # 收集任务
        tasks = []
        for row in tasks_vbox.children:
            # children 顺序: dir_dd, custom_dir_txt, sub_txt, url_txt, del_btn
            url_txt = row.children[3]
            sub_txt = row.children[2]
            url = url_txt.value.strip()
            if not url:
                continue
            model_dir = row._get_dir()
            sub       = sub_txt.value.strip()
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
                cmd = f'aria2c -c -x 16 -s 16 {hdr} {ow} --dir="{dest}" "{url}"'
                with out:
                    print(f"▶ {url}")
                    print(f"  → {dest}")
                    print('─' * 60)
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in proc.stdout:
                    with out: print(line, end='')
                proc.wait()
                with out:
                    print("\n✅ 完成\n" if proc.returncode == 0
                          else f"\n❌ 失败 (退出码 {proc.returncode})\n")
        threading.Thread(target=_dl, daemon=True).start()

    btn_dl.on_click(on_download)

    return widgets.VBox([
        header,
        row_base,
        widgets.HTML('<div style="height:6px"></div>'),
        task_header,
        tasks_vbox,
        widgets.HBox([btn_add], layout=widgets.Layout(margin='6px 0')),
        widgets.HTML('<div style="height:2px;border-top:1px solid #333;margin:4px 0"></div>'),
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
        <div class="tool-tip2">如遇网络超时，可切换为国内 HF-Mirror：https://hf-mirror.com</div>
    """)

    # ── ComfyUI 基础路径（自动探测）──
    _detected_path, _detected_src = detect_comfyui_path()
    base_path_input = widgets.Text(
        value=_detected_path,
        layout=widgets.Layout(width='400px')
    )
    path_source_hint = widgets.HTML(
        f'<span style="font-size:11px;color:#888;">来源：{_detected_src}</span>'
    )
    btn_redetect = widgets.Button(
        description='🔍 重新探测',
        layout=widgets.Layout(width='100px', height='28px'),
        style={'button_color': '#37474f', 'font_size': '11px'}
    )
    def on_redetect(b):
        p, src = detect_comfyui_path()
        base_path_input.value = p
        path_source_hint.value = f'<span style="font-size:11px;color:#888;">来源：{src}</span>'
    btn_redetect.on_click(on_redetect)
    row_base = widgets.VBox([
        widgets.HBox([lbl('ComfyUI路径:'), base_path_input, btn_redetect]),
        widgets.HBox([lbl(''), path_source_hint]),
    ])

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
    row_opts = widgets.HBox([cb_subfolder, cb_token, cb_overwrite],
                            layout=widgets.Layout(margin='4px 0'))

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
        model_dir = get_hf_dir()
        sub = sub_txt.value.strip()
        dest = os.path.join(base, 'models', model_dir)
        if sub:
            dest = os.path.join(dest, sub)
        path_preview.value = (
            f'<div style="font-size:12px;color:#888;margin:2px 0 6px {LBSW};">'
            f'下载到：<span style="color:#4fc3f7">{dest}</span></div>'
        )

    base_path_input.observe(update_preview, names='value')
    # dir_dd 和 custom_dir_txt 已在 on_hf_dir_change 中触发 update_preview
    sub_txt.observe(update_preview, names='value')
    update_preview()

    # ── 按钮 ──
    btn_parse = widgets.Button(description='1. 解析仓库',
                               layout=widgets.Layout(width='130px', height='34px'),
                               style={'button_color': '#4CAF50'})
    btn_dl    = widgets.Button(description='2. 确认下载',
                               layout=widgets.Layout(width='130px', height='34px'),
                               style={'button_color': '#FF9800'})
    row_btns = widgets.HBox([btn_parse, btn_dl],
                            layout=widgets.Layout(gap='10px', margin='6px 0'))

    out = widgets.Output(layout=widgets.Layout(
        width=W, border='1px solid #444', min_height='60px', max_height='320px',
        overflow_y='auto', padding='6px', margin='4px 0 0 0'))

    _state = {'repo_id': None}

    def get_repo_id(raw):
        raw = raw.strip().rstrip('/')
        if 'huggingface.co/' in raw:
            parts = raw.split('huggingface.co/')[-1].split('/')
            if len(parts) >= 2:
                return '/'.join(parts[:2])
        elif '/' in raw and not raw.startswith('http'):
            return raw
        return None

    def build_dest():
        base = base_path_input.value.strip().rstrip('/')
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
        repo_id = get_repo_id(raw)
        if not repo_id:
            with out: print("❌ 无法解析仓库地址，请检查格式"); return

        token = token_input.value.strip() if cb_token.value else None
        with out: print(f"🔍 正在请求仓库信息：{repo_id} ...")

        def _fetch():
            try:
                files = hf_list_files(repo_id, token)
                _state['repo_id'] = repo_id
                dest = build_dest()
                if cb_subfolder.value:
                    dest = os.path.join(dest, repo_id.split('/')[-1])
                with out:
                    out.clear_output()
                    print(f"✅ 解析成功：{repo_id}")
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
        threading.Thread(target=_fetch, daemon=True).start()

    def on_confirm(b):
        out.clear_output()
        repo_id = _state.get('repo_id')
        if not repo_id:
            with out: print("⚠️ 请先点击「解析仓库」并等待解析完成"); return
        if not ensure_hf_hub(out):
            return

        token = token_input.value.strip() if cb_token.value else ''
        dest  = build_dest()
        if cb_subfolder.value:
            dest = os.path.join(dest, repo_id.split('/')[-1])
        os.makedirs(dest, exist_ok=True)

        cmd_parts = ['huggingface-cli', 'download', repo_id]
        if clone_mode.value == '仅允许以下文件':
            for f in [x.strip() for x in filenames_input.value.strip().split('\n') if x.strip()]:
                cmd_parts += ['--include', f'"{f}"']
        elif clone_mode.value == '排除以下文件':
            for f in [x.strip() for x in filenames_input.value.strip().split('\n') if x.strip()]:
                cmd_parts += ['--exclude', f'"{f}"']
        cmd_parts += ['--local-dir', f'"{dest}"']
        if token:
            cmd_parts += ['--token', token]
        cmd_parts += ['--local-dir-use-symlinks', 'False']

        cmd = ' '.join(cmd_parts)
        with out: print(f"▶ 执行：{cmd}\n{'─'*60}")
        run_stream(cmd, out)

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
        <div class="tool-tip2">安装完成后可直接启动，也可安装常用自定义节点</div>
    """)

    # ── 安装路径 ──
    install_path = widgets.Text(
        value='/root/ComfyUI',
        layout=widgets.Layout(width='400px')
    )
    row_path = widgets.HBox([lbl('安装路径:'), install_path])

    # ── Git 分支 ──
    branch_input = widgets.Text(
        value='master',
        layout=widgets.Layout(width='200px')
    )
    row_branch = widgets.HBox([lbl('分支:'), branch_input])

    # ── Python 解释器 ──
    python_input = widgets.Text(
        value='python3',
        placeholder='如 python3 或 /usr/bin/python3',
        layout=widgets.Layout(width='300px')
    )
    row_python = widgets.HBox([lbl('Python:'), python_input])

    # ── 安装选项 ──
    cb_torch_cu121  = widgets.Checkbox(value=True,  description='安装 PyTorch (CUDA 12.1)',
                                       indent=False, layout=widgets.Layout(width='220px'))
    cb_xformers     = widgets.Checkbox(value=True,  description='安装 xformers',
                                       indent=False, layout=widgets.Layout(width='160px'))
    cb_deps         = widgets.Checkbox(value=True,  description='安装 requirements.txt',
                                       indent=False, layout=widgets.Layout(width='200px'))

    row_opts1 = widgets.HBox([cb_torch_cu121, cb_xformers, cb_deps],
                             layout=widgets.Layout(margin='4px 0'))

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
        widgets.HTML('<div style="font-size:12px;color:#aaa;margin:8px 0 4px 0;">📦 自定义节点（可选）：</div>'),
        *node_rows
    ])

    # ── 分隔线 ──
    divider = widgets.HTML('<div style="height:1px;background:#333;margin:10px 0;"></div>')

    # ── 按钮区 ──
    btn_clone   = widgets.Button(description='1. 克隆 ComfyUI',
                                 layout=widgets.Layout(width='150px', height='34px'),
                                 style={'button_color': '#1565C0'})
    btn_install = widgets.Button(description='2. 安装依赖',
                                 layout=widgets.Layout(width='130px', height='34px'),
                                 style={'button_color': '#2E7D32'})
    btn_nodes   = widgets.Button(description='3. 安装自定义节点',
                                 layout=widgets.Layout(width='160px', height='34px'),
                                 style={'button_color': '#6A1B9A'})
    btn_launch  = widgets.Button(description='▶ 启动 ComfyUI',
                                 layout=widgets.Layout(width='140px', height='34px'),
                                 style={'button_color': '#00838F'})

    row_btns = widgets.HBox([btn_clone, btn_install, btn_nodes, btn_launch],
                            layout=widgets.Layout(gap='8px', margin='8px 0'))

    # ── 输出 ──
    out = widgets.Output(layout=widgets.Layout(
        width=W, border='1px solid #444', min_height='80px', max_height='400px',
        overflow_y='auto', padding='8px', margin='6px 0 0 0'
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
        return python_input.value.strip() or 'python3'

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
        cmd = f'git clone -b {branch} --depth 1 https://github.com/comfyanonymous/ComfyUI.git "{path}"'
        with out:
            print(f"▶ 克隆 ComfyUI → {path}")
            print(f"  分支: {branch}\n{'─'*60}")
        set_status('⏳ 正在克隆...', '#f5a623')

        def _run():
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                with out: print(line, end='')
            proc.wait()
            if proc.returncode == 0:
                with out: print("\n✅ 克隆完成！")
                set_status('✅ 克隆完成', '#4CAF50')
            else:
                with out: print(f"\n❌ 克隆失败（退出码 {proc.returncode}）")
                set_status('❌ 克隆失败', '#ef5350')
        threading.Thread(target=_run, daemon=True).start()

    def on_install(b):
        out.clear_output()
        path   = get_path()
        py     = get_python()

        if not os.path.isdir(path):
            with out: print(f"❌ 目录不存在：{path}\n请先执行「克隆 ComfyUI」")
            return

        set_status('⏳ 正在安装依赖...', '#f5a623')

        cmds = []
        if cb_torch_cu121.value:
            cmds.append(
                f'{py} -m pip install torch torchvision torchaudio '
                f'--index-url https://download.pytorch.org/whl/cu121'
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

        full_cmd = ' && '.join(cmds)
        with out:
            print(f"▶ 安装依赖\n{'─'*60}")

        def _run():
            proc = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                with out: print(line, end='')
            proc.wait()
            if proc.returncode == 0:
                with out: print("\n✅ 依赖安装完成！")
                set_status('✅ 依赖安装完成', '#4CAF50')
            else:
                with out: print(f"\n❌ 安装出错（退出码 {proc.returncode}）")
                set_status('❌ 安装出错', '#ef5350')
        threading.Thread(target=_run, daemon=True).start()

    def on_nodes(b):
        out.clear_output()
        path = get_path()
        py   = get_python()
        nodes_dir = os.path.join(path, 'custom_nodes')

        if not os.path.isdir(path):
            with out: print(f"❌ 目录不存在：{path}\n请先执行「克隆 ComfyUI」")
            return

        selected = [(cb.description, url) for cb, url in node_checks if cb.value]
        if not selected:
            with out: print("⚠️  未勾选任何自定义节点")
            return

        os.makedirs(nodes_dir, exist_ok=True)
        set_status('⏳ 正在安装自定义节点...', '#f5a623')
        with out:
            print(f"▶ 安装 {len(selected)} 个自定义节点 → {nodes_dir}\n{'─'*60}")

        def _pip_stream(cmd, label):
            """流式运行 pip，实时打印输出"""
            proc = subprocess.Popen(cmd, shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    with out: print(f"    {line}")
            proc.wait()
            return proc.returncode

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
                    rc = _pip_stream(f'cd "{dest}" && {py} install.py', name)
                    with out:
                        if rc == 0: print(f"  ✅ install.py 完成")
                        else:       print(f"  ⚠️  install.py 退出码 {rc}，继续尝试 requirements.txt")

                if os.path.exists(req_txt):
                    with out: print(f"  ⚙️  安装 requirements.txt ...")
                    rc = _pip_stream(f'{py} -m pip install -r "{req_txt}"', name)
                    with out:
                        if rc == 0: print(f"  ✅ 依赖安装完成")
                        else:       print(f"  ❌ 依赖安装失败（退出码 {rc}）")
                elif not os.path.exists(install_py):
                    with out: print(f"  ℹ️  无需额外依赖")

            with out: print(f"\n{'─'*60}\n✅ 全部节点处理完毕！")
            set_status('✅ 自定义节点安装完成', '#4CAF50')
        threading.Thread(target=_run, daemon=True).start()

    def on_launch(b):
        out.clear_output()
        path = get_path()
        py   = get_python()
        main = os.path.join(path, 'main.py')

        if not os.path.exists(main):
            with out: print(f"❌ 未找到 {main}\n请先完成克隆和安装步骤")
            return

        cmd = f'cd "{path}" && {py} main.py --listen 0.0.0.0 --port 8188'
        with out:
            print(f"▶ 启动 ComfyUI")
            print(f"  访问地址：http://<服务器IP>:8188")
            print(f"  命令：{cmd}\n{'─'*60}")
        run_stream(cmd, out)

    btn_clone.on_click(on_clone)
    btn_install.on_click(on_install)
    btn_nodes.on_click(on_nodes)
    btn_launch.on_click(on_launch)

    return widgets.VBox([
        header,
        row_path,
        row_branch,
        row_python,
        divider,
        widgets.HTML('<div style="font-size:12px;color:#aaa;margin:0 0 4px 0;">⚙️ 安装选项：</div>'),
        row_opts1,
        nodes_section,
        divider,
        row_btns,
        status_html,
        out,
    ], layout=widgets.Layout(padding='12px'))


# ─────────────────────────────────────────────
# 组装 Tab 并显示
# ─────────────────────────────────────────────
tab = widgets.Tab(children=[
    make_comfyui_tab(),
    make_downloader_tab(),
    make_hf_tab(),
])
tab.set_title(0, '🛠 ComfyUI 安装')
tab.set_title(1, '⬇ 直链下载器')
tab.set_title(2, '🤗 HuggingFace 克隆')

display(css, tab)
