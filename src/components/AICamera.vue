<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useAIStore } from '../store/ai'
import { audioService } from '../utils/audio'
import pushupImg from '../assets/instructions/pushup.png'
import jackImg from '../assets/instructions/jumping_jack.png'
import squatImg from '../assets/instructions/squat.png'

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
const aiStore = useAIStore()
const isModelLoading = computed(() => !aiStore.isModelReady)

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
  await aiStore.initModel()
}

const calculateAngle = (a, b, c) => {
  const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x)
  let angle = Math.abs((radians * 180.0) / Math.PI)
  if (angle > 180.0) angle = 360 - angle
  return angle
}

const detectPose = async () => {
  const detector = aiStore.detector
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
      const shoulder = keypoints.find(k => k.name === 'left_shoulder')
      const elbow = keypoints.find(k => k.name === 'left_elbow')
      const wrist = keypoints.find(k => k.name === 'left_wrist')

      if (shoulder?.score > 0.3 && elbow?.score > 0.3 && wrist?.score > 0.3) {
        const angle = calculateAngle(shoulder, elbow, wrist)
        
        if (angle < 90 && exerciseState.value === 'up') {
          exerciseState.value = 'down'
        }
        if (angle > 150 && exerciseState.value === 'down') {
          exerciseState.value = 'up'
          count.value++
          emit('count-updated', count.value)
          if (count.value >= props.targetCount) emit('completed')
        }
      }
    } 
    // Lógica para Agachamento (Squat)
    else if (props.mode === 'squat') {
      const hip = keypoints.find(k => k.name === 'left_hip')
      const knee = keypoints.find(k => k.name === 'left_knee')
      const ankle = keypoints.find(k => k.name === 'left_ankle')

      if (hip?.score > 0.3 && knee?.score > 0.3 && ankle?.score > 0.3) {
        const angle = calculateAngle(hip, knee, ankle)
        
        if (angle < 100 && exerciseState.value === 'up') {
          exerciseState.value = 'down'
        }
        if (angle > 150 && exerciseState.value === 'down') {
          exerciseState.value = 'up'
          count.value++
          emit('count-updated', count.value)
          if (count.value >= props.targetCount) emit('completed')
        }
      }
    }
    // Lógica para Polichinelo (Jumping Jack)
    else if (props.mode === 'jumping_jack') {
      const leftWrist = keypoints.find(k => k.name === 'left_wrist')
      const rightWrist = keypoints.find(k => k.name === 'right_wrist')
      const leftShoulder = keypoints.find(k => k.name === 'left_shoulder')
      const rightShoulder = keypoints.find(k => k.name === 'right_shoulder')
      const nose = keypoints.find(k => k.name === 'nose')

      if (leftWrist?.score > 0.3 && rightWrist?.score > 0.3 && nose?.score > 0.3) {
        const isHandsUp = leftWrist.y < nose.y && rightWrist.y < nose.y
        const isHandsDown = leftWrist.y > leftShoulder.y && rightWrist.y > rightShoulder.y

        if (isHandsUp) {
          exerciseState.value = 'up'
        } else if (isHandsDown) {
          if (exerciseState.value === 'up') {
            count.value++
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
    loadModel()
  }
})

onUnmounted(() => {
  stop()
})
</script>

<template>
  <div class="ai-camera-wrapper">
    <div v-if="isModelLoading" class="loading-overlay">
      <div class="onboarding-content">
        <div class="instruction-card">
          <div class="instruction-visual">
            <img v-if="mode === 'pushup'" :src="pushupImg" alt="Pushup Guide" />
            <img v-else-if="mode === 'squat'" :src="squatImg" alt="Squat Guide" />
            <img v-else :src="jackImg" alt="Jumping Jack Guide" />
          </div>

          <div class="tips-area">
            <h3>
              {{ 
                mode === 'pushup' ? 'Como fazer a Flexão' : 
                mode === 'squat' ? 'Como fazer o Agachamento' : 
                'Como fazer o Polichinelo' 
              }}
            </h3>
            <ul class="tips-list">
              <template v-if="mode === 'pushup'">
                <li>Mantenha as costas retas e o core ativado.</li>
                <li>Desça até os cotovelos formarem 90 graus.</li>
              </template>
              <template v-else-if="mode === 'squat'">
                <li>Mantenha os pés na largura dos ombros.</li>
                <li>Desça o quadril até as coxas ficarem paralelas ao chão.</li>
                <li>Mantenha o peito aberto e olhe para frente.</li>
              </template>
              <template v-else>
                <li>Pule afastando pés e mãos simultaneamente.</li>
                <li>Toque as mãos acima da cabeça.</li>
              </template>
            </ul>
          </div>
        </div>

        <div class="positioning-card">
          <h4>📍 Dicas de Posicionamento</h4>
          <div class="tips-grid">
            <div class="tip-item">
              <span class="tip-icon">📏</span>
              <p>Distância de 2-3 metros</p>
            </div>
            <div class="tip-item">
              <span class="tip-icon">💡</span>
              <p>Boa iluminação frontal</p>
            </div>
            <div class="tip-item">
              <span class="tip-icon">🧘</span>
              <p>Corpo todo visível</p>
            </div>
          </div>
        </div>

        <div class="loading-status">
          <div class="spinner-small"></div>
          <span>Inicializando Visão Computacional...</span>
        </div>
      </div>
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
  background: #0f1115;
  color: white;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.onboarding-content {
  max-width: 500px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.instruction-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0,0,0,0.4);
}

.exercise-preview {
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.exercise-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.tips-area {
  padding: 1.5rem;
}

.tips-area h3 {
  margin-bottom: 0.75rem;
  font-size: 1.1rem;
  color: var(--accent-secondary);
}

.tips-list {
  list-style: none;
  font-size: 0.9rem;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tips-list li::before {
  content: '•';
  color: var(--accent-secondary);
  margin-right: 0.5rem;
  font-weight: bold;
}

.positioning-card {
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.1);
  border-radius: var(--radius-md);
  padding: 1.25rem;
}

.positioning-card h4 {
  font-size: 0.9rem;
  margin-bottom: 1rem;
  color: white;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.tip-item {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.tip-icon {
  font-size: 1.25rem;
}

.tip-item p {
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.2;
}

.loading-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 0.5rem;
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(16, 185, 129, 0.2);
  border-top-color: #10b981;
  border-radius: 50%;
  animation: spin 1s linear infinite;
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
