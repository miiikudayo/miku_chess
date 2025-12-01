/**
 * Miku Chess - 网络通信模块
 * 负责 WebSocket 连接和 REST API 调用
 */

class NetworkManager {
    constructor() {
        this.ws = null;
        this.gameId = null;
        this.playerId = null;
        this.onMessage = null;
        this.onConnect = null;
        this.onDisconnect = null;
        this.onError = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    /**
     * 获取 API 基础 URL
     */
    getBaseUrl() {
        return window.location.origin;
    }
    
    /**
     * 获取 WebSocket URL
     */
    getWsUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}`;
    }
    
    /**
     * 创建游戏
     */
    async createGame(mode) {
        try {
            const response = await fetch(`${this.getBaseUrl()}/api/games`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '创建游戏失败');
            }
            
            const data = await response.json();
            this.gameId = data.game_id;
            this.playerId = data.player_id;
            
            return data;
        } catch (error) {
            console.error('创建游戏失败:', error);
            throw error;
        }
    }
    
    /**
     * 获取游戏状态
     */
    async getGame(gameId) {
        try {
            const response = await fetch(`${this.getBaseUrl()}/api/games/${gameId}`);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '获取游戏失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('获取游戏失败:', error);
            throw error;
        }
    }
    
    /**
     * 加入游戏
     */
    async joinGame(gameId) {
        try {
            const response = await fetch(`${this.getBaseUrl()}/api/games/${gameId}/join`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '加入游戏失败');
            }
            
            const data = await response.json();
            this.gameId = data.game_id;
            this.playerId = data.player_id;
            
            return data;
        } catch (error) {
            console.error('加入游戏失败:', error);
            throw error;
        }
    }
    
    /**
     * 执行移动 (REST API)
     */
    async makeMove(fromPos, toPos) {
        try {
            const response = await fetch(`${this.getBaseUrl()}/api/games/${this.gameId}/move`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    from_pos: fromPos,
                    to_pos: toPos,
                    player_id: this.playerId
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '移动失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('移动失败:', error);
            throw error;
        }
    }
    
    /**
     * 获取合法移动
     */
    async getValidMoves(pos) {
        try {
            const response = await fetch(`${this.getBaseUrl()}/api/games/${this.gameId}/valid-moves`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pos })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '获取合法移动失败');
            }
            
            const data = await response.json();
            return data.valid_moves;
        } catch (error) {
            console.error('获取合法移动失败:', error);
            throw error;
        }
    }
    
    /**
     * 跳过第二次移动
     */
    async skipSecondMove() {
        try {
            const response = await fetch(`${this.getBaseUrl()}/api/games/${this.gameId}/skip-second-move`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '跳过失败');
            }
            
            return await response.json();
        } catch (error) {
            console.error('跳过第二次移动失败:', error);
            throw error;
        }
    }
    
    /**
     * 连接 WebSocket
     */
    connectWebSocket(gameId, playerId) {
        this.gameId = gameId || this.gameId;
        this.playerId = playerId || this.playerId;
        
        if (!this.gameId || !this.playerId) {
            console.error('缺少游戏ID或玩家ID');
            return;
        }
        
        const wsUrl = `${this.getWsUrl()}/ws/${this.gameId}/${this.playerId}`;
        console.log('连接 WebSocket:', wsUrl);
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket 已连接');
            this.reconnectAttempts = 0;
            if (this.onConnect) {
                this.onConnect();
            }
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('收到消息:', data);
                if (this.onMessage) {
                    this.onMessage(data);
                }
            } catch (error) {
                console.error('解析消息失败:', error);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket 已断开:', event.code, event.reason);
            if (this.onDisconnect) {
                this.onDisconnect(event);
            }
            
            // 尝试重连
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                setTimeout(() => this.connectWebSocket(), 2000);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket 错误:', error);
            if (this.onError) {
                this.onError(error);
            }
        };
    }
    
    /**
     * 发送 WebSocket 消息
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket 未连接');
        }
    }
    
    /**
     * 通过 WebSocket 发送移动
     */
    sendMove(fromPos, toPos) {
        this.send({
            type: 'move',
            from: fromPos,
            to: toPos
        });
    }
    
    /**
     * 通过 WebSocket 请求合法移动
     */
    sendGetValidMoves(pos) {
        this.send({
            type: 'get_valid_moves',
            pos: pos
        });
    }
    
    /**
     * 通过 WebSocket 跳过第二次移动
     */
    sendSkipSecondMove() {
        this.send({
            type: 'skip_second_move'
        });
    }
    
    /**
     * 发送聊天消息
     */
    sendChat(message) {
        this.send({
            type: 'chat',
            message: message
        });
    }
    
    /**
     * 发送心跳
     */
    sendPing() {
        this.send({ type: 'ping' });
    }
    
    /**
     * 断开连接
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.gameId = null;
        this.playerId = null;
    }
    
    /**
     * 检查是否已连接
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// 导出
window.NetworkManager = NetworkManager;

