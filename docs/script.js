const videoElement = document.getElementById('inputVideo');
const canvasElement = document.getElementById('gameCanvas');
const canvasCtx = canvasElement.getContext('2d');
const scoreEl = document.getElementById('scoreVal');
const startScreen = document.getElementById('startScreen');
const pauseScreen = document.getElementById('pauseScreen');
const gameOverScreen = document.getElementById('gameOverScreen');
const finalScoreEl = document.getElementById('finalScore');
const statusText = document.querySelector('.status-text');

// 游戏配置
const CONFIG = {
    cameraWidth: 1280,
    cameraHeight: 720,
    snakeSpeed: 3,
    segmentDist: 15,
    colors: {
        head: '#00ff00',
        bodyStart: [0, 200, 0],
        bodyEnd: [0, 100, 0],
        food: '#ff0000'
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
        {x: cx, y: cy},
        {x: cx, y: cy + CONFIG.segmentDist},
        {x: cx, y: cy + CONFIG.segmentDist * 2}
    ];
    gameState.targetPos = {x: cx, y: cy};
    
    spawnFood();
    gameState.status = 'RUNNING';
    
    startScreen.style.display = 'none';
    pauseScreen.style.display = 'none';
    gameOverScreen.style.display = 'none';
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
    gameState.food = {x, y};
}

function updateGame() {
    if (gameState.status !== 'RUNNING') return;

    // 1. 蛇头移动（平滑跟随目标）
    if (gameState.targetPos) {
        const head = gameState.snake[0];
        const dx = gameState.targetPos.x - head.x;
        const dy = gameState.targetPos.y - head.y;
        const dist = Math.hypot(dx, dy);
        
        // 只有当距离足够大时才移动，避免抖动
        if (dist > 5) {
            const speed = CONFIG.snakeSpeed + (gameState.score * 0.05); // 随分数微量加速
            const moveDist = Math.min(dist, speed);
            const angle = Math.atan2(dy, dx);
            
            head.x += Math.cos(angle) * moveDist;
            head.y += Math.sin(angle) * moveDist;
        }
    }

    // 2. 蛇身跟随
    // 算法：每一节朝向上一节的目标位置移动，保持固定间距
    // 这里使用简化版：重新计算每个关节的位置
    // 为了平滑效果，我们让每个关节追踪上一节的历史位置会更好，
    // 但简单的 IK (Inverse Kinematics) 风格跟随在这里也够用
    for (let i = 1; i < gameState.snake.length; i++) {
        const curr = gameState.snake[i];
        const prev = gameState.snake[i-1];
        
        const dx = prev.x - curr.x;
        const dy = prev.y - curr.y;
        const dist = Math.hypot(dx, dy);
        
        if (dist > CONFIG.segmentDist) {
            const angle = Math.atan2(dy, dx);
            // 移动到距离上一节 segmentDist 的位置
            curr.x = prev.x - Math.cos(angle) * CONFIG.segmentDist;
            curr.y = prev.y - Math.sin(angle) * CONFIG.segmentDist;
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
            gameState.snake.push({...tail});
            spawnFood();
        }
    }
}

function drawGame() {
    // 绘制食物
    if (gameState.food) {
        canvasCtx.beginPath();
        canvasCtx.arc(gameState.food.x, gameState.food.y, 10, 0, 2 * Math.PI);
        canvasCtx.fillStyle = CONFIG.colors.food;
        canvasCtx.fill();
        canvasCtx.strokeStyle = 'white';
        canvasCtx.lineWidth = 2;
        canvasCtx.stroke();
    }

    // 绘制蛇
    if (gameState.snake.length > 0) {
        // 连线
        canvasCtx.beginPath();
        canvasCtx.moveTo(gameState.snake[0].x, gameState.snake[0].y);
        // 使用二次贝塞尔曲线使身体更平滑
        for (let i = 1; i < gameState.snake.length - 1; i++) {
            const xc = (gameState.snake[i].x + gameState.snake[i+1].x) / 2;
            const yc = (gameState.snake[i].y + gameState.snake[i+1].y) / 2;
            canvasCtx.quadraticCurveTo(gameState.snake[i].x, gameState.snake[i].y, xc, yc);
        }
        // 连接最后一段
        if (gameState.snake.length > 1) {
            const last = gameState.snake[gameState.snake.length-1];
            canvasCtx.lineTo(last.x, last.y);
        }
        
        canvasCtx.lineCap = 'round';
        canvasCtx.lineJoin = 'round';
        canvasCtx.lineWidth = 20;
        // 简单渐变色模拟
        const grad = canvasCtx.createLinearGradient(
            gameState.snake[0].x, gameState.snake[0].y,
            gameState.snake[gameState.snake.length-1].x, gameState.snake[gameState.snake.length-1].y
        );
        grad.addColorStop(0, '#00ff00');
        grad.addColorStop(1, '#006400');
        canvasCtx.strokeStyle = grad;
        canvasCtx.stroke();

        // 绘制头
        canvasCtx.beginPath();
        canvasCtx.arc(gameState.snake[0].x, gameState.snake[0].y, 12, 0, 2 * Math.PI);
        canvasCtx.fillStyle = '#00ff00';
        canvasCtx.fill();
        canvasCtx.strokeStyle = 'white';
        canvasCtx.lineWidth = 2;
        canvasCtx.stroke();
    }

    // 绘制准星
    if (gameState.targetPos && gameState.status === 'RUNNING') {
        const {x, y} = gameState.targetPos;
        canvasCtx.strokeStyle = 'rgba(0, 255, 255, 0.5)';
        canvasCtx.lineWidth = 2;
        canvasCtx.beginPath();
        canvasCtx.moveTo(x - 10, y);
        canvasCtx.lineTo(x + 10, y);
        canvasCtx.moveTo(x, y - 10);
        canvasCtx.lineTo(x, y + 10);
        canvasCtx.stroke();
        canvasCtx.beginPath();
        canvasCtx.arc(x, y, 5, 0, 2 * Math.PI);
        canvasCtx.stroke();
    }
}

// ==========================================
// MediaPipe 手势识别
// ==========================================

const hands = new Hands({locateFile: (file) => {
    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
}});

hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.7,
    minTrackingConfidence: 0.5
});

hands.onResults(onResults);

function onResults(results) {
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
        const wrist = landmarks[0];

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

        // 握拳检测
        const isFist = fingersUp === 0;

        // 指向检测 (食指伸出)
        // 实际上只要食指伸出，我们就用食指作为光标
        
        // 坐标映射 (MediaPipe输出是归一化的，且因为我们Canvas做了镜像翻转scaleX(-1)，
        // 所以x坐标需要反转一下才能对应屏幕视觉位置？
        // 不，Canvas镜像了，绘制drawImage也是镜像的。
        // MediaPipe给出的x是 0(左) -> 1(右)。
        // 在镜像Canvas上，左边是1，右边是0。
        // 所以我们需要 1 - x 吗？
        // 让我们看看：如果我在摄像头前向左移（屏幕右边），x变大。
        // 在镜像屏幕上，这应该显示在右边。
        // 所以直接用 x * width 即可。
        
        fingerPos = {
            x: indexTip.x * CONFIG.cameraWidth,
            y: indexTip.y * CONFIG.cameraHeight
        };

        // 状态机流转
        if (isOK) {
            if (gameState.status === 'STOPPED' || gameState.status === 'GAMEOVER' || gameState.status === 'PAUSED') {
                initGame();
            }
        } else if (isFist) {
            if (gameState.status === 'RUNNING') {
                gameState.status = 'PAUSED';
                pauseScreen.style.display = 'flex';
            }
        } else {
            // 更新目标位置
            if (gameState.status === 'RUNNING' && fingerPos) {
                gameState.targetPos = fingerPos;
            }
        }

        // 绘制骨架 (可选)
        // drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00FF00', lineWidth: 2});
        // drawLandmarks(canvasCtx, landmarks, {color: '#FF0000', lineWidth: 1});
    }

    // 3. 游戏渲染
    updateGame();
    drawGame();

    canvasCtx.restore();
}

// 摄像头启动
const camera = new Camera(videoElement, {
    onFrame: async () => {
        await hands.send({image: videoElement});
    },
    width: 1280,
    height: 720
});

camera.start()
    .then(() => {
        statusText.innerText = "准备就绪！请做 👌 手势开始";
        gameState.status = 'STOPPED';
    })
    .catch(err => {
        console.error(err);
        statusText.innerText = "摄像头启动失败，请允许权限";
        statusText.style.color = "red";
    });
