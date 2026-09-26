COLS = 9
ROWS = 10

# 棋盘基础判断
def inside_board(r,c):
    return 0 <= r < ROWS and 0 <= c < COLS

# Orientation flag: when True, red side is at top (rows 0-2). Default False (red at bottom).
RED_AT_TOP = False

def inside_palace(r,c,color):
    # Palace columns always 3..5. Rows depend on orientation.
    if RED_AT_TOP:
        if color == 'r':
            return 0 <= r <= 2 and 3 <= c <= 5
        else:
            return 7 <= r <= 9 and 3 <= c <= 5
    else:
        if color == 'r':
            return 7 <= r <= 9 and 3 <= c <= 5
        else:
            return 0 <= r <= 2 and 3 <= c <= 5

# 查找将位置
def find_general(board, color):
    target = color + 'K'
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == target:
                return (r,c)
    return None

# 判断是否同色/敌对
def is_enemy(p1, p2):
    if not p1 or not p2: return False
    return p1[0] != p2[0]

# 生成伪合法走法（不考虑自将）
def generate_pseudo_moves(board, r, c):
    piece = board[r][c]
    if not piece: return []
    color, code = piece[0], piece[1]
    moves = []
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]
    if code == 'R':
        for dr,dc in dirs:
            nr, nc = r+dr, c+dc
            while inside_board(nr,nc):
                if not board[nr][nc]:
                    moves.append((nr,nc))
                else:
                    if is_enemy(piece, board[nr][nc]):
                        moves.append((nr,nc))
                    break
                nr += dr; nc += dc
    elif code == 'C':
        # 非吃子走法
        for dr,dc in dirs:
            nr, nc = r+dr, c+dc
            while inside_board(nr,nc) and not board[nr][nc]:
                moves.append((nr,nc))
                nr += dr; nc += dc
        # 吃子需有屏障
        for dr,dc in dirs:
            nr, nc = r+dr, c+dc
            while inside_board(nr,nc) and not board[nr][nc]:
                nr += dr; nc += dc
            if inside_board(nr,nc):
                nr2, nc2 = nr+dr, nc+dc
                while inside_board(nr2,nc2) and not board[nr2][nc2]:
                    nr2 += dr; nc2 += dc
                if inside_board(nr2,nc2) and is_enemy(piece, board[nr2][nc2]):
                    moves.append((nr2,nc2))
    elif code == 'H':
        leaps = [(-2,-1),(-2,1),(2,-1),(2,1),(-1,-2),(1,-2),(-1,2),(1,2)]
        for dr,dc in leaps:
            nr, nc = r+dr, c+dc
            if not inside_board(nr,nc): continue
            if abs(dr) == 2:
                leg = (r + dr//2, c)
            else:
                leg = (r, c + dc//2)
            if board[leg[0]][leg[1]]: continue
            if not board[nr][nc] or is_enemy(piece, board[nr][nc]):
                moves.append((nr,nc))
    elif code == 'E':
        deltas = [(-2,-2),(-2,2),(2,-2),(2,2)]
        for dr,dc in deltas:
            nr, nc = r+dr, c+dc
            if not inside_board(nr,nc): continue
            mid = (r+dr//2, c+dc//2)
            if board[mid[0]][mid[1]]: continue
            # 禁止过河：依据棋盘方向（RED_AT_TOP）判断
            if not RED_AT_TOP:
                if color == 'r' and nr < 5: continue
                if color == 'b' and nr > 4: continue
            else:
                if color == 'r' and nr > 4: continue
                if color == 'b' and nr < 5: continue
            if not board[nr][nc] or is_enemy(piece, board[nr][nc]):
                moves.append((nr,nc))
    elif code == 'A':
        for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr, nc = r+dr, c+dc
            if not inside_board(nr,nc): continue
            if not inside_palace(nr,nc,color): continue
            if not board[nr][nc] or is_enemy(piece, board[nr][nc]):
                moves.append((nr,nc))
    elif code == 'K':
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if not inside_board(nr,nc): continue
            if not inside_palace(nr,nc,color): continue
            if not board[nr][nc] or is_enemy(piece, board[nr][nc]):
                moves.append((nr,nc))
    elif code == 'P':
        # 反转前进方向：红向下（+1），黑向上（-1）
        forward = 1 if color == 'r' else -1
        # 仅允许向前移动一格
        nr, nc = r + forward, c
        if inside_board(nr, nc) and (not board[nr][nc] or is_enemy(piece, board[nr][nc])):
            moves.append((nr, nc))
        # 过河后可以左右移动一格（水平移动）
        crossed = (color == 'r' and r >= 5) or (color == 'b' and r <= 4)
        if crossed:
            for dc in (-1, 1):
                nr, nc = r, c + dc
                if inside_board(nr, nc) and (not board[nr][nc] or is_enemy(piece, board[nr][nc])):
                    moves.append((nr, nc))
    return moves

# 将帅相对
def generals_face(board):
    g1 = find_general(board, 'r')
    g2 = find_general(board, 'b')
    if not g1 or not g2: return False
    if g1[1] != g2[1]: return False
    c = g1[1]
    start = min(g1[0], g2[0])+1
    end = max(g1[0], g2[0])
    for rr in range(start, end):
        if board[rr][c]:
            return False
    return True

# 将军检测
def is_in_check(board, color):
    gpos = find_general(board, color)
    if not gpos: return False
    opp = 'b' if color == 'r' else 'r'
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r][c]
            if p and p[0] == opp:
                moves = generate_pseudo_moves(board, r, c)
                if gpos in moves:
                    return True
                if p[1] == 'K' and c == gpos[1]:
                    blocked = False
                    step = 1 if r < gpos[0] else -1
                    for rr in range(r+step, gpos[0], step):
                        if board[rr][c]:
                            blocked = True; break
                    if not blocked:
                        return True
    return False

# 是否导致自将（用于合法性检测）
def move_causes_self_check(board, sr, sc, tr, tc):
    board2 = [row[:] for row in board]
    piece = board2[sr][sc]
    board2[tr][tc] = piece
    board2[sr][sc] = None
    if generals_face(board2):
        return True
    color = piece[0]
    return is_in_check(board2, color)

# 是否存在任一合法着（用于将死判定）
def has_any_legal_move(board, color):
    for r in range(ROWS):
        for c in range(COLS):
            p = board[r][c]
            if p and p[0] == color:
                for (nr,nc) in generate_pseudo_moves(board, r, c):
                    if not move_causes_self_check(board, r, c, nr, nc):
                        return True
    return False
