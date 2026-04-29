// video_player.js - 核心逻辑
console.log(typeof io);
// ==================== 配置 ====================
const SOCKETIO_URL = 'http://localhost:5001';  // Flask 服务地址
const RECONNECT_INTERVAL = 2000;                // 重连间隔（毫秒）
const MAX_RECONNECT_ATTEMPTS = 999;             // 最大重连次数

// ==================== 全局变量 ====================
let socket = null;                   // Socket.IO 连接
let reconnectAttempts = 0;           // 重连次数
let reconnectTimer = null;           // 重连定时器
let videoQueue = [];                 // 视频队列
let isPlaying = false;               // 是否正在播放
let currentVideo = null;             // 当前播放的视频

// ==================== DOM 元素 ====================
const videoContainer = document.getElementById('videoContainer');
const video = document.getElementById('welcomeVideo');
const statusDiv = document.getElementById('status');

// ==================== 队列管理 ====================
function addToQueue(videoUrl) {
    videoQueue.push(videoUrl);
    updateStatusText();
    console.log(`📋 视频已加入队列，当前队列长度: ${videoQueue.length}`);

    if (!isPlaying) {
        playNextFromQueue();
    }
}

function playNextFromQueue() {
    if (videoQueue.length === 0) {
        isPlaying = false;
        currentVideo = null;
        videoContainer.classList.remove('show');
        updateStatusText();
        console.log('✅ 队列已空');
        return;
    }

    const nextVideoUrl = videoQueue.shift();
    playVideo(nextVideoUrl);
}

function playVideo(videoUrl) {
    isPlaying = true;
    currentVideo = videoUrl;

    console.log(`🎬 开始播放视频: ${videoUrl}`);

    // 设置视频源并播放
    video.src = videoUrl;
    video.load();
    videoContainer.classList.add('show');

    const playPromise = video.play();
    if (playPromise !== undefined) {
        playPromise.catch(error => {
            console.error('❌ 播放失败:', error);
            onVideoEnded();
        });
    }

    updateStatusText('playing');
}

function onVideoEnded() {
    console.log('🏁 视频播放结束');
    videoContainer.classList.remove('show');
    isPlaying = false;
    currentVideo = null;

    // 清空视频源，释放资源
    try {
        video.pause();
        video.src = '';
        video.load();
    } catch (e) {
        console.warn('清空视频源时出错:', e);
    }

    // 播放下一个
    playNextFromQueue();
}

// 绑定视频结束事件
video.addEventListener('ended', onVideoEnded);
video.addEventListener('error', (e) => {
    console.error('视频错误:', e);
    onVideoEnded();
});

// ==================== Socket.IO 连接（持续重连）====================
function connectSocketIO() {
    if (socket && socket.connected) {
        console.log('[Socket.IO] 已连接，无需重连');
        return;
    }

    console.log(`[Socket.IO] 尝试连接 (${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})...`);
    updateStatusText('connecting');

    try {
        socket = io(SOCKETIO_URL, {
            transports: ['websocket', 'polling'],
            reconnection: false,
            timeout: 5000
        });

        socket.on('connect', () => {
            console.log('[Socket.IO] ✅ 连接成功');
            reconnectAttempts = 0;
            updateStatusText('connected');

            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }

            // 发送注册消息
            socket.emit('register', { client: 'video_player' });
        });

        socket.on('disconnect', () => {
            console.log('[Socket.IO] 连接断开');
            updateStatusText('disconnected');
            scheduleReconnect();
        });

        socket.on('connect_error', (error) => {
            console.error('[Socket.IO] 连接错误:', error);
            scheduleReconnect();
        });

        // ========== 接收视频播放指令 ==========
        socket.on('video_command', (data) => {
            console.log('[指令] 收到 video_command 完整数据:', JSON.stringify(data, null, 2));
            console.log('[指令] data.action:', data.action);
            console.log('[指令] data.video_path:', data.video_path);

            if (data.action === 'play_video' && data.video_url) {
                console.log('[指令] 条件满足，调用 addToQueue');
                addToQueue(data.video_path);
            } else {
                console.log('[指令] 条件不满足，检查 action 和 video_path');
            }
        });

        // 心跳
        socket.on('ping', () => {
            if (socket && socket.connected) {
                socket.emit('pong');
            }
        });

    } catch (e) {
        console.error('[Socket.IO] 创建连接失败:', e);
        scheduleReconnect();
    }
}

function scheduleReconnect() {
    if (reconnectTimer) return;

    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        reconnectAttempts++;

        if (reconnectAttempts <= MAX_RECONNECT_ATTEMPTS) {
            connectSocketIO();
        } else {
            console.log('[Socket.IO] 已达最大重连次数，重置计数继续重连');
            reconnectAttempts = 0;
            scheduleReconnect();
        }
    }, RECONNECT_INTERVAL);
}

// ==================== UI 更新 ====================
function updateStatusText(state = null) {
    if (!statusDiv) return;

    switch (state) {
        case 'connecting':
            statusDiv.innerHTML = `⏳ 连接中... (${reconnectAttempts})`;
            statusDiv.className = 'status';
            break;
        case 'connected':
            statusDiv.innerHTML = `🟢 已连接，等待VIP入场... (队列: ${videoQueue.length})`;
            statusDiv.className = 'status connected';
            break;
        case 'disconnected':
            statusDiv.innerHTML = `🔴 连接断开，重连中... (${reconnectAttempts})`;
            statusDiv.className = 'status disconnected';
            break;
        case 'playing':
            statusDiv.innerHTML = `🎬 播放中 (队列: ${videoQueue.length})`;
            statusDiv.className = 'status playing';
            break;
        default:
            if (socket && socket.connected) {
                statusDiv.innerHTML = `🟢 已连接，等待VIP入场... (队列: ${videoQueue.length})`;
                statusDiv.className = 'status connected';
            } else {
                statusDiv.innerHTML = `🔴 等待连接... (${reconnectAttempts})`;
                statusDiv.className = 'status disconnected';
            }
    }
}

// ==================== 页面交互（激活播放权限）====================
function bindActivationEvents() {
    // 鼠标移入时尝试连接
    document.body.addEventListener('mouseenter', () => {
        if (!socket || !socket.connected) {
            connectSocketIO();
        }
    });

    // 点击时尝试连接
    document.body.addEventListener('click', () => {
        if (!socket || !socket.connected) {
            connectSocketIO();
        }
    });
}

// ==================== 初始化 ====================
function init() {
    console.log('[初始化] 视频播放器启动');

    bindActivationEvents();
    connectSocketIO();

    // 定期发送心跳
    setInterval(() => {
        if (socket && socket.connected) {
            socket.emit('ping');
        }
    }, 30000);

    updateStatusText();
}

// 页面加载完成后启动
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// 调试接口
window.debugVideoPlayer = () => {
    console.log({
        connected: socket ? socket.connected : false,
        reconnectAttempts: reconnectAttempts,
        queueLength: videoQueue.length,
        isPlaying: isPlaying,
        currentVideo: currentVideo
    });
};