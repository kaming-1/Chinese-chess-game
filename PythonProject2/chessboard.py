import random
import chess_pieces as cp
from chess_pieces import inside_board, inside_palace, find_general, generate_pseudo_moves as gp_moves, is_enemy as cp_is_enemy, is_in_check as cp_is_in_check, generals_face as cp_generals_face, move_causes_self_check as cp_move_causes_self_check, has_any_legal_move as cp_has_any_legal_move

COLS = 9
ROWS = 10

# 简单棋子映射：颜色前缀 r/b 与棋子代码
PIECE_CHARS = {
    'R': '车', 'H': '马', 'E': '相', 'A': '仕', 'K': '帅', 'C': '炮', 'P': '兵'
}

INITIAL_BOARD = [
    ['rR','rH','rE','rA','rK','rA','rE','rH','rR'],
    [None]*9,
    [None,'rC',None,None,None,None,None,'rC',None],
    ['rP',None,'rP',None,'rP',None,'rP',None,'rP'],
    [None]*9,
    [None]*9,
    ['bP',None,'bP',None,'bP',None,'bP',None,'bP'],
    [None,'bC',None,None,None,None,None,'bC',None],
    [None]*9,
    ['bR','bH','bE','bA','bK','bA','bE','bH','bR'],
]

# 设置棋盘方向标志，通知 chess_pieces 模块红方是否位于顶部（RED_AT_TOP）
try:
    rpos = next((i for i,row in enumerate(INITIAL_BOARD) if 'rK' in row), None)
    cp.RED_AT_TOP = (rpos == 0)
except Exception:
    cp.RED_AT_TOP = False

class ChessBoard:
    """Encapsulates board state and pure board operations (no GUI)."""
    def __init__(self, board=None):
        self.board = [row[:] for row in (board if board is not None else INITIAL_BOARD)]

    def reset(self):
        self.board = [row[:] for row in INITIAL_BOARD]

    def occupied(self, r, c):
        return self.board[r][c] is not None

    def is_enemy(self, p1, p2):
        return cp_is_enemy(p1, p2)

    def generate_pseudo_moves(self, r, c):
        return gp_moves(self.board, r, c)

    def is_in_check(self, color):
        return cp_is_in_check(self.board, color)

    def generals_face(self):
        return cp_generals_face(self.board)

    def move_causes_self_check(self, sr, sc, tr, tc):
        return cp_move_causes_self_check(self.board, sr, sc, tr, tc)

    def has_any_legal_move(self, color):
        return cp_has_any_legal_move(self.board, color)

    def choose_ai_move(self, color, ai_depth=1):
        """Alpha-beta minimax for selecting an AI move. Returns (sr,sc,tr,tc) or None."""
        piece_values = {'K': 10000, 'R': 500, 'H': 300, 'E': 250, 'A': 200, 'C': 450, 'P': 100}

        def evaluate_board():
            s = 0
            for r in range(ROWS):
                for c in range(COLS):
                    p = self.board[r][c]
                    if not p:
                        continue
                    code = p[1]
                    v = piece_values.get(code, 0)
                    s += v if p[0] == 'r' else -v
            return s

        def generate_moves_for(color_):
            res = []
            for r in range(ROWS):
                for c in range(COLS):
                    p = self.board[r][c]
                    if not p or p[0] != color_:
                        continue
                    targets = self.generate_pseudo_moves(r, c)
                    for tr, tc in targets:
                        if not self.move_causes_self_check(r, c, tr, tc):
                            res.append((r, c, tr, tc))
            return res

        def minimax(depth, alpha, beta, is_red_turn):
            moves = generate_moves_for('r' if is_red_turn else 'b')
            if depth == 0 or not moves:
                if not moves:
                    if self.is_in_check('r' if is_red_turn else 'b'):
                        return -999999 if is_red_turn else 999999
                    else:
                        return 0
                return evaluate_board()
            if is_red_turn:
                value = -10**9
                for mv in moves:
                    sr, sc, tr, tc = mv
                    captured = self.board[tr][tc]
                    self.board[tr][tc] = self.board[sr][sc]
                    self.board[sr][sc] = None
                    val = minimax(depth-1, alpha, beta, False)
                    # revert
                    self.board[sr][sc] = self.board[tr][tc]
                    self.board[tr][tc] = captured
                    if val > value:
                        value = val
                    if value > alpha:
                        alpha = value
                    if alpha >= beta:
                        break
                return value
            else:
                value = 10**9
                for mv in moves:
                    sr, sc, tr, tc = mv
                    captured = self.board[tr][tc]
                    self.board[tr][tc] = self.board[sr][sc]
                    self.board[sr][sc] = None
                    val = minimax(depth-1, alpha, beta, True)
                    # revert
                    self.board[sr][sc] = self.board[tr][tc]
                    self.board[tr][tc] = captured
                    if val < value:
                        value = val
                    if value < beta:
                        beta = value
                    if alpha >= beta:
                        break
                return value

        candidates = generate_moves_for(color)
        if not candidates:
            return None
        best_moves = []
        if color == 'r':
            best_score = -10**9
            for mv in candidates:
                sr, sc, tr, tc = mv
                captured = self.board[tr][tc]
                self.board[tr][tc] = self.board[sr][sc]
                self.board[sr][sc] = None
                score = minimax(ai_depth-1, -10**9, 10**9, False)
                # revert
                self.board[sr][sc] = self.board[tr][tc]
                self.board[tr][tc] = captured
                if score > best_score:
                    best_score = score
                    best_moves = [mv]
                elif score == best_score:
                    best_moves.append(mv)
        else:
            best_score = 10**9
            for mv in candidates:
                sr, sc, tr, tc = mv
                captured = self.board[tr][tc]
                self.board[tr][tc] = self.board[sr][sc]
                self.board[sr][sc] = None
                score = minimax(ai_depth-1, -10**9, 10**9, True)
                # revert
                self.board[sr][sc] = self.board[tr][tc]
                self.board[tr][tc] = captured
                if score < best_score:
                    best_score = score
                    best_moves = [mv]
                elif score == best_score:
                    best_moves.append(mv)
        return random.choice(best_moves) if best_moves else random.choice(candidates)
