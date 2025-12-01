"""
Miku Chess - 核心游戏逻辑
包含棋子类型、移动规则验证、吃子规则等
"""

from enum import Enum
from typing import List, Tuple, Optional
from dataclasses import dataclass


class PieceType(Enum):
    """棋子类型"""
    ATTACK = "attack"      # 进攻棋 (攻)
    DEFENSE = "defense"    # 防守棋 (守)
    SUPPORT = "support"    # 应援棋 (援)
    MAGIC = "magic"        # 魔法阵 (法)
    GENERAL = "general"    # 胜点棋 (将)


class Team(Enum):
    """阵营"""
    BLUE = "blue"   # 蓝方 (上半区, 行0-4)
    RED = "red"     # 红方 (下半区, 行5-9)


@dataclass
class Piece:
    """棋子"""
    piece_type: PieceType
    team: Team
    
    def to_dict(self) -> dict:
        return {
            "type": self.piece_type.value,
            "team": self.team.value
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Piece':
        return Piece(
            piece_type=PieceType(data["type"]),
            team=Team(data["team"])
        )


@dataclass
class Move:
    """移动"""
    from_pos: Tuple[int, int]  # (row, col)
    to_pos: Tuple[int, int]    # (row, col)
    
    def to_dict(self) -> dict:
        return {
            "from": list(self.from_pos),
            "to": list(self.to_pos)
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Move':
        return Move(
            from_pos=tuple(data["from"]),
            to_pos=tuple(data["to"])
        )


# 列名映射
COLUMNS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']


def col_to_index(col: str) -> int:
    """将列名转换为索引"""
    return COLUMNS.index(col.upper())


def index_to_col(index: int) -> str:
    """将索引转换为列名"""
    return COLUMNS[index]


def pos_to_notation(row: int, col: int) -> str:
    """将位置转换为棋谱记号 (如 0A, 2E)"""
    return f"{row}{COLUMNS[col]}"


def notation_to_pos(notation: str) -> Tuple[int, int]:
    """将棋谱记号转换为位置"""
    row = int(notation[0])
    col = col_to_index(notation[1])
    return (row, col)


def is_in_blue_zone(row: int) -> bool:
    """判断是否在蓝色区域 (行0-4)"""
    return 0 <= row <= 4


def is_in_red_zone(row: int) -> bool:
    """判断是否在红色区域 (行5-9)"""
    return 5 <= row <= 9


def get_blue_palace() -> List[Tuple[int, int]]:
    """获取蓝方九宫格位置 (胜点棋活动区域: 行0-2, 列3-5)"""
    positions = []
    for row in range(0, 3):
        for col in range(3, 6):
            positions.append((row, col))
    return positions


def get_red_palace() -> List[Tuple[int, int]]:
    """获取红方九宫格位置 (胜点棋活动区域: 行7-9, 列3-5)"""
    positions = []
    for row in range(7, 10):
        for col in range(3, 6):
            positions.append((row, col))
    return positions


def get_blue_magic_zone() -> List[Tuple[int, int]]:
    """获取蓝方魔法阵活动区域 (行2-4, 列3-5)"""
    positions = []
    for row in range(2, 5):
        for col in range(3, 6):
            positions.append((row, col))
    return positions


def get_red_magic_zone() -> List[Tuple[int, int]]:
    """获取红方魔法阵活动区域 (行5-7, 列3-5)"""
    positions = []
    for row in range(5, 8):
        for col in range(3, 6):
            positions.append((row, col))
    return positions


def is_valid_position(row: int, col: int) -> bool:
    """检查位置是否在棋盘内"""
    return 0 <= row <= 9 and 0 <= col <= 8


def get_path_positions(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    获取从起点到终点之间的所有位置（不包括起点，包括终点）
    仅支持直线移动（横、纵、斜向）
    """
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    positions = []
    
    row_diff = to_row - from_row
    col_diff = to_col - from_col
    
    # 计算方向
    row_step = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
    col_step = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)
    
    # 计算步数
    steps = max(abs(row_diff), abs(col_diff))
    
    current_row, current_col = from_row, from_col
    for _ in range(steps):
        current_row += row_step
        current_col += col_step
        positions.append((current_row, current_col))
    
    return positions


def is_straight_line(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
    """检查是否为直线移动（横或纵）"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    return from_row == to_row or from_col == to_col


def is_diagonal(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
    """检查是否为斜向移动"""
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    return abs(from_row - to_row) == abs(from_col - to_col) and from_row != to_row


def is_horizontal(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
    """检查是否为横向移动"""
    return from_pos[0] == to_pos[0] and from_pos[1] != to_pos[1]


def is_vertical(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
    """检查是否为纵向移动"""
    return from_pos[1] == to_pos[1] and from_pos[0] != to_pos[0]


def is_moving_backward(from_pos: Tuple[int, int], to_pos: Tuple[int, int], team: Team) -> bool:
    """
    检查是否为后退移动
    蓝方后退：向行数减小的方向移动 (向上)
    红方后退：向行数增大的方向移动 (向下)
    """
    from_row = from_pos[0]
    to_row = to_pos[0]
    
    if team == Team.BLUE:
        return to_row < from_row
    else:  # RED
        return to_row > from_row


def is_moving_diagonal_backward(from_pos: Tuple[int, int], to_pos: Tuple[int, int], team: Team) -> bool:
    """
    检查是否为斜后退移动
    """
    if not is_diagonal(from_pos, to_pos):
        return False
    return is_moving_backward(from_pos, to_pos, team)


class GameLogic:
    """游戏逻辑处理器"""
    
    @staticmethod
    def get_valid_moves(board: List[List[Optional[Piece]]], 
                        pos: Tuple[int, int],
                        current_team: Team,
                        blue_magic_alive: bool,
                        red_magic_alive: bool,
                        turn_number: int,
                        is_second_move: bool = False,
                        frozen_positions: List[Tuple[int, int]] = None) -> List[Tuple[int, int]]:
        """
        获取指定位置棋子的所有合法移动位置
        
        Args:
            board: 棋盘状态
            pos: 棋子位置
            current_team: 当前行动方
            blue_magic_alive: 蓝方魔法阵是否存活
            red_magic_alive: 红方魔法阵是否存活
            turn_number: 当前回合数
            is_second_move: 是否是红方第11回合的第二次移动
            frozen_positions: 被冻结的位置列表
        
        Returns:
            合法移动位置列表
        """
        if frozen_positions is None:
            frozen_positions = []
            
        row, col = pos
        piece = board[row][col]
        
        if piece is None:
            return []
        
        if piece.team != current_team:
            return []
        
        # 检查是否被冻结
        if pos in frozen_positions:
            return []
        
        valid_moves = []
        
        # 根据棋子类型获取可能的移动
        if piece.piece_type == PieceType.ATTACK:
            valid_moves = GameLogic._get_attack_moves(board, pos, piece)
        elif piece.piece_type == PieceType.DEFENSE:
            valid_moves = GameLogic._get_defense_moves(board, pos, piece)
        elif piece.piece_type == PieceType.SUPPORT:
            valid_moves = GameLogic._get_support_moves(board, pos, piece)
        elif piece.piece_type == PieceType.MAGIC:
            valid_moves = GameLogic._get_magic_moves(board, pos, piece)
        elif piece.piece_type == PieceType.GENERAL:
            valid_moves = GameLogic._get_general_moves(board, pos, piece)
        
        # 如果该方魔法阵被吃掉，不能后退
        can_retreat = True
        if piece.team == Team.BLUE and not blue_magic_alive:
            can_retreat = False
        elif piece.team == Team.RED and not red_magic_alive:
            can_retreat = False
        
        if not can_retreat:
            valid_moves = [m for m in valid_moves 
                         if not is_moving_backward(pos, m, piece.team) 
                         and not is_moving_diagonal_backward(pos, m, piece.team)]
        
        # 第11回合蓝方魔法效果：红方不能移动蓝色区域的棋子
        if turn_number == 11 and blue_magic_alive and current_team == Team.RED:
            if is_in_blue_zone(row):
                return []
        
        # 第11回合红方第二次移动时的限制
        # 只有当蓝方魔法阵存活时，在蓝色区域的棋子才不能进行第二次移动
        # 如果蓝方魔法阵已死亡，即使在蓝色区域也可以进行第二次移动
        if is_second_move and is_in_blue_zone(row) and blue_magic_alive:
            return []
        
        return valid_moves
    
    @staticmethod
    def _get_attack_moves(board: List[List[Optional[Piece]]], 
                          pos: Tuple[int, int], 
                          piece: Piece) -> List[Tuple[int, int]]:
        """
        进攻棋移动规则:
        - 沿横线或纵线任意方向走任意格数
        - 路径上若有其他棋子则无法越过
        - 纵向可以吃掉敌方棋子
        - 横向不能吃子，遇到任何棋子停止
        """
        valid_moves = []
        row, col = pos
        
        # 四个方向: 上、下、左、右
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for d_row, d_col in directions:
            is_vertical_move = (d_col == 0)
            
            current_row, current_col = row + d_row, col + d_col
            while is_valid_position(current_row, current_col):
                target = board[current_row][current_col]
                
                if target is None:
                    # 空位置，可以移动
                    valid_moves.append((current_row, current_col))
                else:
                    # 有棋子
                    if is_vertical_move:
                        # 纵向移动，可以吃敌方棋子
                        if target.team != piece.team:
                            valid_moves.append((current_row, current_col))
                    # 横向或遇到己方棋子，停止
                    break
                
                current_row += d_row
                current_col += d_col
        
        return valid_moves
    
    @staticmethod
    def _get_defense_moves(board: List[List[Optional[Piece]]], 
                           pos: Tuple[int, int], 
                           piece: Piece) -> List[Tuple[int, int]]:
        """
        防守棋移动规则:
        - 沿横线或纵线任意方向走任意格数
        - 路径上若有其他棋子则无法越过
        - 横向可以吃掉敌方棋子
        - 纵向不能吃子，遇到任何棋子停止
        """
        valid_moves = []
        row, col = pos
        
        # 四个方向: 上、下、左、右
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for d_row, d_col in directions:
            is_horizontal_move = (d_row == 0)
            
            current_row, current_col = row + d_row, col + d_col
            while is_valid_position(current_row, current_col):
                target = board[current_row][current_col]
                
                if target is None:
                    # 空位置，可以移动
                    valid_moves.append((current_row, current_col))
                else:
                    # 有棋子
                    if is_horizontal_move:
                        # 横向移动，可以吃敌方棋子
                        if target.team != piece.team:
                            valid_moves.append((current_row, current_col))
                    # 纵向或遇到己方棋子，停止
                    break
                
                current_row += d_row
                current_col += d_col
        
        return valid_moves
    
    @staticmethod
    def _get_support_moves(board: List[List[Optional[Piece]]], 
                           pos: Tuple[int, int], 
                           piece: Piece) -> List[Tuple[int, int]]:
        """
        应援棋移动规则:
        - 沿斜向任意方向走任意格数
        - 路径上若有其他棋子则无法越过
        - 可以吃掉敌方棋子
        - 遇到己方棋子停止
        """
        valid_moves = []
        row, col = pos
        
        # 四个斜向: 左上、右上、左下、右下
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for d_row, d_col in directions:
            current_row, current_col = row + d_row, col + d_col
            while is_valid_position(current_row, current_col):
                target = board[current_row][current_col]
                
                if target is None:
                    # 空位置，可以移动
                    valid_moves.append((current_row, current_col))
                elif target.team != piece.team:
                    # 敌方棋子，可以吃掉
                    valid_moves.append((current_row, current_col))
                    break
                else:
                    # 己方棋子，停止
                    break
                
                current_row += d_row
                current_col += d_col
        
        return valid_moves
    
    @staticmethod
    def _get_magic_moves(board: List[List[Optional[Piece]]], 
                         pos: Tuple[int, int], 
                         piece: Piece) -> List[Tuple[int, int]]:
        """
        魔法阵移动规则:
        - 仅限己方魔法区域内活动 (蓝方: 行2-4, 红方: 行5-7, 列3-5)
        - 每步只能沿横线或纵线走1格
        - 若被其他棋子阻挡则无法移动
        """
        valid_moves = []
        row, col = pos
        
        # 获取对应阵营的魔法区域
        if piece.team == Team.BLUE:
            magic_zone = get_blue_magic_zone()
        else:
            magic_zone = get_red_magic_zone()
        
        # 四个方向: 上、下、左、右，每次只能走1格
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for d_row, d_col in directions:
            new_row, new_col = row + d_row, col + d_col
            
            if (new_row, new_col) in magic_zone:
                target = board[new_row][new_col]
                if target is None:
                    valid_moves.append((new_row, new_col))
        
        return valid_moves
    
    @staticmethod
    def _get_general_moves(board: List[List[Optional[Piece]]], 
                           pos: Tuple[int, int], 
                           piece: Piece) -> List[Tuple[int, int]]:
        """
        胜点棋移动规则:
        - 仅限己方九宫内活动 (蓝方: 行0-2, 红方: 行7-9, 列3-5)
        - 每步只能沿横线或纵线走1格
        - 若被其他棋子阻挡则无法移动
        """
        valid_moves = []
        row, col = pos
        
        # 获取对应阵营的九宫
        if piece.team == Team.BLUE:
            palace = get_blue_palace()
        else:
            palace = get_red_palace()
        
        # 四个方向: 上、下、左、右，每次只能走1格
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for d_row, d_col in directions:
            new_row, new_col = row + d_row, col + d_col
            
            if (new_row, new_col) in palace:
                target = board[new_row][new_col]
                if target is None:
                    valid_moves.append((new_row, new_col))
        
        return valid_moves
    
    @staticmethod
    def is_general_in_check(board: List[List[Optional[Piece]]], 
                            team: Team,
                            blue_magic_alive: bool = True,
                            red_magic_alive: bool = True) -> bool:
        """
        检查指定方的胜点棋是否被将军
        
        Args:
            board: 棋盘状态
            team: 要检查的阵营
            blue_magic_alive: 蓝方魔法阵是否存活
            red_magic_alive: 红方魔法阵是否存活
        """
        # 找到胜点棋位置
        general_pos = None
        for row in range(10):
            for col in range(9):
                piece = board[row][col]
                if piece and piece.team == team and piece.piece_type == PieceType.GENERAL:
                    general_pos = (row, col)
                    break
            if general_pos:
                break
        
        if not general_pos:
            return True  # 胜点棋不存在，视为被将死
        
        # 检查对方所有棋子是否能攻击到胜点棋
        enemy_team = Team.RED if team == Team.BLUE else Team.BLUE
        
        # 判断敌方是否能后退（魔法阵死亡则不能后退）
        enemy_can_retreat = True
        if enemy_team == Team.BLUE and not blue_magic_alive:
            enemy_can_retreat = False
        elif enemy_team == Team.RED and not red_magic_alive:
            enemy_can_retreat = False
        
        for row in range(10):
            for col in range(9):
                piece = board[row][col]
                if piece and piece.team == enemy_team:
                    pos = (row, col)
                    # 获取该棋子的攻击范围
                    if piece.piece_type == PieceType.ATTACK:
                        moves = GameLogic._get_attack_moves(board, pos, piece)
                    elif piece.piece_type == PieceType.DEFENSE:
                        moves = GameLogic._get_defense_moves(board, pos, piece)
                    elif piece.piece_type == PieceType.SUPPORT:
                        moves = GameLogic._get_support_moves(board, pos, piece)
                    else:
                        continue  # 魔法阵和胜点棋不能吃子
                    
                    # 如果敌方魔法阵死亡，需要过滤掉后退移动
                    if not enemy_can_retreat:
                        moves = [m for m in moves 
                                if not is_moving_backward(pos, m, enemy_team) 
                                and not is_moving_diagonal_backward(pos, m, enemy_team)]
                    
                    if general_pos in moves:
                        return True
        
        return False
    
    @staticmethod
    def is_checkmate(board: List[List[Optional[Piece]]], 
                     team: Team,
                     blue_magic_alive: bool,
                     red_magic_alive: bool,
                     turn_number: int,
                     frozen_positions: List[Tuple[int, int]] = None) -> bool:
        """
        检查指定方是否被将死
        将死条件：胜点棋被将军且无法解除
        
        Args:
            board: 棋盘状态
            team: 要检查的阵营
            blue_magic_alive: 蓝方魔法阵是否存活
            red_magic_alive: 红方魔法阵是否存活
            turn_number: 当前回合数
            frozen_positions: 被冻结的位置列表（第11回合蓝方魔法效果）
        """
        if frozen_positions is None:
            frozen_positions = []
        
        if not GameLogic.is_general_in_check(board, team, blue_magic_alive, red_magic_alive):
            return False
        
        # 尝试所有可能的移动，看是否能解除将军
        for r in range(10):
            for c in range(9):
                piece = board[r][c]
                if piece and piece.team == team:
                    moves = GameLogic.get_valid_moves(
                        board, (r, c), team,
                        blue_magic_alive, red_magic_alive, turn_number,
                        False, frozen_positions
                    )
                    
                    for move_to in moves:
                        # 模拟移动
                        test_board = [row[:] for row in board]
                        test_board[move_to[0]][move_to[1]] = test_board[r][c]
                        test_board[r][c] = None
                        
                        # 检查移动后是否仍被将军（考虑魔法状态）
                        if not GameLogic.is_general_in_check(test_board, team, blue_magic_alive, red_magic_alive):
                            return False
        
        return True
    
    @staticmethod
    def is_stalemate(board: List[List[Optional[Piece]]], 
                     team: Team,
                     blue_magic_alive: bool,
                     red_magic_alive: bool,
                     turn_number: int,
                     frozen_positions: List[Tuple[int, int]] = None) -> bool:
        """
        检查是否为和棋（无子可动）
        
        Args:
            board: 棋盘状态
            team: 要检查的阵营
            blue_magic_alive: 蓝方魔法阵是否存活
            red_magic_alive: 红方魔法阵是否存活
            turn_number: 当前回合数
            frozen_positions: 被冻结的位置列表（第11回合蓝方魔法效果）
        """
        if frozen_positions is None:
            frozen_positions = []
        
        # 检查该方是否有任何合法移动
        for row in range(10):
            for col in range(9):
                piece = board[row][col]
                if piece and piece.team == team:
                    moves = GameLogic.get_valid_moves(
                        board, (row, col), team,
                        blue_magic_alive, red_magic_alive, turn_number,
                        False, frozen_positions
                    )
                    if moves:
                        return False
        
        return True

