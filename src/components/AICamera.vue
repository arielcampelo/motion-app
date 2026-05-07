<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  targetCount: {
    type: Number,
    default: 10
  },
  active: {
    type: Boolean,
    default: false
  },
  mode: {
    type: String,
    default: 'pushup' // 'pushup' or 'jumping_jack'
  }
})

const emit = defineEmits(['count-updated', 'completed'])

const videoRef = ref(null)
const canvasRef = ref(null)
const isModelLoading = ref(true)
const count = ref(0)
const exerciseState = ref('down') // 'up' or 'down'

let detector = null
let animationId = null
let stream = null

const initCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ 
      video: { width: 640, height: 480, facingMode: 'user' } 
    })
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      await new Promise(resolve => {
        videoRef.value.onloadedmetadata = () => resolve()
      })
      videoRef.value.play()
    }
  } catch (e) {
    console.error("Erro ao iniciar câmera", e)
  }
}

const loadModel = async () => {
  if (!window.poseDetection) {
    console.error("Pose detection library not loaded")
    return
  }
  const model = window.poseDetection.SupportedModels.MoveNet
  const detectorConfig = { modelType: window.poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING }
  detector = await window.poseDetection.createDetector(model, detectorConfig)
  isModelLoading.value = false
}

const calculateAngle = (a, b, c) => {
  const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x)
  let angle = Math.abs((radians * 180.0) / Math.PI)
  if (angle > 180.0) angle = 360 - angle
  return angle
}

const detectPose = async () => {
  if (!detector || !videoRef.value || !canvasRef.value) return

  const video = videoRef.value
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  const poses = await detector.estimatePoses(video)
  
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

  if (poses.length > 0) {
    const keypoints = poses[0].keypoints

    const validPoints = keypoints.filter(k => k.score > 0.3)
    
    ctx.fillStyle = '#10b981'
    validPoints.forEach(point => {
      ctx.beginPath()
      ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI)
      ctx.fill()
    })

    const leftShoulder = keypoints.find(k => k.name === 'left_shoulder')
    const leftElbow = keypoints.find(k => k.name === 'left_elbow')
    const leftWrist = keypoints.find(k => k.name === 'left_wrist')

    const rightShoulder = keypoints.find(k => k.name === 'right_shoulder')
    const rightElbow = keypoints.find(k => k.name === 'right_elbow')
    const rightWrist = keypoints.find(k => k.name === 'right_wrist')
    
    const nose = keypoints.find(k => k.name === 'nose')

    ctx.strokeStyle = '#f59e0b'
    ctx.lineWidth = 4

    const drawLine = (p1, p2) => {
      if (p1 && p2 && p1.score > 0.3 && p2.score > 0.3) {
        ctx.beginPath()
        ctx.moveTo(p1.x, p1.y)
        ctx.lineTo(p2.x, p2.y)
        ctx.stroke()
      }
    }

    drawLine(leftShoulder, leftElbow)
    drawLine(leftElbow, leftWrist)
    drawLine(rightShoulder, rightElbow)
    drawLine(rightElbow, rightWrist)
    drawLine(leftShoulder, rightShoulder)

    if (props.mode === 'pushup') {
      let activeSide = null
      if (leftElbow && leftElbow.score > 0.3 && rightElbow && rightElbow.score > 0.3) {
        activeSide = leftElbow.score > rightElbow.score ? 'left' : 'right'
      } else if (leftElbow && leftElbow.score > 0.3) {
        activeSide = 'left'
      } else if (rightElbow && rightElbow.score > 0.3) {
        activeSide = 'right'
      }

      if (activeSide) {
        const shoulder = activeSide === 'left' ? leftShoulder : rightShoulder
        const elbow = activeSide === 'left' ? leftElbow : rightElbow
        const wrist = activeSide === 'left' ? leftWrist : rightWrist

        if (shoulder && wrist && shoulder.score > 0.3 && wrist.score > 0.3) {
          const angle = calculateAngle(shoulder, elbow, wrist)

          if (angle > 150) {
            if (exerciseState.value === 'down') {
              count.value += 1
              exerciseState.value = 'up'
              emit('count-updated', count.value)
              if (count.value >= props.targetCount) emit('completed')
            }
          } else if (angle < 90) {
            exerciseState.value = 'down'
          }

          ctx.fillStyle = 'white'
          ctx.font = '24px Arial'
          ctx.fillText(`${Math.round(angle)}°`, elbow.x + 15, elbow.y)
        }
      }
    } else if (props.mode === 'jumping_jack') {
      // Jumping Jack Logic
      if (leftWrist && rightWrist && leftShoulder && rightShoulder && nose &&
          leftWrist.score > 0.3 && rightWrist.score > 0.3 && nose.score > 0.3) {
        
        const isHandsUp = leftWrist.y < nose.y && rightWrist.y < nose.y
        const isHandsDown = leftWrist.y > leftShoulder.y && rightWrist.y > rightShoulder.y

        if (isHandsUp) {
          exerciseState.value = 'up'
        } else if (isHandsDown) {
          if (exerciseState.value === 'up') {
            count.value += 1
            exerciseState.value = 'down'
            emit('count-updated', count.value)
            if (count.value >= props.targetCount) emit('completed')
          }
        }
      }
    }
  }

  if (props.active) {
    animationId = requestAnimationFrame(detectPose)
  }
}

const start = async () => {
  await initCamera()
  if (isModelLoading.value) {
    await loadModel()
  }
  detectPose()
}

const stop = () => {
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
}

watch(() => props.active, (newVal) => {
  if (newVal) {
    start()
  } else {
    stop()
  }
})

onMounted(() => {
  if (props.active) {
    start()
  } else {
    loadModel() // pre-load in background
  }
})

onUnmounted(() => {
  stop()
})
</script>

<template>
  <div class="ai-camera-wrapper">
    <div v-if="isModelLoading" class="loading-overlay">
      <div class="spinner"></div>
      <span>Carregando IA...</span>
    </div>
    
    <div class="stats-overlay" v-if="!isModelLoading">
      <div class="counter">{{ count }} / {{ targetCount }}</div>
      <div class="state-badge" :class="exerciseState">
        <template v-if="mode === 'pushup'">
          {{ exerciseState === 'down' ? 'Suba!' : 'Desça' }}
        </template>
        <template v-else>
          {{ exerciseState === 'down' ? 'Pule!' : 'Desça' }}
        </template>
      </div>
    </div>

    <!-- Hidden video element, we only show the canvas -->
    <video ref="videoRef" playsinline class="hidden-video"></video>
    <canvas ref="canvasRef" class="output-canvas"></canvas>
  </div>
</template>

<style scoped>
.ai-camera-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #000;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  border: 2px solid var(--border-subtle);
}

.hidden-video {
  display: none;
}

.output-canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1); /* Espelhar a câmera como em um espelho */
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(15, 17, 21, 0.8);
  color: #10b981;
  z-index: 10;
  font-weight: 500;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(16, 185, 129, 0.2);
  border-top-color: #10b981;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.stats-overlay {
  position: absolute;
  top: 1rem;
  left: 1rem;
  right: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 5;
}

.counter {
  background: rgba(0,0,0,0.6);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-full);
  font-family: var(--font-heading);
  font-size: 1.5rem;
  font-weight: 800;
  color: white;
  border: 1px solid rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
}

.state-badge {
  background: rgba(0,0,0,0.6);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-full);
  font-weight: bold;
  backdrop-filter: blur(10px);
  text-transform: uppercase;
  font-size: 0.9rem;
}

.state-badge.up {
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.state-badge.down {
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}
</style>
