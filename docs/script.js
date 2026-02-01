const videoElement = document.getElementById('inputVideo');
const canvasElement = document.getElementById('gameCanvas');
const canvasCtx = canvasElement.getContext('2d');
const scoreEl = document.getElementById('scoreVal');
const startScreen = document.getElementById('startScreen');
const pauseScreen = document.getElementById('pauseScreen');
const gameOverScreen = document.getElementById('gameOverScreen');
const finalScoreEl = document.getElementById('finalScore');
const statusText = document.querySelector('.status-text');
const startBtn = document.getElementById('startBtn');
const restartBtn = document.getElementById('restartBtn');
const pauseScoreEl = document.getElementById('pauseScoreVal');

// 游戏配置
const CONFIG = {
    cameraWidth: 1280,
    cameraHeight: 720,
    snakeSpeedPPS: 200, // 像素/秒
    segmentDist: 10, // Match Python version
    tailSmooth: 0.35, // Smoothing factor for body movement
    colors: {
        head: '#22C55E',
        bodyStart: '#22C55E',
        bodyEnd: '#15803d',
        food: '#ff0055'
    }
};

// 游戏状态
let gameState = {
    status: 'LOADING', // LOADING, STOPPED, RUNNING, PAUSED, GAMEOVER
    score: 0,
    snake: [],
    food: null,
    targetPos: null, // 指尖目标位置
    lastTime: 0
};

// 初始化画布
function resizeCanvas() {
    // 保持16:9比例
    const container = document.querySelector('.game-wrapper');
    canvasElement.width = CONFIG.cameraWidth;
    canvasElement.height = CONFIG.cameraHeight;
}
resizeCanvas();

// ==========================================
// 游戏逻辑
// ==========================================

function initGame() {
    gameState.score = 0;
    scoreEl.innerText = '0';

    // 初始化蛇（屏幕中心）
    const cx = CONFIG.cameraWidth / 2;
    const cy = CONFIG.cameraHeight / 2;
    gameState.snake = [
        { x: cx, y: cy },
        { x: cx, y: cy + CONFIG.segmentDist },
        { x: cx, y: cy + CONFIG.segmentDist * 2 }
    ];
    gameState.targetPos = { x: cx, y: cy };
    gameState.lastTime = performance.now(); // Reset timer

    spawnFood();
    gameState.status = 'RUNNING';

    startScreen.style.opacity = '0';
    setTimeout(() => startScreen.style.display = 'none', 300);
    pauseScreen.style.display = 'none';
    gameOverScreen.style.display = 'none';
    document.getElementById('scoreBoard').style.display = 'block';
}

function spawnFood() {
    // 随机生成食物，避开蛇身
    let valid = false;
    let x, y;
    while (!valid) {
        x = Math.random() * (CONFIG.cameraWidth - 40) + 20;
        y = Math.random() * (CONFIG.cameraHeight - 40) + 20;
        valid = true;
        // 简单距离检查
        const h = gameState.snake[0];
        const d = Math.hypot(x - h.x, y - h.y);
        if (d < 50) valid = false;
    }
    gameState.food = { x, y };
}

function updateGame(dt) {
    if (gameState.status !== 'RUNNING') return;

    // 1. 蛇头移动（平滑跟随目标）
    if (gameState.targetPos) {
        const head = gameState.snake[0];
        const dx = gameState.targetPos.x - head.x;
        const dy = gameState.targetPos.y - head.y;
        const dist = Math.hypot(dx, dy);

        // 只有当距离足够大时才移动，避免抖动
        if (dist > 5) {
            // 使用 Delta Time 计算当帧移动距离
            // distance = speed * time
            const moveStep = CONFIG.snakeSpeedPPS * dt;
            const moveDist = Math.min(dist, moveStep);
            const angle = Math.atan2(dy, dx);

            // 直接移动，不使用平滑，保证响应速度
            head.x += Math.cos(angle) * moveDist;
            head.y += Math.sin(angle) * moveDist;
        }
    }

    // 2. 蛇身跟随
    for (let i = 1; i < gameState.snake.length; i++) {
        const curr = gameState.snake[i];
        const prev = gameState.snake[i - 1];

        const dx = prev.x - curr.x;
        const dy = prev.y - curr.y;
        const dist = Math.hypot(dx, dy);

        if (dist > CONFIG.segmentDist) {
            const ratio = dist !== 0 ? CONFIG.segmentDist / dist : 0;
            const targetX = prev.x - dx * ratio;
            const targetY = prev.y - dy * ratio;

            // 使用帧率无关的平滑公式 (Lerp with Delta Time)
            // factor = 1 - exp(-decay * dt)
            // decay 越大越快。CONFIG.tailSmooth 调整为 decay 值，比如 10-20
            const decay = 15.0;
            const smoothFactor = 1 - Math.exp(-decay * dt);

            curr.x += (targetX - curr.x) * smoothFactor;
            curr.y += (targetY - curr.y) * smoothFactor;
        }
    }

    // 3. 碰撞检测（食物）
    if (gameState.food) {
        const head = gameState.snake[0];
        const d = Math.hypot(head.x - gameState.food.x, head.y - gameState.food.y);
        if (d < 20) { // 吃到食物
            gameState.score += 10;
            scoreEl.innerText = gameState.score;
            // 增加长度
            const tail = gameState.snake[gameState.snake.length - 1];
            gameState.snake.push({ ...tail });
            spawnFood();
        }
    }
}

function drawGame() {
    // 绘制食物 (带发光效果)
    if (gameState.food) {
        canvasCtx.shadowBlur = 15;
        canvasCtx.shadowColor = CONFIG.colors.food;
        canvasCtx.beginPath();
        canvasCtx.arc(gameState.food.x, gameState.food.y, 8, 0, 2 * Math.PI);
        canvasCtx.fillStyle = CONFIG.colors.food;
        canvasCtx.fill();
        canvasCtx.shadowBlur = 0;
    }

    // 绘制蛇
    if (gameState.snake.length > 0) {
        // 连线
        canvasCtx.beginPath();
        canvasCtx.moveTo(gameState.snake[0].x, gameState.snake[0].y);
        // 使用二次贝塞尔曲线使身体更平滑
        for (let i = 1; i < gameState.snake.length - 1; i++) {
            const xc = (gameState.snake[i].x + gameState.snake[i + 1].x) / 2;
            const yc = (gameState.snake[i].y + gameState.snake[i + 1].y) / 2;
            canvasCtx.quadraticCurveTo(gameState.snake[i].x, gameState.snake[i].y, xc, yc);
        }
        // 连接最后一段
        if (gameState.snake.length > 1) {
            const last = gameState.snake[gameState.snake.length - 1];
            canvasCtx.lineTo(last.x, last.y);
        }

        canvasCtx.lineCap = 'round';
        canvasCtx.lineJoin = 'round';
        canvasCtx.lineWidth = CONFIG.segmentDist * 1.8; // 动态调整宽度
        // 简单渐变色模拟
        const grad = canvasCtx.createLinearGradient(
            gameState.snake[0].x, gameState.snake[0].y,
            gameState.snake[gameState.snake.length - 1].x, gameState.snake[gameState.snake.length - 1].y
        );
        grad.addColorStop(0, CONFIG.colors.bodyStart);
        grad.addColorStop(1, CONFIG.colors.bodyEnd);
        canvasCtx.strokeStyle = grad;
        canvasCtx.stroke();

        // 绘制头
        canvasCtx.shadowBlur = 10;
        canvasCtx.shadowColor = CONFIG.colors.head;
        canvasCtx.beginPath();
        canvasCtx.arc(gameState.snake[0].x, gameState.snake[0].y, CONFIG.segmentDist, 0, 2 * Math.PI);
        canvasCtx.fillStyle = CONFIG.colors.head;
        canvasCtx.fill();
        canvasCtx.shadowBlur = 0;
    }

    // 绘制准星
    if (gameState.targetPos && gameState.status === 'RUNNING') {
        const { x, y } = gameState.targetPos;
        canvasCtx.strokeStyle = 'rgba(34, 197, 94, 0.5)';
        canvasCtx.lineWidth = 2;
        canvasCtx.beginPath();
        canvasCtx.moveTo(x - 15, y);
        canvasCtx.lineTo(x + 15, y);
        canvasCtx.moveTo(x, y - 15);
        canvasCtx.lineTo(x, y + 15);
        canvasCtx.stroke();
        canvasCtx.beginPath();
        canvasCtx.arc(x, y, 8, 0, 2 * Math.PI);
        canvasCtx.stroke();
    }
}

// ==========================================
// MediaPipe 手势识别
// ==========================================

const hands = new Hands({
    locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
    }
});

hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.7,
    minTrackingConfidence: 0.5
});

hands.onResults(onResults);

function onResults(results) {
    // 计算 Delta Time
    const now = performance.now();
    const dt = (now - gameState.lastTime) / 1000; // 秒
    gameState.lastTime = now;

    // 1. 绘制摄像头画面
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

    // 2. 识别逻辑
    let gesture = 'NONE';
    let fingerPos = null;

    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        const landmarks = results.multiHandLandmarks[0];

        // 获取关键点 (0-1 归一化坐标)
        const thumbTip = landmarks[4];
        const indexTip = landmarks[8];
        const middleTip = landmarks[12];
        const ringTip = landmarks[16];
        const pinkyTip = landmarks[20];

        // 简单的手指状态判断 (y坐标小于关节)
        const isIndexUp = indexTip.y < landmarks[6].y;
        const isMiddleUp = middleTip.y < landmarks[10].y;
        const isRingUp = ringTip.y < landmarks[14].y;
        const isPinkyUp = pinkyTip.y < landmarks[18].y;

        // 计算手指伸展数量
        let fingersUp = 0;
        if (isIndexUp) fingersUp++;
        if (isMiddleUp) fingersUp++;
        if (isRingUp) fingersUp++;
        if (isPinkyUp) fingersUp++;

        // OK 手势检测 (拇指与食指接触)
        const distThumbIndex = Math.hypot(thumbTip.x - indexTip.x, thumbTip.y - indexTip.y);
        const isOK = distThumbIndex < 0.05 && isMiddleUp && isRingUp;

        // 握拳检测 (所有手指都收缩)
        const isFist = fingersUp === 0;

        // 坐标映射 (MediaPipe输出是归一化的)
        fingerPos = {
            x: indexTip.x * CONFIG.cameraWidth,
            y: indexTip.y * CONFIG.cameraHeight
        };

        // 状态机流转
        if (isOK) {
            if (gameState.status === 'STOPPED' || gameState.status === 'GAMEOVER') {
                initGame();
            } else if (gameState.status === 'PAUSED') {
                // Resume game
                gameState.status = 'RUNNING';
                pauseScreen.style.display = 'none';
                // 重置时间防止跳跃
                gameState.lastTime = performance.now();
            }
        } else if (isFist) {
            if (gameState.status === 'RUNNING') {
                gameState.status = 'PAUSED';
                if (pauseScoreEl) pauseScoreEl.innerText = gameState.score;
                pauseScreen.style.display = 'flex';
            }
        } else {
            // 更新目标位置
            if (gameState.status === 'RUNNING' && fingerPos) {
                gameState.targetPos = fingerPos;
            }
        }
    }

    // 3. 游戏渲染
    // 限制最大 dt 防止切换后台后跳跃
    const safeDt = Math.min(dt, 0.1);
    updateGame(safeDt);
    drawGame();

    canvasCtx.restore();
}

// 摄像头启动
const camera = new Camera(videoElement, {
    onFrame: async () => {
        await hands.send({ image: videoElement });
    },
    width: 1280,
    height: 720
});

// 绑定按钮事件
startBtn.addEventListener('click', () => {
    initGame();
});

restartBtn.addEventListener('click', () => {
    initGame();
});

// 键盘控制 (Q键暂停/退出)
document.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 'q') {
        if (gameState.status === 'RUNNING') {
            // 暂停
            gameState.status = 'PAUSED';
            if (pauseScoreEl) pauseScoreEl.innerText = gameState.score;
            pauseScreen.style.display = 'flex';
        } else if (gameState.status === 'PAUSED') {
            // 退出到标题
            gameState.status = 'STOPPED';
            pauseScreen.style.display = 'none';
            startScreen.style.display = 'flex';
            setTimeout(() => startScreen.style.opacity = '1', 10);
        }
    }
});

// 启动流程
camera.start()
    .then(() => {
        statusText.innerText = "摄像头已就绪";
        gameState.status = 'STOPPED';
    })
    .catch(err => {
        console.error(err);
        statusText.innerText = "请允许摄像头权限以继续";
        statusText.style.color = "#ff4444";
    });
