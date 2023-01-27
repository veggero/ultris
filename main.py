from __future__ import annotations
from subprocess import PIPE,Popen
from multiprocessing import Process
from dataclasses import dataclass, field
from typing import Optional
from time import sleep
import argparse
import threading, signal, io, sys, os

try:
    from PySide2.QtGui import QGuiApplication
    from PySide2.QtQml import QQmlApplicationEngine, QQmlDebuggingEnabler
    from PySide2.QtCore import QObject, Slot, Signal, Property
except ModuleNotFoundError:
    print('This program requires PySide2 to run!')
    exit()


if 'ULTIMATTT_PATH' in os.environ:
    ULTIMATTT = os.environ['ULTIMATTT_PATH']
else:
    print('This program relies on ultimattt, which you can find here:')
    print('https://github.com/nelhage/ultimattt')
    print('When you have installed and compiled that project, please '
          'run this script with the environment variable ULTIMATTT_PATH '
          'set to the path of the ultimattt executable, usually in '
          'ultimattt/target/release/ultimattt.')
    exit()

wins = ('1  1  1  ', ' 1  1  1 ', '  1  1  1', '111      ',
        '   111   ', '      111', '1   1   1', '  1 1 1  ')

numfy, strfy = {k: i for i, k in enumerate('abcdefghi')}, 'abcdefghi'

def change(original, index, delta):
    return original[:index] + (delta,) + original[index+1:]

@dataclass
class Position(QObject):

    turn: int = 1
    cells: tuple[tuple[int]] = tuple((0,)*9 for i in range(9))

    last_move: Optional[tuple[int, int]] = None
    move_n: int = 0
    parent: Optional[Position] = None
    lines: list[Position, ...] = field(default_factory=list)

    evaluation: float = 0
    depth: int = 0
    best_move: Optional[str] = None

    @Signal
    def eval_changed(self): pass

    @property
    def next_board(self):
        if self.last_move == None or self.boards[self.last_move[1]]: return None
        return self.last_move[1]

    @property
    def boards(self):
        return tuple(next((s.pop() for win in wins if len(s := {x for x, y in
                     zip(b, win) if y=='1'}) == 1 and s != {0}), 0)
                     for b in self.cells)

    @property
    def png(self):
        return ';'.join(['X' if self.turn == 1 else 'O',
                         ''.join('@' if i == self.next_board else '.XO'[p]
                                 for i, p in enumerate(self.boards)),
                         '/'.join(''.join('.XO'[c] for c in b)
                                  for b in self.cells)])

    def add_line(self, x, y):
        self.lines.append(p := Position(
            turn = -self.turn,
            cells = change(self.cells, x, change(self.cells[x], y, self.turn)),
            move_n = self.move_n + 1, last_move = (x, y),
            parent = self, evaluation = self.evaluation))
        return p

    def read_eval(self):
        prev_val = 0
        for line in io.TextIOWrapper(self.process.stderr, encoding="utf-8"):
            _, depth, move, val, _, _, _, _ = line.strip().split()
            self.depth, self.best_move, val = int(depth[6:]), move[5:], float(val[2:])
            val = max(-100, min(100, val))
            if self.depth > 8: self.evaluation = (val+prev_val)/2 * self.turn
            prev_val = val
            self.eval_changed.emit()
            if self.depth >= 30: return
        self.evaluation = (val+prev_val)/2 * self.turn

    def __post_init__(self):
        super().__init__()
        self.process = Popen([ULTIMATTT, 'analyze', self.png, '--limit', '2m',
                              '--table-mem', '10M'],
                             stderr=PIPE, stdout=PIPE)
        threading.Thread(target=self.read_eval).start()

    def pause_eval(self): os.kill(self.process.pid, signal.SIGSTOP)
    def resume_eval(self): os.kill(self.process.pid, signal.SIGCONT)
    def stop_eval(self):
        self.resume_eval()
        self.process.terminate()
        for line in self.lines: line.stop_eval()

@dataclass
class Match(QObject):

    position: Position = Position()
    root: Position = position

    @Signal
    def eval_changed(self): pass
    @Signal
    def pos_changed(self): pass

    def _png(self): return self.position.png
    def _allboards(self): return self.position.next_board == None

    def write_position(self, position, output=''):
        if position is self.position: output += '<b>'
        self.links[position.png] = position
        output += f"<a href='{position.png}' style='text-decoration:none;color:black'>"
        output += strfy[position.last_move[0]] + strfy[position.last_move[1]]
        if position is self.position: output += '</b>'
        return output + '</a> '

    def moves_after(self, position, i=0, output=''):
        if i == 0: self.links = {}
        if position.last_move:
            output += self.write_position(position)
        while position.lines:
            if not i % 2: output += f'<sup><i>{i//2+1}</i></sup>'
            position, i = position.lines[0], i + 1
            for line in position.parent.lines[1:]:
                output += ' <small>(' + self.moves_after(line, i) + ')</small> '
            output += self.write_position(position)
        return output.strip()

    def _moves(self): return self.moves_after(self.root)

    def _evaluation(self): return self.position.evaluation
    def _best_move(self): return self.position.best_move or '  '
    def _depth(self): return self.position.depth

    png = Property(str, _png, notify=pos_changed)
    allboards = Property(bool, _allboards, notify=pos_changed)
    moves = Property(str, _moves, notify=pos_changed)

    evaluation = Property(float, _evaluation, notify=eval_changed)
    best_move = Property(str, _best_move, notify=eval_changed)
    depth = Property(int, _depth, notify=eval_changed)

    def __post_init__(self):
        super().__init__()
        self.position.eval_changed.connect(self.eval_changed)

    def new_position(self, new):
        self.position.pause_eval()
        self.position.eval_changed.disconnect(self.eval_changed)
        self.position = new
        self.position.eval_changed.connect(self.eval_changed)
        self.position.resume_eval()
        self.pos_changed.emit()
        self.eval_changed.emit()

    def load_hero(self, hero: str):
        t = ['NW', 'N', 'NE', 'W', 'C', 'E', 'SW', 'S', 'SE']
        for move in hero.split():
            x, _, y = move.partition('/')
            x, y = t.index(x), t.index(y)
            self.add_move(x, y)
        self.new_position(self.root)

    @Slot(int, int)
    def add_move(self, x, y):
        if (p := next((l for l in self.position.lines if l.last_move == (x, y)), None)):
            return self.new_position(p)
        self.new_position(self.position.add_line(x, y))

    @Slot()
    def back(self):
        if not self.position.parent: return
        self.new_position(self.position.parent)

    @Slot()
    def forward(self):
        if not self.position.lines: return
        self.new_position(self.position.lines[0])

    @Slot()
    def delete(self):
        if not self.position.parent: return
        i = self.position.parent.lines.index(self.position)
        self.new_position(self.position.parent)
        self.position.lines[i].stop_eval()
        del self.position.lines[i]
        self.pos_changed.emit()

    @Slot()
    def prev_line(self):
        if not self.position.parent: return
        i = self.position.parent.lines.index(self.position)
        if i == 0: return
        self.new_position(self.position.parent.lines[i-1])

    @Slot()
    def next_line(self):
        if not self.position.parent: return
        i = self.position.parent.lines.index(self.position)
        if i == len(self.position.parent.lines) - 1: return
        self.new_position(self.position.parent.lines[i+1])

    @Slot(str)
    def link(self, link):
        self.new_position(self.links[link])

m = Match()

if len(sys.argv) > 1: m.load_hero(sys.argv[1])

app = QGuiApplication(sys.argv)
try:
    qml = QQmlApplicationEngine('main.qml')
except Exception as e:
    print('Please run the script in the root folder, along main.qml')
qml.rootContext().setContextProperty("py", m)
app.exec_()
m.root.stop_eval()

