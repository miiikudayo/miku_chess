/**
 * Miku Chess - 棋盘渲染模块
 * 负责棋盘的绘制和更新
 */

const PIECE_NAMES = {
    'attack': '攻',
    'defense': '守',
    'support': '援',
    'magic': '法',
    'general': '将'
};

const COLUMNS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'];

/**
 * 棋盘渲染器
 */
class BoardRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.cells = [];
        this.selectedCell = null;
        this.validMoves = [];
        this.frozenPositions = [];
        this.onCellClick = null;
        this.flipped = false;  // 是否翻转棋盘（蓝方视角）
    }
    
    /**
     * 设置棋盘翻转状态
     */
    setFlipped(flipped) {
        this.flipped = flipped;
    }
    
    /**
     * 将逻辑坐标转换为显示坐标
     */
    toDisplayCoord(row, col) {
        if (this.flipped) {
            return [9 - row, 8 - col];
        }
        return [row, col];
    }
    
    /**
     * 将显示坐标转换为逻辑坐标
     */
    toLogicCoord(displayRow, displayCol) {
        if (this.flipped) {
            return [9 - displayRow, 8 - displayCol];
        }
        return [displayRow, displayCol];
    }
    
    /**
     * 初始化棋盘
     */
    init() {
        this.container.innerHTML = '';
        this.cells = [];
        
        // 初始化10行的空数组
        for (let i = 0; i < 10; i++) {
            this.cells.push([]);
        }
        
        for (let displayRow = 0; displayRow < 10; displayRow++) {
            for (let displayCol = 0; displayCol < 9; displayCol++) {
                // 计算逻辑坐标（用于确定区域颜色等）
                const [logicRow, logicCol] = this.toLogicCoord(displayRow, displayCol);
                
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.displayRow = displayRow;
                cell.dataset.displayCol = displayCol;
                cell.dataset.row = logicRow;
                cell.dataset.col = logicCol;
                
                // 设置区域颜色（基于逻辑坐标）
                const isBlueZone = logicRow <= 4;
                const isDark = (logicRow + logicCol) % 2 === 1;
                
                cell.classList.add(isBlueZone ? 'blue-zone' : 'red-zone');
                cell.classList.add(isDark ? 'dark' : 'light');
                
                // 标记九宫格和魔法区（基于逻辑坐标）
                const palaceClasses = this.getPalaceBorderClass(logicRow, logicCol);
                palaceClasses.forEach(cls => cell.classList.add(cls));
                
                // 点击事件（返回逻辑坐标）
                cell.addEventListener('click', () => this.handleCellClick(logicRow, logicCol));
                
                this.container.appendChild(cell);
                // 存储到逻辑坐标对应的位置
                this.cells[logicRow][logicCol] = cell;
            }
        }
    }
    
    /**
     * 判断是否在将的九宫格内
     */
    isInGeneralPalace(row, col) {
        // 蓝方九宫格 (胜点棋): 行0-2, 列3-5
        // 红方九宫格 (胜点棋): 行7-9, 列3-5
        if (col >= 3 && col <= 5) {
            if ((row >= 0 && row <= 2) || (row >= 7 && row <= 9)) {
                return true;
            }
        }
        return false;
    }
    
    /**
     * 判断是否在魔法阵九宫格内
     */
    isInMagicZone(row, col) {
        // 蓝方魔法区: 行2-4, 列3-5
        // 红方魔法区: 行5-7, 列3-5
        if (col >= 3 && col <= 5) {
            if ((row >= 2 && row <= 4) || (row >= 5 && row <= 7)) {
                return true;
            }
        }
        return false;
    }
    
    /**
     * 获取九宫格边框类型（考虑翻转）
     */
    getPalaceBorderClass(row, col) {
        const classes = [];
        const [displayRow] = this.toDisplayCoord(row, col);
        
        // 蓝方将九宫格 (行0-2, 列3-5)
        if (row >= 0 && row <= 2 && col >= 3 && col <= 5) {
            // 翻转时边框方向也要翻转
            if (this.flipped) {
                if (row === 0) classes.push('palace-bottom');
                if (row === 2) classes.push('palace-top');
                if (col === 3) classes.push('palace-right');
                if (col === 5) classes.push('palace-left');
            } else {
                if (row === 0) classes.push('palace-top');
                if (row === 2) classes.push('palace-bottom');
                if (col === 3) classes.push('palace-left');
                if (col === 5) classes.push('palace-right');
            }
            classes.push('general-palace', 'blue-general-palace');
        }
        
        // 红方将九宫格 (行7-9, 列3-5)
        if (row >= 7 && row <= 9 && col >= 3 && col <= 5) {
            if (this.flipped) {
                if (row === 7) classes.push('palace-bottom');
                if (row === 9) classes.push('palace-top');
                if (col === 3) classes.push('palace-right');
                if (col === 5) classes.push('palace-left');
            } else {
                if (row === 7) classes.push('palace-top');
                if (row === 9) classes.push('palace-bottom');
                if (col === 3) classes.push('palace-left');
                if (col === 5) classes.push('palace-right');
            }
            classes.push('general-palace', 'red-general-palace');
        }
        
        // 蓝方魔法九宫格 (行2-4, 列3-5)
        if (row >= 2 && row <= 4 && col >= 3 && col <= 5) {
            if (this.flipped) {
                if (row === 2) classes.push('magic-zone-bottom');
                if (row === 4) classes.push('magic-zone-top');
                if (col === 3) classes.push('magic-zone-right');
                if (col === 5) classes.push('magic-zone-left');
            } else {
                if (row === 2) classes.push('magic-zone-top');
                if (row === 4) classes.push('magic-zone-bottom');
                if (col === 3) classes.push('magic-zone-left');
                if (col === 5) classes.push('magic-zone-right');
            }
            classes.push('magic-zone', 'blue-magic-zone');
        }
        
        // 红方魔法九宫格 (行5-7, 列3-5)
        if (row >= 5 && row <= 7 && col >= 3 && col <= 5) {
            if (this.flipped) {
                if (row === 5) classes.push('magic-zone-bottom');
                if (row === 7) classes.push('magic-zone-top');
                if (col === 3) classes.push('magic-zone-right');
                if (col === 5) classes.push('magic-zone-left');
            } else {
                if (row === 5) classes.push('magic-zone-top');
                if (row === 7) classes.push('magic-zone-bottom');
                if (col === 3) classes.push('magic-zone-left');
                if (col === 5) classes.push('magic-zone-right');
            }
            classes.push('magic-zone', 'red-magic-zone');
        }
        
        return classes;
    }
    
    /**
     * 处理格子点击
     */
    handleCellClick(row, col) {
        if (this.onCellClick) {
            this.onCellClick(row, col);
        }
    }
    
    /**
     * 渲染棋盘状态
     */
    render(board, frozenPositions = [], mustMovePos = null) {
        this.frozenPositions = frozenPositions;
        this.mustMovePos = mustMovePos;
        
        for (let row = 0; row < 10; row++) {
            for (let col = 0; col < 9; col++) {
                const cell = this.cells[row][col];
                const piece = board[row][col];
                
                // 清除之前的棋子
                const existingPiece = cell.querySelector('.piece');
                if (existingPiece) {
                    existingPiece.remove();
                }
                
                // 清除冻结状态和必须移动状态
                cell.classList.remove('frozen', 'must-move');
                
                // 检查是否被冻结
                if (this.isPositionFrozen(row, col)) {
                    cell.classList.add('frozen');
                }
                
                // 检查是否是必须移动的棋子（第二次移动）
                if (mustMovePos && mustMovePos[0] === row && mustMovePos[1] === col) {
                    cell.classList.add('must-move');
                }
                
                // 添加棋子
                if (piece) {
                    const pieceEl = this.createPieceElement(piece);
                    cell.appendChild(pieceEl);
                }
            }
        }
    }
    
    /**
     * 检查位置是否被冻结
     */
    isPositionFrozen(row, col) {
        return this.frozenPositions.some(pos => pos[0] === row && pos[1] === col);
    }
    
    /**
     * 创建棋子元素
     */
    createPieceElement(piece) {
        const pieceEl = document.createElement('div');
        pieceEl.className = `piece ${piece.team}`;
        
        const typeEl = document.createElement('span');
        typeEl.className = 'piece-type';
        typeEl.textContent = PIECE_NAMES[piece.type] || '?';
        
        pieceEl.appendChild(typeEl);
        return pieceEl;
    }
    
    /**
     * 设置选中的格子
     */
    setSelected(row, col) {
        // 清除之前的选中
        this.clearSelection();
        
        if (row !== null && col !== null) {
            this.selectedCell = [row, col];
            this.cells[row][col].classList.add('selected');
            
            const piece = this.cells[row][col].querySelector('.piece');
            if (piece) {
                piece.classList.add('selected');
            }
        }
    }
    
    /**
     * 清除选中状态
     */
    clearSelection() {
        if (this.selectedCell) {
            const [row, col] = this.selectedCell;
            this.cells[row][col].classList.remove('selected');
            
            const piece = this.cells[row][col].querySelector('.piece');
            if (piece) {
                piece.classList.remove('selected');
            }
        }
        this.selectedCell = null;
        this.clearValidMoves();
    }
    
    /**
     * 显示合法移动位置
     */
    showValidMoves(moves, board) {
        this.clearValidMoves();
        this.validMoves = moves;
        
        for (const [row, col] of moves) {
            const cell = this.cells[row][col];
            const hasPiece = board[row][col] !== null;
            
            if (hasPiece) {
                cell.classList.add('can-capture');
            } else {
                cell.classList.add('valid-move');
            }
        }
    }
    
    /**
     * 清除合法移动显示
     */
    clearValidMoves() {
        for (const [row, col] of this.validMoves) {
            this.cells[row][col].classList.remove('valid-move', 'can-capture');
        }
        this.validMoves = [];
    }
    
    /**
     * 动画移动棋子
     */
    animateMove(fromRow, fromCol, toRow, toCol, callback) {
        const fromCell = this.cells[fromRow][fromCol];
        const toCell = this.cells[toRow][toCol];
        const piece = fromCell.querySelector('.piece');
        
        if (!piece) {
            if (callback) callback();
            return;
        }
        
        // 获取位置
        const fromRect = fromCell.getBoundingClientRect();
        const toRect = toCell.getBoundingClientRect();
        
        // 创建动画棋子
        const animPiece = piece.cloneNode(true);
        animPiece.style.position = 'fixed';
        animPiece.style.left = `${fromRect.left + fromRect.width / 2 - 22}px`;
        animPiece.style.top = `${fromRect.top + fromRect.height / 2 - 22}px`;
        animPiece.style.transition = 'all 0.3s ease';
        animPiece.style.zIndex = '100';
        document.body.appendChild(animPiece);
        
        // 隐藏原棋子
        piece.style.opacity = '0';
        
        // 执行动画
        requestAnimationFrame(() => {
            animPiece.style.left = `${toRect.left + toRect.width / 2 - 22}px`;
            animPiece.style.top = `${toRect.top + toRect.height / 2 - 22}px`;
        });
        
        // 动画结束后清理
        setTimeout(() => {
            animPiece.remove();
            piece.style.opacity = '1';
            if (callback) callback();
        }, 300);
    }
    
    /**
     * 高亮最后一次移动
     */
    highlightLastMove(fromPos, toPos) {
        // 清除之前的高亮
        document.querySelectorAll('.last-move').forEach(el => {
            el.classList.remove('last-move');
        });
        
        if (fromPos && toPos) {
            this.cells[fromPos[0]][fromPos[1]].classList.add('last-move');
            this.cells[toPos[0]][toPos[1]].classList.add('last-move');
        }
    }
}

// 导出
window.BoardRenderer = BoardRenderer;
window.PIECE_NAMES = PIECE_NAMES;
window.COLUMNS = COLUMNS;

