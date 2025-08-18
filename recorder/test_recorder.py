# run_recorder.py
from recorder.recorder import Recorder
from recorder.recorderPool import RecorderPool
from hand.hand import Hand
from hand.finger import Finger
from midi.midiToNotes import NotesMap
from piano.piano import Piano

if __name__ == '__main__':
    # 初始化钢琴
    piano = Piano()

    # 初始化左右手,左手放在C3，右手放在C4
    left_hand = Hand([
        Finger(0, piano.note_to_key(48)),
        Finger(1, piano.note_to_key(50)),
        Finger(2, piano.note_to_key(52)),
        Finger(3, piano.note_to_key(53)),
        Finger(4, piano.note_to_key(55))
    ], piano, True)

    right_hand = Hand([
        Finger(0, piano.note_to_key(60), False),
        Finger(1, piano.note_to_key(62), False),
        Finger(2, piano.note_to_key(64), False),
        Finger(3, piano.note_to_key(65), False),
        Finger(4, piano.note_to_key(67), False)
    ], piano, False)

    init_real_tick = 0.0
    init_real_ticks = []

    # 初始化recorder
    recorder = Recorder(piano, [left_hand], [right_hand],
                        0, init_real_tick, init_real_ticks)

    current_real_tick = 167616
    current_notes = [63, 66, 70, 73, 77]
    current_notes_map = NotesMap(
        notes=current_notes, real_tick=current_real_tick)

    # 初始化recorderPool
    pool_size = 100
    recorder_pool = RecorderPool([recorder], pool_size, 0)

    recorder_pool.update_recorder_pool(current_notes_map, 13, 4)
