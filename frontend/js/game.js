/**
 * Miku Chess - 游戏主模块
 * 负责游戏流程控制和界面交互
 */

// 游戏状态
let gameState = null;
let gameMode = null;  // 'local', 'online'
let myTeam = null;    // 'red', 'blue' (仅在线模式)
let boardRenderer = null;
let networkManager = null;

// 选中状态
let selectedPos = null;
let validMoves = [];

// 移动标志，用于防止动画重复播放
let pendingMove = null;  // 正在等待服务器响应的移动

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    boardRenderer = new BoardRenderer('chess-board');
    networkManager = new NetworkManager();
    
    // 设置网络事件处理
    networkManager.onMessage = handleNetworkMessage;
    networkManager.onConnect = handleConnect;
    networkManager.onDisconnect = handleDisconnect;
    
    // 检查 URL 是否包含游戏 ID
    checkUrlForGame();
});

/**
 * 检查 URL 中是否有游戏 ID
 */
function checkUrlForGame() {
    const path = window.location.pathname;
    const match = path.match(/\/game\/([a-zA-Z0-9]+)/);
    
    if (match) {
        const gameId = match[1];
        joinOnlineGameById(gameId);
    }
}

/**
 * 显示指定屏幕
 */
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
}

/**
 * 返回主菜单
 */
function showMenu() {
    showScreen('menu-screen');
}

/**
 * 显示在线选项
 */
function showOnlineOptions() {
    showScreen('online-screen');
}

/**
 * 显示规则
 */
function showRules() {
    document.getElementById('rules-modal').classList.add('active');
}

/**
 * 隐藏规则
 */
function hideRules() {
    document.getElementById('rules-modal').classList.remove('active');
}

/**
 * 开始本地游戏
 */
async function startLocalGame() {
    try {
        const data = await networkManager.createGame('local');
        gameMode = 'local';
        myTeam = null;  // 本地模式双方都可操作
        
        // 获取游戏状态
        gameState = await networkManager.getGame(data.game_id);
        
        initGame();
    } catch (error) {
        alert('创建游戏失败: ' + error.message);
    }
}

/**
 * 创建在线游戏
 */
async function createOnlineGame() {
    try {
        const data = await networkManager.createGame('online');
        gameMode = 'online';
        myTeam = data.team;  // 创建者为红方
        
        // 显示等待界面
        document.getElementById('room-id-display').textContent = data.game_id;
        showScreen('waiting-screen');
        
        // 连接 WebSocket
        networkManager.connectWebSocket(data.game_id, data.player_id);
    } catch (error) {
        alert('创建房间失败: ' + error.message);
    }
}

/**
 * 加入在线游戏
 */
async function joinOnlineGame() {
    const gameId = document.getElementById('game-id-input').value.trim();
    if (!gameId) {
        alert('请输入房间ID');
        return;
    }
    
    await joinOnlineGameById(gameId);
}

/**
 * 通过 ID 加入游戏
 */
async function joinOnlineGameById(gameId) {
    try {
        // 先检查游戏状态
        const game = await networkManager.getGame(gameId);
        
        if (game.status === 'waiting') {
            // 游戏等待中，加入游戏
            const data = await networkManager.joinGame(gameId);
            gameMode = 'online';
            myTeam = data.team;  // 加入者为蓝方
            
            // 获取完整游戏状态
            gameState = await networkManager.getGame(gameId);
            
            // 连接 WebSocket
            networkManager.connectWebSocket(data.game_id, data.player_id);
            
            // 显示加入提示
            showJoinNotification(myTeam);
            
            initGame();
        } else if (game.status === 'playing') {
            alert('游戏已开始，无法加入');
        } else {
            alert('游戏已结束');
        }
    } catch (error) {
        alert('加入游戏失败: ' + error.message);
    }
}

/**
 * 显示加入游戏的通知
 */
function showJoinNotification(team) {
    const notification = document.createElement('div');
    notification.className = `join-notification ${team === 'blue' ? 'team-blue' : 'team-red'}`;
    notification.innerHTML = team === 'blue' ? 
        '<span>💙 你已加入游戏，执蓝方棋子</span>' : 
        '<span>❤️ 你已加入游戏，执红方棋子</span>';
    document.body.appendChild(notification);
    
    // 3秒后移除
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

/**
 * 复制房间链接
 */
function copyRoomLink() {
    const gameId = document.getElementById('room-id-display').textContent;
    const link = `${window.location.origin}/game/${gameId}`;
    
    // 检查 Clipboard API 是否可用（需要 HTTPS 或 localhost）
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(link).then(() => {
            showCopySuccess();
        }).catch(() => {
            fallbackCopy(link);
        });
    } else {
        fallbackCopy(link);
    }
}

/**
 * 显示复制成功提示
 */
function showCopySuccess() {
    const btn = document.querySelector('.copy-btn');
    btn.textContent = '已复制!';
    setTimeout(() => {
        btn.textContent = '复制邀请链接';
    }, 2000);
}

/**
 * 备用复制方法（兼容非 HTTPS 环境）
 */
function fallbackCopy(text) {
    // 创建临时输入框
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    textArea.style.top = '0';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopySuccess();
        } else {
            prompt('复制此链接发送给好友:', text);
        }
    } catch (err) {
        prompt('复制此链接发送给好友:', text);
    }
    
    document.body.removeChild(textArea);
}

/**
 * 取消等待
 */
function cancelWaiting() {
    networkManager.disconnect();
    showScreen('online-screen');
}

/**
 * 初始化游戏
 */
function initGame() {
    showScreen('game-screen');
    
    // 设置棋盘翻转（蓝方视角时翻转）
    const shouldFlip = gameMode === 'online' && myTeam === 'blue';
    boardRenderer.setFlipped(shouldFlip);
    
    // 初始化棋盘
    boardRenderer.init();
    boardRenderer.onCellClick = handleCellClick;
    
    // 更新行标签（翻转时需要反转）
    updateRowLabels(shouldFlip);
    
    // 更新列标签（翻转时需要反转）
    updateColLabels(shouldFlip);
    
    // 更新队伍指示器
    updateTeamIndicator();
    
    // 渲染棋盘
    updateBoard();
    updateUI();
}

/**
 * 更新行标签
 */
function updateRowLabels(flipped) {
    const rowLabels = document.querySelector('.row-labels');
    if (rowLabels) {
        const labels = flipped ? 
            ['9', '8', '7', '6', '5', '4', '3', '2', '1', '0'] : 
            ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
        rowLabels.innerHTML = labels.map(l => `<span>${l}</span>`).join('');
    }
}

/**
 * 更新列标签
 */
function updateColLabels(flipped) {
    const colLabels = document.querySelector('.col-labels');
    if (colLabels) {
        const labels = flipped ?
            ['I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A'] :
            ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'];
        colLabels.innerHTML = labels.map(l => `<span>${l}</span>`).join('');
    }
}

/**
 * 更新队伍指示器
 */
function updateTeamIndicator() {
    const indicator = document.getElementById('my-team-indicator');
    if (indicator) {
        if (gameMode === 'online' && myTeam) {
            indicator.style.display = 'block';
            if (myTeam === 'red') {
                indicator.className = 'my-team-indicator team-red';
                indicator.innerHTML = '<span class="team-icon">❤️</span><span>你是红方</span>';
            } else {
                indicator.className = 'my-team-indicator team-blue';
                indicator.innerHTML = '<span class="team-icon">💙</span><span>你是蓝方</span>';
            }
        } else {
            indicator.style.display = 'none';
        }
    }
}

/**
 * 更新棋盘显示
 */
function updateBoard() {
    if (!gameState) return;
    
    // 计算冻结位置
    const frozenPositions = getFrozenPositions();
    
    // 获取必须移动的棋子位置（第二次移动时）
    const mustMovePos = getMustMovePosition();
    
    boardRenderer.render(gameState.board, frozenPositions, mustMovePos);
}

/**
 * 获取必须移动的棋子位置（红方第11回合第二次移动）
 */
function getMustMovePosition() {
    if (gameState.red_first_move_done && gameState.red_first_move_pos) {
        return gameState.red_first_move_pos;
    }
    return null;
}

/**
 * 获取被冻结的位置
 */
function getFrozenPositions() {
    if (gameState.turn_number === 11 && 
        gameState.blue_magic_alive && 
        gameState.current_team === 'red') {
        // 蓝色区域的红方棋子被冻结
        const frozen = [];
        for (let row = 0; row < 5; row++) {
            for (let col = 0; col < 9; col++) {
                const piece = gameState.board[row][col];
                if (piece && piece.team === 'red') {
                    frozen.push([row, col]);
                }
            }
        }
        return frozen;
    }
    return [];
}

/**
 * 更新界面
 */
function updateUI() {
    if (!gameState) return;
    
    // 更新回合数
    document.getElementById('turn-number').textContent = gameState.turn_number;
    
    // 更新当前玩家显示
    const currentTeamText = gameState.current_team === 'red' ? '红方行动' : '蓝方行动';
    const currentPlayerDisplay = document.getElementById('current-player-display');
    currentPlayerDisplay.textContent = currentTeamText;
    
    // 在线模式下，显示是否是自己的回合
    if (gameMode === 'online' && myTeam) {
        const isMyTurn = myTeam === gameState.current_team;
        currentPlayerDisplay.textContent = isMyTurn ? 
            `${currentTeamText} - 你的回合` : 
            `${currentTeamText} - 等待对方`;
        currentPlayerDisplay.classList.toggle('my-turn', isMyTurn);
        currentPlayerDisplay.classList.toggle('opponent-turn', !isMyTurn);
    } else {
        currentPlayerDisplay.classList.remove('my-turn', 'opponent-turn');
    }
    
    // 更新回合指示器
    const blueTurn = document.getElementById('blue-turn');
    const redTurn = document.getElementById('red-turn');
    
    blueTurn.classList.toggle('active', gameState.current_team === 'blue');
    redTurn.classList.toggle('active', gameState.current_team === 'red');
    
    // 更新魔法阵状态
    const blueMagicEl = document.getElementById('blue-magic-status');
    const redMagicEl = document.getElementById('red-magic-status');
    
    blueMagicEl.textContent = `蓝方魔法阵: ${gameState.blue_magic_alive ? '存活' : '已消亡'}`;
    redMagicEl.textContent = `红方魔法阵: ${gameState.red_magic_alive ? '存活' : '已消亡'}`;
    
    blueMagicEl.parentElement.classList.toggle('dead', !gameState.blue_magic_alive);
    redMagicEl.parentElement.classList.toggle('dead', !gameState.red_magic_alive);
    
    // 更新特殊状态
    const specialStatus = document.getElementById('special-status');
    if (gameState.turn_number === 11) {
        let statusText = '';
        if (gameState.blue_magic_alive) {
            statusText += '❄️ 蓝方魔法生效: 蓝区红子被冻结 ';
        }
        if (gameState.red_magic_alive && gameState.current_team === 'red') {
            statusText += '⚡ 红方魔法生效: 红区红子可移动两次';
        }
        specialStatus.textContent = statusText;
    } else {
        specialStatus.textContent = '';
    }
    
    // 显示/隐藏跳过按钮
    const skipBtn = document.getElementById('skip-btn');
    skipBtn.style.display = gameState.red_first_move_done ? 'block' : 'none';
    
    // 检查游戏结束
    if (gameState.status !== 'playing') {
        showGameOver();
    }
}

/**
 * 处理格子点击
 */
async function handleCellClick(row, col) {
    if (!gameState || gameState.status !== 'playing') return;
    
    // 在线模式下检查是否是自己的回合
    if (gameMode === 'online' && myTeam !== gameState.current_team) {
        return;
    }
    
    const piece = gameState.board[row][col];
    
    // 如果已选中棋子
    if (selectedPos) {
        const [selRow, selCol] = selectedPos;
        
        // 点击的是合法移动位置
        if (isValidMove(row, col)) {
            await makeMove(selRow, selCol, row, col);
            clearSelection();
            return;
        }
        
        // 点击的是己方其他棋子
        if (piece && piece.team === gameState.current_team) {
            selectPiece(row, col);
            return;
        }
        
        // 点击其他位置，取消选中
        clearSelection();
        return;
    }
    
    // 选中己方棋子
    if (piece && piece.team === gameState.current_team) {
        // 检查是否被冻结
        const frozen = getFrozenPositions();
        if (frozen.some(pos => pos[0] === row && pos[1] === col)) {
            return;  // 被冻结的棋子不能选中
        }
        
        selectPiece(row, col);
    }
}

/**
 * 选中棋子
 */
async function selectPiece(row, col) {
    selectedPos = [row, col];
    boardRenderer.setSelected(row, col);
    
    try {
        // 获取合法移动
        validMoves = await networkManager.getValidMoves([row, col]);
        boardRenderer.showValidMoves(validMoves, gameState.board);
    } catch (error) {
        console.error('获取合法移动失败:', error);
    }
}

/**
 * 清除选中状态
 */
function clearSelection() {
    selectedPos = null;
    validMoves = [];
    boardRenderer.clearSelection();
}

/**
 * 检查是否是合法移动
 */
function isValidMove(row, col) {
    return validMoves.some(move => move[0] === row && move[1] === col);
}

/**
 * 执行移动
 */
async function makeMove(fromRow, fromCol, toRow, toCol) {
    try {
        // 记录这是自己发起的移动，防止收到广播时重复播放动画
        pendingMove = { from: [fromRow, fromCol], to: [toRow, toCol] };
        
        // 动画移动
        boardRenderer.animateMove(fromRow, fromCol, toRow, toCol, async () => {
            // 发送移动请求
            const result = await networkManager.makeMove([fromRow, fromCol], [toRow, toCol]);
            
            // 更新游戏状态
            gameState = result.game_state;
            
            // 更新界面
            updateBoard();
            updateUI();
            
            // 如果是双倍移动，提示
            if (result.waiting_second_move) {
                document.getElementById('special-status').textContent = 
                    '⚡ 请再次移动高亮的棋子，或点击"跳过"';
            }
        });
    } catch (error) {
        pendingMove = null;  // 移动失败，清除标志
        alert('移动失败: ' + error.message);
        updateBoard();
    }
}

/**
 * 跳过第二次移动
 */
async function skipSecondMove() {
    try {
        const result = await networkManager.skipSecondMove();
        gameState = result.game_state;
        updateBoard();
        updateUI();
    } catch (error) {
        alert('跳过失败: ' + error.message);
    }
}

/**
 * 处理网络消息
 */
function handleNetworkMessage(data) {
    switch (data.type) {
        case 'connected':
            console.log('WebSocket 已连接');
            break;
            
        case 'player_joined':
            // 对手加入
            if (gameMode === 'online' && !gameState) {
                gameState = data.game_state;
                initGame();
            }
            break;
            
        case 'move_made':
            // 对手移动
            gameState = data.game_state;
            
            // 如果是在线模式
            if (gameMode === 'online') {
                const move = data.move;
                
                // 检查是否是自己发起的移动（已经播放过动画了）
                const isMyMove = pendingMove && 
                    pendingMove.from[0] === move.from[0] && 
                    pendingMove.from[1] === move.from[1] &&
                    pendingMove.to[0] === move.to[0] && 
                    pendingMove.to[1] === move.to[1];
                
                if (isMyMove) {
                    // 清除标志，不播放动画（已经在 makeMove 中播放过了）
                    pendingMove = null;
                } else {
                    // 对手的移动，播放动画
                    boardRenderer.animateMove(
                        move.from[0], move.from[1],
                        move.to[0], move.to[1],
                        () => {
                            updateBoard();
                            updateUI();
                        }
                    );
                }
            } else {
                updateBoard();
                updateUI();
            }
            break;
            
        case 'turn_changed':
            gameState = data.game_state;
            updateBoard();
            updateUI();
            break;
            
        case 'player_disconnected':
            alert('对手已断开连接');
            break;
            
        case 'chat':
            console.log('聊天:', data.message);
            break;
    }
}

/**
 * 处理连接成功
 */
function handleConnect() {
    console.log('已连接到服务器');
}

/**
 * 处理断开连接
 */
function handleDisconnect(event) {
    console.log('与服务器断开连接');
}

/**
 * 显示游戏菜单
 */
function showGameMenu() {
    document.getElementById('game-menu-modal').classList.add('active');
}

/**
 * 隐藏游戏菜单
 */
function hideGameMenu() {
    document.getElementById('game-menu-modal').classList.remove('active');
}

/**
 * 显示游戏结束
 */
function showGameOver() {
    const modal = document.getElementById('game-over-modal');
    const title = document.getElementById('game-over-title');
    const message = document.getElementById('game-over-message');
    
    if (gameState.status === 'red_win') {
        title.textContent = '🎉 红方胜利!';
        message.textContent = '红方成功将死蓝方胜点棋';
    } else if (gameState.status === 'blue_win') {
        title.textContent = '🎉 蓝方胜利!';
        message.textContent = '蓝方成功将死红方胜点棋';
    } else if (gameState.status === 'draw') {
        title.textContent = '🤝 和棋';
        message.textContent = '双方无子可动，握手言和';
    }
    
    modal.classList.add('active');
}

/**
 * 重新开始游戏
 */
async function restartGame() {
    hideGameMenu();
    document.getElementById('game-over-modal').classList.remove('active');
    
    // 断开当前连接
    networkManager.disconnect();
    
    // 根据模式重新开始
    if (gameMode === 'local') {
        await startLocalGame();
    } else {
        // 在线模式返回选择界面
        showScreen('online-screen');
    }
}

/**
 * 退出游戏
 */
function exitGame() {
    hideGameMenu();
    document.getElementById('game-over-modal').classList.remove('active');
    
    // 断开连接
    networkManager.disconnect();
    
    // 清理状态
    gameState = null;
    gameMode = null;
    myTeam = null;
    selectedPos = null;
    validMoves = [];
    pendingMove = null;
    
    // 返回主菜单
    showMenu();
    
    // 清理 URL
    window.history.pushState({}, '', '/');
}

