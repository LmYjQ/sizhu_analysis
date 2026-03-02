import mido

input_file = r"D:\code\music\jnsz_pattern江南丝竹\中花六板.mid"
output_file = r"D:\code\music\jnsz_pattern江南丝竹\中花六板_fix.mid"

mid = mido.MidiFile(input_file)
ticks_per_beat = mid.ticks_per_beat

# --- 参数设置 ---
target_beat = 10  # 从第10拍开始
shift_amount = 2  # 提前2拍

target_start_tick = target_beat * ticks_per_beat  # 10 * 4800 = 48000
shift_ticks = shift_amount * ticks_per_beat  # 2 * 4800 = 9600

print(f"ticks_per_beat = {ticks_per_beat}")
print(f"target_beat = {target_beat}, target_start_tick = {target_start_tick}")
print(f"shift_amount = {shift_amount} beats, shift_ticks = {shift_ticks}")
print()

# 遍历每个轨道
for track_idx, track in enumerate(mid.tracks):
    # 第一步：收集所有消息的绝对时间
    abs_messages = []
    current_tick = 0
    for msg in track:
        current_tick += msg.time
        abs_messages.append((current_tick, msg))

    # 第二步：找出所有音符对 (note_on, note_off)
    note_pairs = []  # [(note, velocity, start_tick, end_tick), ...]
    note_on_times = {}  # note -> (tick, velocity)

    for abs_tick, msg in abs_messages:
        if msg.type == 'note_on' and msg.velocity > 0:
            note_on_times[msg.note] = (abs_tick, msg.velocity)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in note_on_times:
                start_tick, velocity = note_on_times.pop(msg.note)
                note_pairs.append((msg.note, velocity, start_tick, abs_tick))

    print(f"轨道 {track_idx}: 找到 {len(note_pairs)} 个音符")

    # 第三步：修改需要移动的音符时间
    for i, (note, velocity, start_tick, end_tick) in enumerate(note_pairs):
        if start_tick >= target_start_tick:
            # 音符开始时间在目标位置之后，需要提前
            note_pairs[i] = (note, velocity, start_tick - shift_ticks, end_tick - shift_ticks)

    # 第四步：用修改后的音符重建轨道
    # 保持非音符消息不变
    new_messages = []

    # 先添加非音符消息
    for abs_tick, msg in abs_messages:
        if msg.type not in ('note_on', 'note_off'):
            new_messages.append((abs_tick, msg))

    # 再添加音符消息
    for note, velocity, start_tick, end_tick in note_pairs:
        # note_on
        on_msg = mido.Message('note_on', note=note, velocity=velocity)
        new_messages.append((start_tick, on_msg))
        # note_off
        off_msg = mido.Message('note_off', note=note, velocity=0)
        new_messages.append((end_tick, off_msg))

    # 第五步：按绝对时间排序，然后转回 delta time
    new_messages.sort(key=lambda x: x[0])

    # 清空轨道并重建
    track.clear()
    prev_tick = 0
    for abs_tick, msg in new_messages:
        delta = abs_tick - prev_tick
        msg.time = int(delta)
        track.append(msg)
        prev_tick = abs_tick

print(f"\n处理完成，保存为: {output_file}")
mid.save(output_file)
