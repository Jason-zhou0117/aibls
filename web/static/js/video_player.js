// video_player.js - 循环刷新直到服务启动

let socket = null;
let videoQueue = [];
let isPlaying = false;
let monitorTimer = null;

// ==================== DOM 元素 ====================
const videoContainer = document.getElementById('videoContainer');
const video = document.getElementById('welcomeVideo');
const statusDiv = document.getElementById('status');

// ==================== 视频队列管理 ====================
function addToQueue(videoUrl) {
    videoQueue.push(videoUrl);
    if (!isPlaying) playNext();
}

function playNext() {
    if (videoQueue.length === 0) {
        isPlaying = false;
        videoContainer.classList.remove('show');
        updateStatusText();
        return;
    }
    const nextVideo = videoQueue.shift();
    playVideo(nextVideo);
}

function playVideo(videoUrl) {
    isPlaying = true;
    video.src = videoUrl;
    video.load();
    videoContainer.classList.add('show');
    video.play().catch(() => onVideoEnded());
    updateStatusText('playing');
}

function onVideoEnded() {
    videoContainer.classList.remove('show');
    isPlaying = false;
    video.src = '';
    playNext();
}

video.addEventListener('ended', onVideoEnded);
video.addEventListener('error', () => onVideoEnded());

// ==================== WebSocket 连接 ====================
function connectWebSocket() {
    if (socket && socket.readyState === WebSocket.OPEN) return;

    updateStatusText('connecting');

    try {
        socket = new WebSocket('ws://localhost:5001/socket.io/?EIO=4&transport=websocket');

        socket.onopen = () => {
            updateStatusText('connected');
            socket.send('40');
        };

        socket.onmessage = (event) => {
            try {
                const data = event.data;
                if (typeof data === 'string') {
                    if (data.startsWith('42')) {
                        const jsonStr = data.substring(2);
                        const parsed = JSON.parse(jsonStr);
                        const eventName = parsed[0];
                        const eventData = parsed[1];
                        if (eventName === 'video_command' && eventData.action === 'play_video') {
                            let videoUrl = eventData.video_url;

                            if (videoUrl) addToQueue(videoUrl);
                        }
                    } else if (data === '3') {
                        socket.send('3');
                    }
                }
            } catch (e) {}
        };

        socket.onclose = () => {
            updateStatusText('disconnected');
            socket = null;
            // 断开后刷新页面
            setTimeout(() => location.reload(), 1000);
        };

        socket.onerror = () => {
            socket?.close();
        };

    } catch (e) {
        socket = null;
        setTimeout(() => location.reload(), 1000);
    }
}

// ==================== 服务监控（循环刷新）====================
function startMonitor() {
    const monitor = document.createElement('object');
    monitor.id = 'serviceMonitor';
    monitor.style.visibility = 'hidden';
    monitor.style.width = '0';
    monitor.style.height = '0';
    monitor.type = 'text/plain';
    document.body.appendChild(monitor);

    function checkService() {
        monitor.data = 'http://localhost:5001/health?_=' + Date.now();
    }

    monitor.onload = () => {
        // 服务可用，停止监控，连接 WebSocket
        if (monitorTimer) clearTimeout(monitorTimer);
        connectWebSocket();
    };

    monitor.onerror = () => {
        // 服务不可用，继续刷新页面（关键！）
        if (monitorTimer) clearTimeout(monitorTimer);
        monitorTimer = setTimeout(() => {
            location.reload();
        }, 2000);
    };

    // 开始监控
    checkService();
}

// ==================== UI 更新 ====================
function updateStatusText(state = null) {
    if (!statusDiv) return;

    switch (state) {
        case 'connecting':
            statusDiv.innerHTML = `⏳ 连接中...`;
            statusDiv.className = 'status';
            break;
        case 'connected':
            statusDiv.innerHTML = `🟢 已连接，等待入场...`;
            statusDiv.className = 'status connected';
            break;
        case 'disconnected':
            statusDiv.innerHTML = `🔴 连接断开，将自动恢复...`;
            statusDiv.className = 'status disconnected';
            break;
        case 'playing':
            statusDiv.innerHTML = `🎬 播放中`;
            statusDiv.className = 'status playing';
            break;
        default:
            statusDiv.innerHTML = `⚫ 等待服务...`;
            statusDiv.className = 'status';
    }
}

// ==================== 初始化 ====================
function init() {
    startMonitor();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}