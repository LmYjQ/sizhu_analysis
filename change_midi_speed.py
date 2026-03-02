#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIDI 速度修改脚本
用于修改 MIDI 文件的速度 (tempo)
"""

import sys
import os

try:
    import mido
except ImportError:
    print("错误: 需要安装 mido 库")
    print("请运行: pip install mido")
    sys.exit(1)


def get_tempo_info(mid):
    """获取 MIDI 文件的当前速度信息"""
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return msg.tempo
    return None


def set_tempo(mid_file_path, new_tempo=None, speed_ratio=None, output_path=None):
    """
    修改 MIDI 文件的速度

    参数:
        mid_file_path: 输入 MIDI 文件路径
        new_tempo: 新的 tempo 值 (微秒/拍)，如果不指定则使用 speed_ratio
        speed_ratio: 速度倍率 (例如 0.5 为慢一半, 2.0 为快一倍)
        output_path: 输出文件路径，如果为 None 则覆盖原文件
    """
    if not os.path.exists(mid_file_path):
        print(f"错误: 文件不存在: {mid_file_path}")
        return False

    mid = mido.MidiFile(mid_file_path)

    # 获取当前 tempo
    current_tempo = get_tempo_info(mid)
    if current_tempo:
        current_bpm = mido.tempo2bpm(current_tempo)
        print(f"当前 tempo: {current_tempo} 微秒/拍")
        print(f"当前速度: {current_bpm:.1f} BPM")
    else:
        print("警告: 未找到 tempo 设置，使用默认值 500000 (120 BPM)")
        current_tempo = 500000

    # 计算新的 tempo
    if new_tempo is not None:
        target_tempo = new_tempo
    elif speed_ratio is not None:
        target_tempo = int(current_tempo / speed_ratio)
    else:
        print("错误: 请指定 new_tempo 或 speed_ratio")
        return False

    new_bpm = mido.tempo2bpm(target_tempo)
    print(f"目标 tempo: {target_tempo} 微秒/拍")
    print(f"目标速度: {new_bpm:.1f} BPM")

    # 修改 tempo
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                msg.tempo = target_tempo

    # 保存文件
    if output_path is None:
        output_path = mid_file_path

    mid.save(output_path)
    print(f"已保存到: {output_path}")
    return True


def main():
    # 配置
    input_file = r"D:\code\music\jnsz_pattern江南丝竹\中花六板.mid"

    # ====== 设置你想要的 BPM ======
    target_bpm = 100  # 修改这里！例如设为 80 BPM
    # ==============================

    print(f"输入文件: {input_file}")
    print(f"目标速度: {target_bpm} BPM")
    print("-" * 40)

    # 将 BPM 转换为 tempo (微秒/拍)
    new_tempo = mido.bpm2tempo(target_bpm)

    set_tempo(input_file, new_tempo=new_tempo)


if __name__ == "__main__":
    main()
