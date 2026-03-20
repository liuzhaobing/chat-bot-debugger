#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设备协议 JSON 文件转 Markdown 表格工具
"""

import argparse
import json
import sys
from pathlib import Path


def _format_param_value(param_info: dict) -> str:
    """格式化参数取值信息，包含范围、枚举、默认值、必填"""
    parts = []

    # 是否必填
    required = param_info.get('required', 0)
    parts.append("必填" if required == 1 else "非必填")

    # 枚举值
    enum_vals = param_info.get('enum', [])
    if enum_vals:
        parts.append(f"可选: {', '.join(map(str, enum_vals))}")
    else:
        # 取值范围
        minimum = param_info.get('minimum')
        maximum = param_info.get('maximum')
        if minimum is not None and maximum is not None:
            parts.append(f"取值范围: {minimum} ~ {maximum}")

    # 默认值
    default = param_info.get('defaultX')
    if default is not None:
        parts.append(f"默认值: {default}")

    return "<br>".join(parts)


def convert_device_json_to_markdown(json_path: str) -> str:
    """
    将单个设备协议 JSON 文件转换为易读的 Markdown 表格

    Args:
        json_path: JSON 文件的路径

    Returns:
        Markdown 格式的字符串
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    md_lines = []

    # 三级标题：device_type + device_model
    device_type = data.get('device_type', '')
    device_model = data.get('device_model', '')
    md_lines.append(f"### {device_type} {device_model}\n")

    function_config = data.get('function_config', {})

    # 第一张表格：功能列表
    if function_config:
        md_lines.append(f"#### {device_type} {device_model} 功能列表\n")
        md_lines.append("| 功能 | 参数 | 参数描述 | 可选值 |")
        md_lines.append("| --- | --- | --- | --- |")

        for func_key, func_info in function_config.items():
            desc = func_info.get('description', '-')
            params = func_info.get('function_parameters', {})

            # 特殊处理 mode_switch：引导用户查看第二张表
            if func_key == 'mode_switch':
                md_lines.append(f"| {desc} | 详见模式设置表 | 详见模式设置表 | 详见模式设置表 |")
                continue

            if not params:
                md_lines.append(f"| {desc} | - | - | - |")
                continue

            param_names = list(params.keys())
            first_param = True
            for param_name in param_names:
                param_info = params[param_name]
                param_desc = param_info.get('description', '-')
                enum_vals = param_info.get('enum', [])
                enum_str = "、".join(map(str, enum_vals)) if enum_vals else "-"

                if first_param:
                    md_lines.append(f"| {desc} | {param_name} | {param_desc} | {enum_str} |")
                    first_param = False
                else:
                    md_lines.append(f"| | {param_name} | {param_desc} | {enum_str} |")

        md_lines.append("")

    # 第二张表格：mode_switch（模式设置详情）
    if 'mode_switch' in function_config:
        md_lines.append(f"#### {device_type} {device_model} 模式设置\n")
        mode_switch = function_config['mode_switch']
        mode_params_config = mode_switch.get('mode_parameters_config', [])

        md_lines.append("| 模式 | 参数 | 参数描述 | 参数取值 |")
        md_lines.append("| --- | --- | --- | --- |")

        for mode_cfg in mode_params_config:
            mode_name = mode_cfg.get('function_name', '')
            params = mode_cfg.get('function_parameters', {})

            if not params:
                md_lines.append(f"| {mode_name} | - | - | - |")
                continue

            param_names = list(params.keys())
            first_param = True
            for param_name in param_names:
                info = params[param_name]
                desc = info.get('description', '-')
                value_str = _format_param_value(info)

                if first_param:
                    md_lines.append(f"| {mode_name} | {param_name} | {desc} | {value_str} |")
                    first_param = False
                else:
                    md_lines.append(f"| | {param_name} | {desc} | {value_str} |")

        md_lines.append("")

    return '\n'.join(md_lines)


def main():
    parser = argparse.ArgumentParser(
        description='将设备协议 JSON 文件转换为 Markdown 表格'
    )
    parser.add_argument(
        'json_file',
        type=str,
        help='JSON 文件路径'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='输出 Markdown 文件路径（默认使用相同路径和文件名，仅更改后缀为 .md）'
    )

    args = parser.parse_args()

    json_path = Path(args.json_file)

    if not json_path.exists():
        print(f"错误: 文件不存在: {json_path}", file=sys.stderr)
        sys.exit(1)

    if json_path.suffix.lower() != '.json':
        print(f"错误: 输入文件必须是 .json 格式: {json_path}", file=sys.stderr)
        sys.exit(1)

    try:
        md_content = convert_device_json_to_markdown(str(json_path))
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 转换失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 确定输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = json_path.with_suffix('.md')

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"转换成功: {output_path}")
    except Exception as e:
        print(f"错误: 写入文件失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
