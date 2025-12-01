"""
Miku Chess - AI 接口模块
预留的 AI 对战接口，供后续实现智能对手
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from dataclasses import dataclass

from game_logic import Move, Team, Piece
from game_state import GameState


@dataclass
class AIMove:
    """AI 移动结果"""
    move: Move
    confidence: float  # 置信度 0-1
    evaluation: float  # 局面评估分数
    thinking_time: float  # 思考时间（秒）


class AIPlayer(ABC):
    """
    AI 玩家抽象基类
    实现此接口以创建不同难度/策略的 AI
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """AI 名称"""
        pass
    
    @property
    @abstractmethod
    def difficulty(self) -> str:
        """难度等级: easy, medium, hard, expert"""
        pass
    
    @abstractmethod
    def get_move(self, game_state: GameState) -> AIMove:
        """
        根据当前游戏状态计算最佳移动
        
        Args:
            game_state: 当前游戏状态
            
        Returns:
            AIMove: 包含移动信息和评估结果
        """
        pass
    
    @abstractmethod
    def evaluate_position(self, game_state: GameState) -> float:
        """
        评估当前局面
        
        Args:
            game_state: 当前游戏状态
            
        Returns:
            float: 评估分数，正数有利于红方，负数有利于蓝方
        """
        pass
    
    def on_game_start(self, game_state: GameState, team: Team):
        """
        游戏开始时的回调
        可用于初始化 AI 状态
        """
        pass
    
    def on_opponent_move(self, game_state: GameState, move: Move):
        """
        对手移动后的回调
        可用于更新内部状态
        """
        pass
    
    def on_game_end(self, game_state: GameState, winner: Optional[Team]):
        """
        游戏结束时的回调
        可用于学习和统计
        """
        pass


class RandomAI(AIPlayer):
    """
    随机 AI - 最简单的实现，随机选择合法移动
    可作为基准测试和示例
    """
    
    import random
    
    @property
    def name(self) -> str:
        return "Random Miku"
    
    @property
    def difficulty(self) -> str:
        return "easy"
    
    def get_move(self, game_state: GameState) -> AIMove:
        import random
        import time
        from game_logic import GameLogic
        
        start_time = time.time()
        
        # 收集所有合法移动
        all_moves = []
        current_team = game_state.current_team
        
        for row in range(10):
            for col in range(9):
                piece = game_state.board[row][col]
                if piece and piece.team == current_team:
                    valid_moves = GameLogic.get_valid_moves(
                        game_state.board, (row, col), current_team,
                        game_state.blue_magic_alive, game_state.red_magic_alive,
                        game_state.turn_number
                    )
                    for to_pos in valid_moves:
                        all_moves.append(Move((row, col), to_pos))
        
        if not all_moves:
            # 无合法移动（理论上不应该发生）
            return None
        
        # 随机选择一个移动
        selected_move = random.choice(all_moves)
        
        thinking_time = time.time() - start_time
        
        return AIMove(
            move=selected_move,
            confidence=1.0 / len(all_moves),  # 置信度基于可选数量
            evaluation=0.0,  # 随机AI不评估局面
            thinking_time=thinking_time
        )
    
    def evaluate_position(self, game_state: GameState) -> float:
        """简单的材料评估"""
        from game_logic import PieceType
        
        piece_values = {
            PieceType.ATTACK: 5,
            PieceType.DEFENSE: 5,
            PieceType.SUPPORT: 4,
            PieceType.MAGIC: 3,
            PieceType.GENERAL: 100  # 胜点棋价值极高
        }
        
        score = 0
        for row in range(10):
            for col in range(9):
                piece = game_state.board[row][col]
                if piece:
                    value = piece_values.get(piece.piece_type, 0)
                    if piece.team == Team.RED:
                        score += value
                    else:
                        score -= value
        
        return score


# AI 注册表
AI_REGISTRY = {
    "random": RandomAI
}


def get_ai_player(ai_type: str) -> Optional[AIPlayer]:
    """
    获取 AI 玩家实例
    
    Args:
        ai_type: AI 类型名称
        
    Returns:
        AIPlayer 实例，如果类型不存在则返回 None
    """
    ai_class = AI_REGISTRY.get(ai_type)
    if ai_class:
        return ai_class()
    return None


def list_available_ais() -> List[dict]:
    """
    列出所有可用的 AI
    
    Returns:
        AI 信息列表
    """
    ais = []
    for ai_type, ai_class in AI_REGISTRY.items():
        ai_instance = ai_class()
        ais.append({
            "type": ai_type,
            "name": ai_instance.name,
            "difficulty": ai_instance.difficulty
        })
    return ais


# 占位：未来可以实现更高级的 AI
# class MinimaxAI(AIPlayer):
#     """使用 Minimax 算法的 AI"""
#     pass

# class MCTSAI(AIPlayer):
#     """使用蒙特卡洛树搜索的 AI"""
#     pass

# class NeuralNetworkAI(AIPlayer):
#     """使用神经网络的 AI"""
#     pass

