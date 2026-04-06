#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class PatchResult:
    changed: bool = False
    notes: list[str] = field(default_factory=list)


def run(cmd: Iterable[str], cwd: Path | None = None) -> None:
    subprocess.run(list(cmd), cwd=str(cwd) if cwd else None, check=True)


def replace_once(text: str, old: str, new: str, note: str, result: PatchResult) -> str:
    if new in text:
        return text
    if old in text:
        result.changed = True
        result.notes.append(note)
        return text.replace(old, new, 1)
    return text


def replace_all(text: str, old: str, new: str, note: str, result: PatchResult) -> str:
    if old in text:
        count = text.count(old)
        if count > 0:
            result.changed = True
            result.notes.append(f"{note} x{count}")
            return text.replace(old, new)
    return text


def patch_provider_sets(text: str, result: PatchResult) -> str:
    pat = re.compile(r'new Set\(\[(?P<body>[^\]]+)\]\)')

    def _repl(m: re.Match[str]) -> str:
        body = m.group("body")
        if '"minimax"' not in body or '"deepseek"' not in body or '"qwen"' not in body:
            return m.group(0)

        tokens = [x.strip() for x in body.split(",") if x.strip()]
        has_other = any(t == '"other"' for t in tokens)
        has_sys = any(t in ('"system-config"', 'vn') for t in tokens)

        changed = False
        if not has_other:
            tokens.append('"other"')
            changed = True
        if not has_sys:
            tokens.append('"system-config"')
            changed = True

        if changed:
            result.changed = True
            result.notes.append("补充模型厂商集合(other/system-config)")
            return f"new Set([{','.join(tokens)}])"
        return m.group(0)

    return pat.sub(_repl, text)


def patch_provider_label_map(text: str, result: PatchResult) -> str:
    pat = re.compile(
        r'(?P<prefix>\b\w+=\{)(?P<body>[^{}]{0,1500}minimax:"Minimax"[^{}]{0,1500}doubao:"豆包"[^{}]{0,1500})(?P<suffix>\})'
    )

    def _repl(m: re.Match[str]) -> str:
        body = m.group("body")
        if '"用户系统配置"' in body and ('other:"其他"' in body or '"other":"其他"' in body):
            return m.group(0)

        new_body = body
        changed = False

        if 'system-config' not in new_body and '用户系统配置' not in new_body:
            new_body = '"system-config":"用户系统配置",' + new_body
            changed = True

        if 'other:"其他"' not in new_body and '"other":"其他"' not in new_body:
            new_body = new_body + ',"other":"其他"'
            changed = True

        if changed:
            result.changed = True
            result.notes.append("补充模型厂商名称映射(other/用户系统配置)")
            return f"{m.group('prefix')}{new_body}{m.group('suffix')}"
        return m.group(0)

    return pat.sub(_repl, text)


def patch_js(text: str) -> PatchResult:
    result = PatchResult()
    original = text

    # Chat: 邀请码只在 localhost + DEV_MODE=true 时启用；生产环境直接放行
    text = replace_once(
        text,
        'if(i.value){await F();return}const De=Rt.getUserId();',
        'if(i.value){await F();return}const V=location.hostname==="localhost"&&localStorage.getItem("DEV_MODE")==="true";if(!V){i.value=!0,await F();return}const De=Rt.getUserId();',
        "Chat 邀请码改为仅本地 DEV_MODE 生效",
        result,
    )

    # WX 登录页: 邀请码校验增加 DEV_MODE 门禁
    text = replace_once(
        text,
        'Z=async o=>{var e,t,l;try{const c=await v.checkInviteCode({user_id:x.value});',
        'Z=async o=>{var e,t,l;const a=location.hostname==="localhost"&&localStorage.getItem("DEV_MODE")==="true";if(!a){o();return}try{const c=await v.checkInviteCode({user_id:x.value});',
        "WXLogin 邀请码改为仅本地 DEV_MODE 生效",
        result,
    )

    # 模型厂商集合补全
    text = replace_once(
        text,
        'Qt=new Set(["minimax","kimi","deepseek","zai","qwen","hunyuan","doubao"]),',
        'Qt=new Set(["minimax","kimi","deepseek","zai","qwen","hunyuan","doubao","other","system-config"]),',
        "Chat 模型厂商集合补全",
        result,
    )
    text = replace_once(
        text,
        'r=new Set(["minimax","kimi","deepseek","zai","qwen","hunyuan","doubao"]),',
        'r=new Set(["minimax","kimi","deepseek","zai","qwen","hunyuan","doubao","other",vn]),',
        "ModelSetting 模型厂商集合补全",
        result,
    )

    # 模型厂商文案补全
    text = replace_once(
        text,
        'qn={minimax:"Minimax",kimi:"Kimi",deepseek:"DeepSeek",zai:"智谱",qwen:"千问",hunyuan:"混元",doubao:"豆包"},',
        'qn={"system-config":"用户系统配置",minimax:"Minimax",kimi:"Kimi",deepseek:"DeepSeek",zai:"智谱",qwen:"千问",hunyuan:"混元",doubao:"豆包",other:"其他"},',
        "Chat 模型厂商文案补全",
        result,
    )

    # ModelSetting 下拉补全：追加 other 选项
    text = replace_once(
        text,
        'l=[{key:vn,label:"用户系统配置",baseUrl:"",officialUrl:""},{key:"minimax",label:"Minimax",',
        'l=[{key:vn,label:"用户系统配置",baseUrl:"",officialUrl:""},{key:"other",label:"其他",baseUrl:"",officialUrl:""},{key:"minimax",label:"Minimax",',
        "ModelSetting 下拉补充 other",
        result,
    )

    # 取消 system-config 可见性限制
    text = replace_all(
        text,
        'l.filter(k=>k.key!==vn)',
        'l',
        "取消 system-config 可见性限制",
        result,
    )
    text = replace_all(
        text,
        'l.filter(k=>k.key!=="system-config")',
        'l',
        "取消 system-config 可见性限制",
        result,
    )

    # Fallback: 尝试通过模式补齐 provider set / label map
    text = patch_provider_sets(text, result)
    text = patch_provider_label_map(text, result)

    if text != original and not result.changed:
        # 理论不会发生，兜底
        result.changed = True
        result.notes.append("发生未知文本变更")

    # 将变更内容暂存在对象上（避免定义额外结构）
    result._patched_text = text  # type: ignore[attr-defined]
    return result


def resolve_source_asar(app_arg: str, asar_arg: str | None) -> Path:
    if asar_arg:
        p = Path(asar_arg).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"app.asar 不存在: {p}")
        return p

    app = Path(app_arg).expanduser().resolve()
    if app.is_file() and app.name == "app.asar":
        return app
    if app.suffix == ".app":
        p = app / "Contents" / "Resources" / "app.asar"
        if not p.exists():
            raise FileNotFoundError(f"未找到 app.asar: {p}")
        return p
    raise FileNotFoundError("请传入 --app /Applications/QClaw.app 或 --asar /path/to/app.asar")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Patch packaged QClaw app.asar: DEV_MODE-gated invite checks + model provider visibility fixes."
    )
    parser.add_argument("--app", default="/Applications/QClaw.app", help="QClaw.app 路径")
    parser.add_argument("--asar", help="直接指定 app.asar 路径（优先于 --app）")
    parser.add_argument("--output", help="输出 asar 路径（默认同目录 app.asar.patched）")
    parser.add_argument("--no-install", action="store_true", help="只产出 patched asar，不替换原 app.asar")
    parser.add_argument("--keep-temp", action="store_true", help="保留临时目录用于排查")
    args = parser.parse_args()

    source_asar = resolve_source_asar(args.app, args.asar)
    resources_dir = source_asar.parent

    if args.output:
        output_asar = Path(args.output).expanduser().resolve()
    else:
        output_asar = resources_dir / "app.asar.patched"

    temp_dir_path: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="qclaw_hotfix_") as td:
            temp_dir_path = Path(td)
            extract_dir = temp_dir_path / "extract"

            print(f"[1/5] 解包: {source_asar}")
            run(["npx", "-y", "@electron/asar", "extract", str(source_asar), str(extract_dir)])

            js_files = sorted((extract_dir / "out" / "renderer" / "assets").glob("*.js"))
            if not js_files:
                print("未找到 renderer js 文件，可能不是预期的 QClaw 包", file=sys.stderr)
                return 2

            total_changed_files = 0
            total_notes: list[str] = []

            print(f"[2/5] 打补丁: 扫描 {len(js_files)} 个 js 文件")
            for js in js_files:
                text = js.read_text(encoding="utf-8")
                patch = patch_js(text)
                patched_text = getattr(patch, "_patched_text", text)
                if patch.changed:
                    js.write_text(patched_text, encoding="utf-8")
                    total_changed_files += 1
                    total_notes.extend([f"{js.name}: {n}" for n in patch.notes])
                    run(["node", "--check", str(js)])

            if total_changed_files == 0:
                print("未匹配到可修改的补丁位点，未生成新包。", file=sys.stderr)
                return 3

            print("[3/5] 重新打包 asar")
            output_asar.parent.mkdir(parents=True, exist_ok=True)
            run(["npx", "-y", "@electron/asar", "pack", str(extract_dir), str(output_asar)])

            if not args.no_install:
                ts = dt.datetime.now().strftime("%Y%m%d%H%M%S")
                backup_path = resources_dir / f"app.asar.bak.hotfix.{ts}"
                print(f"[4/5] 备份原包: {backup_path}")
                shutil.copy2(source_asar, backup_path)
                print(f"[5/5] 替换生效: {source_asar}")
                shutil.copy2(output_asar, source_asar)
            else:
                print("[4/5] 跳过安装（--no-install）")
                print("[5/5] 完成，仅输出 patched asar")

            print("\n补丁摘要:")
            for note in total_notes:
                print(f"- {note}")
            print(f"\n输出文件: {output_asar}")
            return 0
    finally:
        if args.keep_temp and temp_dir_path:
            print(f"临时目录保留: {temp_dir_path}")


if __name__ == "__main__":
    raise SystemExit(main())
