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
