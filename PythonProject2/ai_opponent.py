class AiOpponent:
    """Encapsulates the AI opponent configuration and move selection."""

    def __init__(self, chess_board, depth=1):
        self.chess_board = chess_board
        self.depth = max(1, int(depth))

    def set_depth(self, depth):
        """Update the search depth used by the opponent."""
        self.depth = max(1, int(round(depth)))

    def set_board(self, chess_board):
        """Attach the opponent to a new board model after a game restart."""
        self.chess_board = chess_board

    def choose_move(self, color='b'):
        """Return the best move for color, or None when no legal move exists."""
        return self.chess_board.choose_ai_move(color, self.depth)

    def apply_move(self, move):
        """Apply an AI move and return the captured piece, if any."""
        if not move or len(move) != 4:
            raise ValueError('AI move must contain source and target coordinates')
        sr, sc, tr, tc = move
        captured = self.chess_board.board[tr][tc]
        self.chess_board.board[tr][tc] = self.chess_board.board[sr][sc]
        self.chess_board.board[sr][sc] = None
        return captured

    # Keep a descriptive alias for callers that use the old method name.
    def choose_ai_move(self, color='b'):
        return self.choose_move(color)