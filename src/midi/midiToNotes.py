from mido import MidiFile
from typing import List, TypedDict
import json

MIDI_INSTRUMENTS = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano", "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavi",
    "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ", "Accordion", "Harmonica", "Tango Accordion",
    "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)", "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar", "Distortion Guitar", "Guitar Harmonics",
    "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass", "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2",
    "Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani",
    "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2", "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit",
    "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn", "Brass Section", "Synth Brass 1", "Synth Brass 2",
    "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet",
    "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)", "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",
    "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba", "Bagpipe", "Fiddle", "Shanai",
    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal",
    "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot"
]


class MessageItem(TypedDict):
    message: str
    real_tick: float


class NotesMap(TypedDict):
    notes: list[int]
    real_tick: float
    frame: float


class PitchWheelItem(TypedDict):
    pitch_wheel: int
    real_tick: float


class MidiProcessor:
    def __init__(self, midi_name: str, track_numbers: List[int] = [], channel_number: int = -1, FPS: int = 30):
        self.midi_file_path = f'asset/midi/{midi_name}.mid'
        self.track_numbers = track_numbers
        self.channel_number = channel_number
        self.FPS = FPS

    def calculate_frame(self, tempo_changes: list[tuple], ticks_per_beat: int, real_tick: float) -> float:
        total_frames = 0
        for i in range(len(tempo_changes)):
            current_track, current_tempo, current_time = tempo_changes[i]

            # 如果当前的时间已经超过了real_tick，那么就停止计算
            if current_time > real_tick:
                break

            # 获取下一个时间点，如果没有下一个时间点，或者下一个时间点超过了real_tick，那么就使用real_tick
            next_time = min(tempo_changes[i + 1][2] if i + 1 <
                            len(tempo_changes) else real_tick, real_tick)

            # 计算当前时间点和下一个时间点之间的秒数
            seconds = (next_time - current_time) * \
                current_tempo / (ticks_per_beat * 1000000)

            # 将秒数转换为帧数
            frames = seconds * self.FPS

            # 累加帧数
            total_frames += frames

        return total_frames

    def get_tempo_changes(self) -> tuple[List[tuple], int]:
        midi_file = MidiFile(self.midi_file_path)
        tick_per_beat: int = midi_file.ticks_per_beat
        tempo_changes = []
        for i, track in enumerate(midi_file.tracks):
            absolute_time = 0
            for msg in track:
                absolute_time += msg.time
                if msg.type == 'set_tempo':
                    tempo_changes.append((i, msg.tempo, absolute_time))
        return tempo_changes, tick_per_beat

    def export_midi_info(self) -> str:
        result = ''
        midi_file = MidiFile(self.midi_file_path)

        with open('asset/temp/current_midi_info.txt', 'w', encoding='utf-8') as f:
            for message in midi_file.tracks[0]:
                f.write(str(message) + '\n')

        for i, track in enumerate(midi_file.tracks):
            result += f'Track {i}: {track.name}\n'
            for msg in track:
                if msg.type == 'program_change':
                    channel = msg.channel
                    instrument = MIDI_INSTRUMENTS[msg.program]
                    result += f'Track {i}, Channel {channel}: {instrument}\n'

        return result

    def midiToPianoNotes(self, higher_octave: bool = False) -> tuple[List[NotesMap], List[PitchWheelItem], list[MessageItem]]:
        """    
        :param midi_file_path: path of input midi file. 输入midi文件路径
        :param useTrack: track number to use. 使用的轨道编号
        :param useChannel: channel number to use. 使用的通道编号，如果使用-1表示不限制
        :return: notes and beat in the midi file. 返回midi文件中指定轨道的音符和时间信息
        """
        midTracks = []
        try:
            for track in self.track_numbers:
                midTracks.append(MidiFile(self.midi_file_path).tracks[track])
        except:
            midTracks.append(MidiFile(self.midi_file_path).tracks[0])

        notes_maps: list[NotesMap] = []
        pitch_wheel_map: list[PitchWheelItem] = []
        messages: list[MessageItem] = []

        for midTrack in midTracks:
            note = []
            real_tick: float = 0
            pre_tick: float = 0
            for message in midTrack:
                ticks = message.time
                real_tick += ticks

                if not hasattr(message, 'channel'):
                    continue

                if message.channel == self.channel_number or self.channel_number == -1:
                    messages.append(
                        {'message': str(message), 'real_tick': real_tick})
                    if message.type == 'note_on':
                        message_note = message.note if not higher_octave else message.note + 12
                        note.append(message_note)
                    else:
                        # 结束音符的收集
                        if len(note) == 0:
                            continue
                        # 将note里的元素按大小排序
                        notes = sorted(note)
                        notes_maps.append(
                            {"notes": notes, "real_tick": pre_tick, "frame": 0})
                        note = []

                    if message.type == 'pitchwheel':
                        pitch_wheel_map.append(
                            {"pitch_wheel": message.pitch, "real_tick": pre_tick})

                pre_tick = real_tick

        # notes_map，pitch_wheel_map,messages都按real_tick排序
        notes_map = sorted(notes_maps, key=lambda x: x['real_tick'])
        pitch_wheel_map = sorted(pitch_wheel_map, key=lambda x: x['real_tick'])
        messages = sorted(messages, key=lambda x: x['real_tick'])

        return notes_maps, pitch_wheel_map, messages

    def processedNotes(self, chord_notes: list[int], min: int, max: int) -> list[int]:
        """
        :param chord_notes: multiple notes in a chord. 和弦中的多个音符
        :return: simplified notes. 精简后的音符
        """
        return self.simplifyNotes(self.compressNotes(chord_notes, min, max))

    def compressNotes(self, chord_notes: List[int], min: int = 21, max: int = 108) -> List[int]:
        """
        :param chord_notes: input notes. 输入音符
        :param min: minimum note on piano. 钢琴上的最低音符
        :param max: maximum note on piano. 钢琴上的最高音符
        :return: compressed notes. 压缩后的音符
        """
        compressed_chord_notes = []
        for note in chord_notes:
            while note < min:
                note += 12
            while note > max:
                note -= 12
            if note not in compressed_chord_notes:
                compressed_chord_notes.append(note)
        compressed_chord_notes = sorted(compressed_chord_notes)

        return compressed_chord_notes

    def simplifyNotes(self, chord_notes: List[int]) -> List[int]:
        """
        :param chord_notes: input notes. 输入音符
        :return: simplified notes. 精简后的音符
        """
        """
        here is the rule of simplifying notes:
        1. if the number of notes is not greater than 6, return the notes directly.    
        2. remove the notes that are octves of the lowest note or the highest note.
        3. if there are still notes need to be removed, randomly remove the notes from the middle notes.
        
        精简音符的规则如下：
        1. 如果音符数量不大于10，直接返回音符。
        2. 移除与最低音或者最高音有八度关系的音符。
        3. 如果还有音符需要移除，随机从中间音符里挑出来需要移除的音符。
        """
        if len(chord_notes) <= 10:
            return chord_notes

        lowest_note = chord_notes[0]
        highest_note = chord_notes[-1]
        middle_notes = chord_notes[1:-2]
        amount_of_notes_need_to_remove = len(chord_notes) - 10
        amount_of_removed_notes = 0

        for note in middle_notes:
            # 如果中间音符与最高音或者最高低有八度关系，可以移除
            if note - lowest_note % 12 == 0 or highest_note - note % 12 == 0:
                middle_notes.remove(note)
                amount_of_removed_notes += 1
            if amount_of_removed_notes == amount_of_notes_need_to_remove:
                break

        # 如果经过上面的步骤，还有音符需要移除，那么从正中间音符里挑出来需要移除的音符，这样做的目的是确保音符的分布是靠近两端，可以分别由左右手同时演奏的，而不至于出现某些音符在正中间，左手和右手同时都无法按到的情况
        while amount_of_removed_notes < amount_of_notes_need_to_remove:
            remove_note_index = int(len(middle_notes) / 2)
            middle_notes.pop(remove_note_index)
            amount_of_removed_notes += 1

        simplified_chord_notes = [lowest_note] + middle_notes + [highest_note]

        return simplified_chord_notes

    def generate_notes_map_and_messages(self, higher_octave: bool = False) -> list[NotesMap]:
        """
        :return: notes_map, pitch_wheel_map, messages. 音符映射，音高映射，消息
        """
        notes_map_file = "asset/temp/notes_map.json"
        pitch_wheel_map_file = "asset/temp/pitch_wheel_map.json"
        messages_file = "asset/temp/messages.json"

        tempo_changes, ticks_per_beat = self.get_tempo_changes()
        notes_maps, pitch_wheel_map, messages = self.midiToPianoNotes(
            higher_octave)

        # 保存notes_map,pitch_wheel_map,messages到文件

        with open(pitch_wheel_map_file, "w") as f:
            json.dump(pitch_wheel_map, f, indent=4)
            print("pitch_wheel_map 保存到了", pitch_wheel_map_file)

        with open(messages_file, "w") as f:
            json.dump(messages, f, indent=4)
            print("messages 保存到了", messages_file)

        print(f'全曲的速度变化是:')
        for track, tempo, tick in tempo_changes:
            print(f'在{track}轨，tick为{tick}时，速度变为{tempo}')

        print(f'\n全曲的每拍tick数是:{ticks_per_beat}\n')

        # 计算总时长
        total_tick = notes_maps[-1].get('real_tick', 0)
        total_frame = self.calculate_frame(
            tempo_changes, ticks_per_beat, total_tick)
        total_time = total_frame/self.FPS
        print(
            f'如果以{self.FPS}的fps做成动画，一共是{total_tick} ticks, 合计{total_frame}帧, 约{total_time}秒')

        # 将notes_map里的real_tick转换为frame
        for notes_map in notes_maps:
            notes_map['frame'] = self.calculate_frame(
                tempo_changes, ticks_per_beat, notes_map['real_tick'])

        with open(notes_map_file, "w") as f:
            json.dump(notes_maps, f, indent=4)
            print("notes_map 保存到了", notes_map_file)

        return notes_maps


if __name__ == '__main__':
    pass
