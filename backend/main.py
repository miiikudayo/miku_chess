"""
Miku Chess - FastAPI 后端入口
提供 REST API 和 WebSocket 接口
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import json
import uuid
import os

from game_state import GameManager, GameMode, GameStatus
from game_logic import Move, Team
from ai_interface import list_available_ais, get_ai_player

app = FastAPI(title="Miku Chess", version="1.0.0")

# 游戏管理器
game_manager = GameManager()

# WebSocket 连接管理
class ConnectionManager:
    def __init__(self):
        # game_id -> {player_id: websocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        self.active_connections[game_id][player_id] = websocket
    
    def disconnect(self, game_id: str, player_id: str):
        if game_id in self.active_connections:
            if player_id in self.active_connections[game_id]:
                del self.active_connections[game_id][player_id]
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
    
    async def send_to_player(self, game_id: str, player_id: str, message: dict):
        if game_id in self.active_connections:
            if player_id in self.active_connections[game_id]:
                await self.active_connections[game_id][player_id].send_json(message)
    
    async def broadcast_to_game(self, game_id: str, message: dict):
        if game_id in self.active_connections:
            for player_id, websocket in self.active_connections[game_id].items():
                await websocket.send_json(message)

connection_manager = ConnectionManager()


# Request/Response 模型
class CreateGameRequest(BaseModel):
    mode: str  # "local", "online", "ai"
    player_name: Optional[str] = None


class JoinGameRequest(BaseModel):
    player_name: Optional[str] = None


class MoveRequest(BaseModel):
    from_pos: List[int]  # [row, col]
    to_pos: List[int]    # [row, col]
    player_id: Optional[str] = None


class GetMovesRequest(BaseModel):
    pos: List[int]  # [row, col]


# REST API 端点
@app.post("/api/games")
async def create_game(request: CreateGameRequest):
    """创建新游戏"""
    try:
        mode = GameMode(request.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的游戏模式")
    
    player_id = str(uuid.uuid4())[:8] if mode == GameMode.ONLINE else None
    game = game_manager.create_game(mode, player_id)
    
    return {
        "game_id": game.game_id,
        "player_id": player_id,
        "mode": game.mode.value,
        "status": game.status.value,
        "team": "red" if player_id else None  # 创建者为红方
    }


@app.get("/api/games/{game_id}")
async def get_game(game_id: str):
    """获取游戏状态"""
    game = game_manager.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    return game.to_dict()


@app.post("/api/games/{game_id}/join")
async def join_game(game_id: str, request: JoinGameRequest):
    """加入游戏（在线模式）"""
    player_id = str(uuid.uuid4())[:8]
    game = game_manager.join_game(game_id, player_id)
    
    if not game:
        raise HTTPException(status_code=400, detail="无法加入游戏")
    
    # 通知其他玩家
    await connection_manager.broadcast_to_game(game_id, {
        "type": "player_joined",
        "player_id": player_id,
        "team": "blue",
        "game_state": game.to_dict()
    })
    
    return {
        "game_id": game.game_id,
        "player_id": player_id,
        "team": "blue",  # 加入者为蓝方
        "status": game.status.value
    }


@app.post("/api/games/{game_id}/move")
async def make_move(game_id: str, request: MoveRequest):
    """执行移动"""
    move = Move(
        from_pos=tuple(request.from_pos),
        to_pos=tuple(request.to_pos)
    )
    
    result = game_manager.make_move(game_id, move, request.player_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    game = game_manager.get_game(game_id)
    
    # 广播移动给所有连接的玩家
    await connection_manager.broadcast_to_game(game_id, {
        "type": "move_made",
        "move": move.to_dict(),
        "result": result,
        "game_state": game.to_dict()
    })
    
    return {
        **result,
        "game_state": game.to_dict()
    }


@app.post("/api/games/{game_id}/valid-moves")
async def get_valid_moves(game_id: str, request: GetMovesRequest):
    """获取指定位置棋子的所有合法移动"""
    pos = tuple(request.pos)
    moves = game_manager.get_valid_moves_for_piece(game_id, pos)
    
    return {
        "valid_moves": [list(m) for m in moves]
    }


@app.post("/api/games/{game_id}/skip-second-move")
async def skip_second_move(game_id: str):
    """跳过第二次移动（红方第11回合）"""
    result = game_manager.skip_second_move(game_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    game = game_manager.get_game(game_id)
    
    # 广播状态更新
    await connection_manager.broadcast_to_game(game_id, {
        "type": "turn_changed",
        "game_state": game.to_dict()
    })
    
    return {
        **result,
        "game_state": game.to_dict()
    }


@app.get("/api/ai/list")
async def list_ais():
    """列出所有可用的 AI"""
    return {"ais": list_available_ais()}


@app.delete("/api/games/{game_id}")
async def delete_game(game_id: str):
    """删除游戏"""
    game_manager.delete_game(game_id)
    return {"success": True}


# WebSocket 端点
@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    """WebSocket 连接处理"""
    game = game_manager.get_game(game_id)
    if not game:
        await websocket.close(code=4004, reason="游戏不存在")
        return
    
    await connection_manager.connect(websocket, game_id, player_id)
    
    try:
        # 发送当前游戏状态
        await websocket.send_json({
            "type": "connected",
            "game_state": game.to_dict()
        })
        
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "move":
                # 处理移动
                move = Move(
                    from_pos=tuple(data["from"]),
                    to_pos=tuple(data["to"])
                )
                result = game_manager.make_move(game_id, move, player_id)
                
                game = game_manager.get_game(game_id)
                
                # 广播给所有玩家
                await connection_manager.broadcast_to_game(game_id, {
                    "type": "move_made",
                    "move": move.to_dict(),
                    "result": result,
                    "game_state": game.to_dict()
                })
            
            elif message_type == "get_valid_moves":
                # 获取合法移动
                pos = tuple(data["pos"])
                moves = game_manager.get_valid_moves_for_piece(game_id, pos)
                
                await websocket.send_json({
                    "type": "valid_moves",
                    "pos": list(pos),
                    "valid_moves": [list(m) for m in moves]
                })
            
            elif message_type == "skip_second_move":
                # 跳过第二次移动
                result = game_manager.skip_second_move(game_id, player_id)
                game = game_manager.get_game(game_id)
                
                await connection_manager.broadcast_to_game(game_id, {
                    "type": "turn_changed",
                    "game_state": game.to_dict()
                })
            
            elif message_type == "chat":
                # 聊天消息
                await connection_manager.broadcast_to_game(game_id, {
                    "type": "chat",
                    "player_id": player_id,
                    "message": data.get("message", "")
                })
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        connection_manager.disconnect(game_id, player_id)
        
        # 通知其他玩家
        await connection_manager.broadcast_to_game(game_id, {
            "type": "player_disconnected",
            "player_id": player_id
        })


# 静态文件服务
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/css", StaticFiles(directory=os.path.join(frontend_path, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_path, "js")), name="js")
    
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))
    
    @app.get("/game/{game_id}")
    async def serve_game_page(game_id: str):
        return FileResponse(os.path.join(frontend_path, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

