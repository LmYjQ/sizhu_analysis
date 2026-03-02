#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIDI 每一拍内容统计分析
统计指定声部中每一拍的音符内容及出现次数
"""

import mido
from collections import defaultdict
import sys
import os


def analyze_beat_contents(mid_file_path, track_index=0):
    """
    分析 MIDI 文件中指定声部的每一拍内容

    参数:
        mid_file_path: MIDI 文件路径
        track_index: 要分析的声部索引 (从 0 开始)

    返回:
        beat_contents: 每拍的内容列表，包含 (音符, 拍内偏移) 元组
        ticks_per_beat: 每拍的 tick 数
    """
    mid = mido.MidiFile(mid_file_path)

    # 检查声部索引是否有效
    if track_index >= len(mid.tracks):
        print(f"错误: 只有 {len(mid.tracks)} 个声部，索引 {track_index} 超出范围")
        return None

    # 获取指定声部
    track = mid.tracks[track_index]
    print(f"分析声部 {track_index}: {track.name if track.name else '未命名'}")

    # 获取 ticks_per_beat (每拍的 tick 数)
    ticks_per_beat = mid.ticks_per_beat
    print(f"每拍 tick 数: {ticks_per_beat}")

    # 用于存储每拍的内容
    # beat_contents[拍号] = [(音符1, 拍内偏移1), (音符2, 拍内偏移2), ...]
    # 拍内偏移是该音符相对于该拍开始位置的 tick 数
    beat_contents = defaultdict(list)

    # 第一步：收集所有音符的开始和结束时间
    note_on_times = {}  # note -> start_tick

    current_tick = 0
    for msg in track:
        current_tick += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            note_on_times[msg.note] = current_tick
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in note_on_times:
                start_tick = note_on_times.pop(msg.note)
                duration = current_tick - start_tick

                # 找出音符跨越的所有拍
                start_beat = start_tick // ticks_per_beat
                end_beat = (start_tick + duration - 1) // ticks_per_beat  # -1 确保音符结束时不算入下一拍

                for beat in range(start_beat, end_beat + 1):
                    # 计算该音符在此拍中的偏移
                    if beat == start_beat:
                        beat_offset = start_tick % ticks_per_beat
                    else:
                        beat_offset = 0  # 音符在该拍开始时就响着

                    beat_contents[beat].append((msg.note, beat_offset))

    return beat_contents, ticks_per_beat


def format_note_name(note_num):
    """将 MIDI 音符编号转换为音名"""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = note_num // 12 - 1
    note_name = notes[note_num % 12]
    return f"{note_name}{octave}"


def get_jianpu_dots():
    """根据系统判断使用哪种高低音点字符"""
    import platform
    system = platform.system()
    if system == "Windows":
        # Windows 控制台用 ASCII 字符
        return ('^', '_')  # (高音点, 低音点)
    else:
        # 其他系统用 Unicode 字符
        return ('̇', '̳')


# 全局变量存储高低音点字符
_JIANPU_DOTS = get_jianpu_dots()


def midi_to_jianpu(note_num, key="C"):
    """
    将 MIDI 音符编号转换为简谱音名

    参数:
        note_num: MIDI 音符编号 (60 = 中央 C = C4)
        key: 调性，如 "C", "G", "D", "F", "Bb", "Eb" 等

    返回:
        简谱音名，如 "1", "1^"(高音点), "5_"(低音点), "#4", "b7" 等
    """
    # 调的主音 MIDI 编号 (该音 = 简谱 1)
    # C=60, G=67, D=74, A=81, E=88, B=95
    # F=65, Bb=70, Eb=75, Ab=80, Db=83, Gb=78
    key_tonic_midi = {
        'C': 60, 'G': 67, 'D': 74, 'A': 81, 'E': 88, 'B': 95,
        'F': 65, 'Bb': 70, 'Eb': 75, 'Ab': 80, 'Db': 83, 'Gb': 78,
        'F#': 78, 'Cb': 59, 'E#': 65, 'B#': 60, 'A#': 70,
    }

    # 获取调的主音
    tonic = key_tonic_midi.get(key, 60)

    # 简谱显示提高一个八度（仅影响显示，不改变实际音符）
    note_num = note_num + 12

    # 计算相对于主音的音程
    interval = note_num - tonic

    # 将音程映射到简谱 1-7
    # 0=1, 1=#1/b2, 2=2, 3=#2/b3, 4=3, 5=4, 6=#4/b5, 7=5, 8=#5/b6, 9=6, 10=#6/b7, 11=7
    # 取模 12 得到相对于主音的音级
    relative_pitch = interval % 12

    # 简谱映射 (0-11 相对于主音)
    interval_to_jianpu = {
        0: '1', 1: '#1', 2: '2', 3: '#2', 4: '3',
        5: '4', 6: '#4', 7: '5', 8: '#5', 9: '6', 10: '#6', 11: '7'
    }

    base_note = interval_to_jianpu.get(relative_pitch, '?')

    # 计算八度 (相对于调的主音)
    octave_offset = interval // 12

    # 添加高低音点
    high_dot, low_dot = _JIANPU_DOTS
    if octave_offset > 0:
        dots = high_dot * min(octave_offset, 2)  # 最多两个点
    elif octave_offset < 0:
        dots = low_dot * min(-octave_offset, 2)
    else:
        dots = ''

    return f"{base_note}{dots}"


def print_beat_statistics(beat_contents, ticks_per_beat, key="C"):
    """打印统计结果"""
    if not beat_contents:
        print("未找到任何音符")
        return

    print("\n" + "=" * 60)
    print("每拍音符统计结果 (音符顺序+拍内位置)")
    print("=" * 60)

    # 按拍号排序
    sorted_beats = sorted(beat_contents.keys())
    max_beat = max(sorted_beats) + 1

    beats_in_measure = 4  # 每4拍算一小节

    # 遍历所有拍，包括空拍
    for beat in range(max_beat):
        # 转换为"第xx小节第i拍"格式
        measure_num = beat // beats_in_measure + 1
        beat_in_measure = beat % beats_in_measure + 1
        beat_label = f"第{measure_num}小节第{beat_in_measure}拍"

        notes_list = beat_contents.get(beat, [])

        if not notes_list:
            # 空拍
            print(f"{beat_label}: 0")
            continue

        # 检查拍开始是否是休止符（第一个音符的 offset > 0）
        # 如果是，在前面补一个 0
        note_strs = []
        first_offset = notes_list[0][1]  # 第一个音符的拍内偏移
        if first_offset > 0:
            note_strs.append("0")  # 拍开始是休止符

        # 转换为音名，保留顺序和位置信息
        for note, offset in notes_list:
            note_name = format_note_name(note)
            jianpu = midi_to_jianpu(note, key)
            # 用位置百分比来表示拍内偏移 (0%=开始, 100%=结束)
            pos_percent = int(offset / ticks_per_beat * 100)
            note_strs.append(f"{jianpu}[{pos_percent:>3}%]")

        print(f"{beat_label}: {' '.join(note_strs)}")

    # 统计有多少个不同的拍
    beats_with_notes = sum(1 for notes_list in beat_contents.values() if notes_list)
    print(f"\n共有 {max_beat} 拍，其中 {beats_with_notes} 拍有音符")


def print_beat_transitions(beat_contents, key="C"):
    """打印拍子之间的转换关系"""
    if not beat_contents:
        return

    print("\n" + "=" * 60)
    print("拍子转换关系 (前一拍 -> 后一拍)")
    print("=" * 60)

    # 统计转换关系
    # transition[(前一个音集, 后一个音集)] = 出现次数
    transitions = defaultdict(int)

    sorted_beats = sorted(beat_contents.keys())

    for i in range(len(sorted_beats) - 1):
        current_beat = sorted_beats[i]
        next_beat = sorted_beats[i + 1]

        # 跳过没有音符的拍
        if not beat_contents[current_beat] or not beat_contents[next_beat]:
            continue

        # 获取当前拍和下一拍的音符集合
        current_notes = tuple(sorted(beat_contents[current_beat].keys()))
        next_notes = tuple(sorted(beat_contents[next_beat].keys()))

        # 转换为音名和简谱
        current_strs = []
        for n in current_notes:
            jianpu = midi_to_jianpu(n, key)
            current_strs.append(f"{jianpu}")

        next_strs = []
        for n in next_notes:
            jianpu = midi_to_jianpu(n, key)
            next_strs.append(f"{jianpu}")

        current_str = ','.join(current_strs)
        next_str = ','.join(next_strs)

        transitions[(current_str, next_str)] += 1

    # 按出现次数排序
    sorted_transitions = sorted(transitions.items(), key=lambda x: -x[1])

    for (current, next_), count in sorted_transitions:
        print(f"{current} -> {next_}: {count} 次")


def beat_to_pattern(notes_list, ticks_per_beat, key="C"):
    """
    将拍内音符转换为模式字符串（用于比较是否相同）

    参数:
        notes_list: [(音符, 拍内偏移), ...] 列表
        ticks_per_beat: 每拍的 tick 数
        key: 调性

    返回:
        模式字符串，如 "1[0]5[50]"（空拍返回 "0"）
    """
    if not notes_list:
        return "0"

    # 转换为 (简谱, 位置百分比) 元组列表
    pattern_parts = []
    for note, offset in notes_list:
        jianpu = midi_to_jianpu(note, key)
        pos_percent = int(offset / ticks_per_beat * 100)
        pattern_parts.append((jianpu, pos_percent))

    # 按位置排序
    pattern_parts.sort(key=lambda x: x[1])

    # 构建模式字符串
    return ''.join(f"{jp}[{pos}]" for jp, pos in pattern_parts)


def find_pattern_occurrences(beat_contents, ticks_per_beat, key="C", total_beats=None):
    """
    统计每拍模式的重复出现次数和位置

    参数:
        beat_contents: analyze_beat_contents 返回的每拍内容
        ticks_per_beat: 每拍的 tick 数
        key: 调性
        total_beats: 总拍数（如果为None则从beat_contents估算）

    返回:
        pattern_info: {
            "模式字符串": {
                "count": 出现次数,
                "positions": [拍号列表 (0开始)],
                "pattern_str": 模式字符串
            },
            ...
        }
    """
    # 获取总拍数
    if total_beats is not None:
        max_beat = total_beats
    else:
        sorted_beats = sorted(beat_contents.keys())
        max_beat = max(sorted_beats) + 1

    # 统计模式出现
    # pattern_str -> [位置列表]
    pattern_positions = defaultdict(list)

    for beat in range(max_beat):
        notes_list = beat_contents.get(beat, [])
        pattern_str = beat_to_pattern(notes_list, ticks_per_beat, key)
        pattern_positions[pattern_str].append(beat)

    # 构建结果
    pattern_info = {}
    for pattern_str, positions in pattern_positions.items():
        pattern_info[pattern_str] = {
            "count": len(positions),
            "positions": positions,
            "pattern_str": pattern_str
        }

    return pattern_info


def generate_annotated_musicxml(mid_file_path, track_index, key, output_path=None):
    """
    生成带有重复片段标注的 MusicXML 文件

    每一拍后添加一个休止符凑成2拍一小节，在小节末尾标注重复位置和次数

    参数:
        mid_file_path: MIDI 文件路径
        track_index: 声部索引
        key: 调性
        output_path: 输出文件路径

    返回:
        是否成功
    """
    try:
        from music21 import note, stream
    except ImportError:
        print("错误: 需要安装 music21 库")
        print("请运行: pip install music21")
        return False

    # 分析拍子内容
    result = analyze_beat_contents(mid_file_path, track_index)
    if result is None:
        return False

    beat_contents, ticks_per_beat = result

    # 计算总拍数（从 MIDI 文件的结束时间）
    mid = mido.MidiFile(mid_file_path)
    # msg.time 是时间增量，需要累加得到累计时间
    total_ticks = 0
    for msg in mid.tracks[track_index]:
        total_ticks += msg.time
    total_beats = total_ticks // ticks_per_beat + 1  # +1 确保包含最后一拍

    # 统计重复模式
    pattern_info = find_pattern_occurrences(beat_contents, ticks_per_beat, key, total_beats)

    # 使用 mido 直接从 MIDI 消息构建乐谱（更可靠）
    # 先收集每个音符的持续时间
    track = mid.tracks[track_index]

    # 收集音符事件：note_on -> note_off 之间的 tick 数
    note_durations = {}  # note -> tick 数
    note_on_times = {}  # note -> 开始 tick

    current_tick = 0
    for msg in track:
        current_tick += msg.time

        if msg.type == 'note_on' and msg.velocity > 0:
            note_on_times[msg.note] = current_tick
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in note_on_times:
                duration = current_tick - note_on_times[msg.note]
                note_durations[msg.note] = duration
                del note_on_times[msg.note]

    # 重新遍历计算每个音符对应的拍号和时值
    current_tick = 0
    notes_data = []  # [(note, velocity, start_tick, duration)]

    for msg in track:
        current_tick += msg.time

        if msg.type == 'note_on' and msg.velocity > 0:
            duration = note_durations.get(msg.note, ticks_per_beat)  # 默认1拍
            notes_data.append((msg.note, current_tick, duration))

    # 创建新的 part
    new_part = stream.Part()

    # 设置速度（从 mido 获取）
    for msg in track:
        if msg.type == 'set_tempo':
            from music21 import tempo as m21_tempo
            new_part.insert(0, m21_tempo.MetronomeMark('quarter', mido.tempo2bpm(msg.tempo)))
            break

    # 遍历音符数据，添加休止符并在小节末尾标注
    current_beat = 0  # 当前是第几拍
    beats_in_measure = 4  # 每4拍算一小节（2/4拍，每小节2拍×2=4拍）

    for note_num, start_tick, duration in notes_data:
        # 计算该音符对应的拍号
        beat_num = start_tick // ticks_per_beat

        # 获取该拍的模式信息
        pattern_str = beat_to_pattern(beat_contents.get(beat_num, []), ticks_per_beat, key)
        pattern_data = pattern_info.get(pattern_str, {})

        # 创建音符，保留原始时值
        n = note.Note(note_num)
        # 将 tick 转换为 quarterLength (1 = 四分音符)
        n.quarterLength = duration / ticks_per_beat

        # 添加 lyric（显示位置和次数）
        if pattern_data.get("count", 1) > 1:
            count = pattern_data["count"]
            positions = pattern_data["positions"]
            # 转换为"第k小节第i拍"格式
            pos_parts = []
            for p in positions:
                measure_num = p // beats_in_measure + 1  # 小节号从1开始
                beat_in_measure = p % beats_in_measure + 1  # 拍号从1开始
                pos_parts.append(f"{measure_num}小节第{beat_in_measure}拍")
            pos_str = ','.join(pos_parts)
            lyric_text = f"x{count}({pos_str})"
            n.lyrics.append(note.Lyric(lyric_text))

        new_part.append(n)

        # 添加休止符（补齐到1拍）
        rest_duration = ticks_per_beat - (duration % ticks_per_beat)
        if rest_duration > 0:
            rest = note.Rest()
            rest.quarterLength = rest_duration / ticks_per_beat
            new_part.append(rest)

        current_beat += 1

    print(f"DEBUG: 共添加 {current_beat} 个音符到乐谱")

    # 创建新的 Score
    new_stream = stream.Score()
    new_stream.insert(0, new_part)

    # 添加重复模式统计说明到 part name
    new_part.partName = "重复模式分析"

    # 保存文件
    if output_path is None:
        base = os.path.splitext(mid_file_path)[0]
        output_path = f"{base}_重复标注.xml"

    new_stream.write('musicxml', fp=output_path)
    print(f"已生成 MusicXML 文件: {output_path}")

    # 输出重复模式统计
    print("\n" + "=" * 60)
    print("重复模式统计")
    print("=" * 60)

    # 按出现次数排序
    sorted_patterns = sorted(pattern_info.items(), key=lambda x: -x[1]["count"])
    beats_in_measure = 4  # 每4拍算一小节（2/4拍，每小节2拍×2=4拍）

    for pattern_str, data in sorted_patterns:
        if data["count"] > 1:
            # 转换为"第k小节第i拍"格式
            pos_parts = []
            for p in data["positions"]:
                measure_num = p // beats_in_measure + 1  # 小节号从1开始
                beat_in_measure = p % beats_in_measure + 1  # 拍号从1开始
                pos_parts.append(f"{measure_num}小节第{beat_in_measure}拍")
            pos_str = ','.join(pos_parts)

            print(f"模式: {pattern_str}")
            print(f"  重复次数: {data['count']} 次")
            print(f"  出现位置: {pos_str}")
            print()

    return True


def main():
    # 配置
    mid_file = r"D:\code\music\jnsz_pattern江南丝竹\中花六板.mid"

    # 指定要分析的声部索引 (从 0 开始)
    # 0 = 第一个声部, 1 = 第二个声部, 以此类推
    track_index = 1  # 修改这里！

    # 指定调性 (简谱输出用)
    key = "D"  # 修改这里！如 "C", "G", "D", "F" 等

    # 是否生成带重复标注的 MusicXML 文件
    generate_musicxml = True  # 修改这里！设为 True 生成 XML

    print(f"输入文件: {mid_file}")
    print(f"分析声部索引: {track_index}")
    print(f"调性: {key}")
    print("-" * 60)

    # 先列出所有声部
    mid = mido.MidiFile(mid_file)
    print(f"文件包含 {len(mid.tracks)} 个声部:")
    for i, track in enumerate(mid.tracks):
        print(f"  [{i}] {track.name if track.name else '未命名'} ({len(track)} 条消息)")
    print("-" * 60)

    # 分析
    result = analyze_beat_contents(mid_file, track_index)
    if result is None:
        return

    beat_contents, ticks_per_beat = result

    # 打印详细统计
    print_beat_statistics(beat_contents, ticks_per_beat, key)

    # 生成带重复标注的 MusicXML 文件
    if generate_musicxml:
        print("\n正在生成 MusicXML 文件...")
        generate_annotated_musicxml(mid_file, track_index, key)

    # 打印转换关系
    # print_beat_transitions(beat_contents, key)


if __name__ == "__main__":
    main()
