"""
Miku Chess - 游戏状态管理
管理棋盘状态、回合、玩家等
"""

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import copy

from game_logic import (
    Piece, PieceType, Team, Move, GameLogic,
    is_in_blue_zone, is_in_red_zone
)


class GameStatus(Enum):
    """游戏状态"""
    WAITING = "waiting"          # 等待玩家加入
    PLAYING = "playing"          # 游戏进行中
    BLUE_WIN = "blue_win"        # 蓝方胜利
    RED_WIN = "red_win"          # 红方胜利
    DRAW = "draw"                # 和棋


class GameMode(Enum):
    """游戏模式"""
    LOCAL = "local"              # 本地双人对战
    ONLINE = "online"            # 在线对战
    AI = "ai"                    # AI对战（预留）


@dataclass
class GameState:
    """游戏状态"""
    game_id: str
    mode: GameMode
    status: GameStatus
    board: List[List[Optional[Piece]]]
    current_team: Team
    turn_number: int
    blue_magic_alive: bool
    red_magic_alive: bool
    # 红方第11回合双倍移动状态
    red_double_move_active: bool = False
    red_first_move_done: bool = False
    red_first_move_pos: Optional[Tuple[int, int]] = None
    # 移动历史
    move_history: List[Dict] = field(default_factory=list)
    # 玩家信息 (在线模式)
    blue_player_id: Optional[str] = None
    red_player_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为可JSON序列化的字典"""
        board_data = []
        for row in self.board:
            row_data = []
            for piece in row:
                if piece is None:
                    row_data.append(None)
                else:
                    row_data.append(piece.to_dict())
            board_data.append(row_data)
        
        return {
            "game_id": self.game_id,
            "mode": self.mode.value,
            "status": self.status.value,
            "board": board_data,
            "current_team": self.current_team.value,
            "turn_number": self.turn_number,
            "blue_magic_alive": self.blue_magic_alive,
            "red_magic_alive": self.red_magic_alive,
            "red_double_move_active": self.red_double_move_active,
            "red_first_move_done": self.red_first_move_done,
            "red_first_move_pos": list(self.red_first_move_pos) if self.red_first_move_pos else None,
            "move_history": self.move_history,
            "blue_player_id": self.blue_player_id,
            "red_player_id": self.red_player_id
        }


def create_initial_board() -> List[List[Optional[Piece]]]:
    """创建初始棋盘"""
    # 创建空棋盘 10行9列
    board = [[None for _ in range(9)] for _ in range(10)]
    
    # 蓝方棋子 (行0-4)
    # 0A、0B、0C、0G、0H、0I是进攻棋
    for col in [0, 1, 2, 6, 7, 8]:  # A, B, C, G, H, I
        board[0][col] = Piece(PieceType.ATTACK, Team.BLUE)
    
    # 0E是胜点棋
    board[0][4] = Piece(PieceType.GENERAL, Team.BLUE)  # E
    
    # 0D、0F是应援棋
    board[0][3] = Piece(PieceType.SUPPORT, Team.BLUE)  # D
    board[0][5] = Piece(PieceType.SUPPORT, Team.BLUE)  # F
    
    # 2A、2B、2C、2D、2F、2G、2H、2I是防守棋
    for col in [0, 1, 2, 3, 5, 6, 7, 8]:  # A, B, C, D, F, G, H, I
        board[2][col] = Piece(PieceType.DEFENSE, Team.BLUE)
    
    # 2E是魔法阵
    board[2][4] = Piece(PieceType.MAGIC, Team.BLUE)  # E
    
    # 红方棋子 (行5-9)
    # 9A、9B、9C、9G、9H、9I是进攻棋
    for col in [0, 1, 2, 6, 7, 8]:  # A, B, C, G, H, I
        board[9][col] = Piece(PieceType.ATTACK, Team.RED)
    
    # 9E是胜点棋
    board[9][4] = Piece(PieceType.GENERAL, Team.RED)  # E
    
    # 9D、9F是应援棋
    board[9][3] = Piece(PieceType.SUPPORT, Team.RED)  # D
    board[9][5] = Piece(PieceType.SUPPORT, Team.RED)  # F
    
    # 7A、7B、7C、7D、7F、7G、7H、7I是防守棋
    for col in [0, 1, 2, 3, 5, 6, 7, 8]:  # A, B, C, D, F, G, H, I
        board[7][col] = Piece(PieceType.DEFENSE, Team.RED)
    
    # 7E是魔法阵
    board[7][4] = Piece(PieceType.MAGIC, Team.RED)  # E
    
    return board


def create_game(mode: GameMode, player_id: Optional[str] = None) -> GameState:
    """创建新游戏"""
    game_id = str(uuid.uuid4())[:8]
    
    game = GameState(
        game_id=game_id,
        mode=mode,
        status=GameStatus.WAITING if mode == GameMode.ONLINE else GameStatus.PLAYING,
        board=create_initial_board(),
        current_team=Team.RED,  # 红方先行
        turn_number=1,
        blue_magic_alive=True,
        red_magic_alive=True
    )
    
    # 在线模式下，创建者为红方
    if mode == GameMode.ONLINE and player_id:
        game.red_player_id = player_id
    
    return game


class GameManager:
    """游戏管理器 - 管理所有游戏实例"""
    
    def __init__(self):
        self.games: Dict[str, GameState] = {}
    
    def create_game(self, mode: GameMode, player_id: Optional[str] = None) -> GameState:
        """创建新游戏"""
        game = create_game(mode, player_id)
        self.games[game.game_id] = game
        return game
    
    def get_game(self, game_id: str) -> Optional[GameState]:
        """获取游戏"""
        return self.games.get(game_id)
    
    def join_game(self, game_id: str, player_id: str) -> Optional[GameState]:
        """加入游戏（在线模式）"""
        game = self.games.get(game_id)
        if not game:
            return None
        
        if game.mode != GameMode.ONLINE:
            return None
        
        if game.status != GameStatus.WAITING:
            return None
        
        # 分配蓝方
        if game.blue_player_id is None:
            game.blue_player_id = player_id
            game.status = GameStatus.PLAYING
            return game
        
        return None
    
    def get_frozen_positions(self, game: GameState) -> List[Tuple[int, int]]:
        """获取被冻结的位置（第11回合蓝方魔法效果）"""
        frozen = []
        if game.turn_number == 11 and game.blue_magic_alive and game.current_team == Team.RED:
            # 蓝色区域的红方棋子被冻结
            for row in range(5):  # 行0-4是蓝色区域
                for col in range(9):
                    piece = game.board[row][col]
                    if piece and piece.team == Team.RED:
                        frozen.append((row, col))
        return frozen
    
    def make_move(self, game_id: str, move: Move, player_id: Optional[str] = None) -> Dict:
        """
        执行移动
        返回移动结果
        """
        game = self.games.get(game_id)
        if not game:
            return {"success": False, "error": "游戏不存在"}
        
        if game.status != GameStatus.PLAYING:
            return {"success": False, "error": "游戏未在进行中"}
        
        # 在线模式下验证玩家身份
        if game.mode == GameMode.ONLINE and player_id:
            if game.current_team == Team.RED and player_id != game.red_player_id:
                return {"success": False, "error": "不是你的回合"}
            if game.current_team == Team.BLUE and player_id != game.blue_player_id:
                return {"success": False, "error": "不是你的回合"}
        
        from_row, from_col = move.from_pos
        to_row, to_col = move.to_pos
        
        piece = game.board[from_row][from_col]
        if not piece:
            return {"success": False, "error": "没有选中棋子"}
        
        if piece.team != game.current_team:
            return {"success": False, "error": "不是你的棋子"}
        
        # 获取冻结位置
        frozen_positions = self.get_frozen_positions(game)
        
        # 检查是否是红方第11回合的第二次移动
        is_second_move = game.red_first_move_done and game.red_double_move_active
        
        # 第二次移动只能移动第一次移动的那个棋子
        if is_second_move:
            if game.red_first_move_pos != move.from_pos:
                return {"success": False, "error": "第二次移动只能移动同一个棋子"}
        
        # 验证移动合法性
        valid_moves = GameLogic.get_valid_moves(
            game.board, move.from_pos, game.current_team,
            game.blue_magic_alive, game.red_magic_alive, game.turn_number,
            is_second_move, frozen_positions
        )
        
        if move.to_pos not in valid_moves:
            return {"success": False, "error": "非法移动"}
        
        # 执行移动
        captured_piece = game.board[to_row][to_col]
        game.board[to_row][to_col] = piece
        game.board[from_row][from_col] = None
        
        # 检查是否吃掉了魔法阵
        if captured_piece:
            if captured_piece.piece_type == PieceType.MAGIC:
                if captured_piece.team == Team.BLUE:
                    game.blue_magic_alive = False
                else:
                    game.red_magic_alive = False
            
            # 检查是否吃掉了胜点棋
            if captured_piece.piece_type == PieceType.GENERAL:
                if captured_piece.team == Team.BLUE:
                    game.status = GameStatus.RED_WIN
                else:
                    game.status = GameStatus.BLUE_WIN
        
        # 记录移动历史
        game.move_history.append({
            "turn": game.turn_number,
            "team": game.current_team.value,
            "move": move.to_dict(),
            "captured": captured_piece.to_dict() if captured_piece else None
        })
        
        # 处理回合切换
        result = {
            "success": True,
            "captured": captured_piece.to_dict() if captured_piece else None,
            "game_status": game.status.value
        }
        
        # 第11回合红方双倍移动逻辑
        if (game.turn_number == 11 and 
            game.current_team == Team.RED and 
            game.red_magic_alive and
            game.status == GameStatus.PLAYING):
            
            if not game.red_first_move_done:
                # 第一次移动
                # 检查棋子是否从红色区域出发
                if is_in_red_zone(from_row):
                    # 检查移动后是否还在红色区域
                    if is_in_red_zone(to_row):
                        # 仍在红色区域，可以进行第二次移动（无论蓝方是否发动了魔法）
                        game.red_double_move_active = True
                        game.red_first_move_done = True
                        game.red_first_move_pos = move.to_pos
                        result["double_move"] = True
                        result["waiting_second_move"] = True
                        return result
                    # 移动到蓝色区域，不能进行第二次移动
                # 从蓝色区域移动，只能移动一次
            else:
                # 第二次移动完成
                game.red_double_move_active = False
                game.red_first_move_done = False
                game.red_first_move_pos = None
        
        # 切换回合
        if game.current_team == Team.RED:
            game.current_team = Team.BLUE
        else:
            game.current_team = Team.RED
            game.turn_number += 1
        
        # 重置红方双倍移动状态
        game.red_double_move_active = False
        game.red_first_move_done = False
        game.red_first_move_pos = None
        
        # 检查将死/和棋
        if game.status == GameStatus.PLAYING:
            # 获取新回合的冻结位置（针对下一位行动方）
            next_frozen_positions = self.get_frozen_positions(game)
            
            if GameLogic.is_checkmate(game.board, game.current_team,
                                      game.blue_magic_alive, game.red_magic_alive,
                                      game.turn_number, next_frozen_positions):
                if game.current_team == Team.BLUE:
                    game.status = GameStatus.RED_WIN
                else:
                    game.status = GameStatus.BLUE_WIN
                result["game_status"] = game.status.value
            elif GameLogic.is_stalemate(game.board, game.current_team,
                                        game.blue_magic_alive, game.red_magic_alive,
                                        game.turn_number, next_frozen_positions):
                game.status = GameStatus.DRAW
                result["game_status"] = game.status.value
        
        return result
    
    def get_valid_moves_for_piece(self, game_id: str, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """获取指定位置棋子的所有合法移动"""
        game = self.games.get(game_id)
        if not game:
            return []
        
        if game.status != GameStatus.PLAYING:
            return []
        
        frozen_positions = self.get_frozen_positions(game)
        is_second_move = game.red_first_move_done and game.red_double_move_active
        
        # 第二次移动只能移动第一次移动的那个棋子
        if is_second_move and game.red_first_move_pos != pos:
            return []
        
        return GameLogic.get_valid_moves(
            game.board, pos, game.current_team,
            game.blue_magic_alive, game.red_magic_alive, game.turn_number,
            is_second_move, frozen_positions
        )
    
    def skip_second_move(self, game_id: str, player_id: Optional[str] = None) -> Dict:
        """跳过第二次移动（红方第11回合）"""
        game = self.games.get(game_id)
        if not game:
            return {"success": False, "error": "游戏不存在"}
        
        if not game.red_double_move_active or not game.red_first_move_done:
            return {"success": False, "error": "当前不能跳过"}
        
        # 切换回合
        game.current_team = Team.BLUE
        game.red_double_move_active = False
        game.red_first_move_done = False
        game.red_first_move_pos = None
        
        return {"success": True}
    
    def delete_game(self, game_id: str):
        """删除游戏"""
        if game_id in self.games:
            del self.games[game_id]

