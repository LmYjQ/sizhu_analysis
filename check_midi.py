#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看 MIDI 文件信息"""

import mido

input_file = r"D:\code\music\jnsz_pattern江南丝竹\中花六板.mid"

mid = mido.MidiFile(input_file)

print(f"MIDI 文件: {input_file}")
print(f"格式: Type {mid.type}")
print(f"轨道数: {len(mid.tracks)}")
print(f"Ticks per beat: {mid.ticks_per_beat}")
print()

for i, track in enumerate(mid.tracks):
    print(f"轨道 {i}: {track.name if track.name else '未命名'}")
    print(f"  消息数: {len(track)}")

    # 统计各类消息
    program_changes = 0
    notes = 0
    tempos = 0

    for msg in track:
        if msg.type == 'program_change':
            program_changes += 1
        elif msg.type == 'note_on' or msg.type == 'note_off':
            notes += 1
        elif msg.type == 'set_tempo':
            tempos += 1

    print(f"  音符消息: {notes}, 程序切换: {program_changes}, tempo: {tempos}")
    print()

# 显示 tempo 信息
print("=" * 40)
print("Tempo 信息:")
for track in mid.tracks:
    for msg in track:
        if msg.type == 'set_tempo':
            bpm = mido.tempo2bpm(msg.tempo)
            print(f"  Tempo: {msg.tempo} 微秒/拍 = {bpm:.1f} BPM")

# 打印第二声部前四拍（第一个小节）的音符
print("\n" + "=" * 40)
print("Part 2 (first 4 beats / bar 1) notes:")

track1 = mid.tracks[1]  # 第二声部
ticks_per_beat = mid.ticks_per_beat
four_beats = 4 * ticks_per_beat  # 前四拍

current_time = 0
notes_on = {}  # 记录当前正在播放的音符
notes_data = []  # 收集音符数据

for msg in track1:
    current_time += msg.time

    if current_time > four_beats:
        break

    if msg.type == 'note_on' and msg.velocity > 0:
        notes_on[msg.note] = current_time
    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
        if msg.note in notes_on:
            start_time = notes_on.pop(msg.note)
            duration = current_time - start_time
            notes_data.append((msg.note, start_time, duration))

# 按开始时间排序显示
note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

print(f"ticks_per_beat = {ticks_per_beat}")
print(f"前四拍 = {four_beats} ticks")
print()
for note, start, duration in sorted(notes_data, key=lambda x: x[1]):
    note_name = note_names[note % 12] + str(note // 12 - 1)
    beat_start = start / ticks_per_beat
    beat_duration = duration / ticks_per_beat
    print(f"  {note_name:>3} ({note:>3})  start={beat_start:>5.2f} beats  duration={beat_duration:>5.2f} beats")
