<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { audioService } from '../utils/audio'
import { useAIStore } from '../store/ai'

const aiStore = useAIStore()
const isModelLoading = computed(() => !aiStore.isModelReady)

const props = defineProps({
  targetCount: {
    type: Number,
    default: 0
  },
  active: {
    type: Boolean,
    default: false
  },
  isFreeMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['count-updated', 'completed'])

const videoRef = ref(null)
const canvasRef = ref(null)
const outputCanvasRef = ref(null)

const count = ref(0)
const balls = ref([]) 
const targetColors = ref([{ r: 245, g: 158, b: 11 }]) 
const tolerance = ref(70) 
const isMirrored = ref(false) // Mudado para falso como padrão baseado no feedback
const mousePos = ref({ x: 0, y: 0 }) 

let animationId = null
let stream = null

// Configurações de rastreamento
const MAX_BALLS = 5

const lastAction = ref('') 
const showFeedback = ref(false)
const debugTime = ref('') 
let prevFrameData = null // Para detecção de movimento

const initCamera = async () => {
  console.log('Tentando acessar a câmera...')
  try {
    stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        width: { ideal: 640 }, 
        height: { ideal: 480 }, 
        facingMode: 'user' 
      } 
    })
    
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      
      // Esperar metadados e forçar o play
      await new Promise((resolve) => {
        videoRef.value.onloadedmetadata = () => {
          console.log('Metadados carregados:', videoRef.value.videoWidth, 'x', videoRef.value.videoHeight)
          resolve()
        }
      })
      
      await videoRef.value.play()
      console.log('Vídeo em execução')
      
      // Forçar dimensões iniciais do canvas
      if (canvasRef.value && outputCanvasRef.value) {
        const w = videoRef.value.videoWidth
        const h = videoRef.value.videoHeight
        canvasRef.value.width = w
        canvasRef.value.height = h
        outputCanvasRef.value.width = w
        outputCanvasRef.value.height = h
      }
    }
  } catch (e) {
    console.error("Erro fatal ao iniciar câmera:", e)
    alert("Não foi possível acessar a câmera. Verifique as permissões.")
  }
}

const calibrateColor = (event) => {
  if (!videoRef.value || !outputCanvasRef.value) return
  
  const video = videoRef.value
  const canvas = outputCanvasRef.value
  
  // offsetX e offsetY já nos dão a posição dentro do canvas
  const xRatio = event.offsetX / canvas.clientWidth
  const yRatio = event.offsetY / canvas.clientHeight
  
  // Se estiver espelhado, invertemos o X
  const finalXRatio = isMirrored.value ? (1 - xRatio) : xRatio
  
  const x = Math.floor(video.videoWidth * finalXRatio)
  const y = Math.floor(video.videoHeight * yRatio)

  const tempCanvas = document.createElement('canvas')
  tempCanvas.width = 1
  tempCanvas.height = 1
  const tempCtx = tempCanvas.getContext('2d')
  
  tempCtx.drawImage(video, x, y, 1, 1, 0, 0, 1, 1)
  const pixel = tempCtx.getImageData(0, 0, 1, 1).data
  
  if (pixel[3] > 0) {
    const newColor = { r: pixel[0], g: pixel[1], b: pixel[2] }
    if (targetColors.value.length < 5) {
      targetColors.value.push(newColor)
    } else {
      targetColors.value.shift()
      targetColors.value.push(newColor)
    }
    
    lastAction.value = `Calibrado! RGB(${newColor.r},${newColor.g},${newColor.b})`
    showFeedback.value = true
    setTimeout(() => { showFeedback.value = false }, 2000)
    audioService.playClick()
  }
}

const clearColors = () => {
  targetColors.value = []
  audioService.playClick()
}

const updateMousePos = (event) => {
  mousePos.value = { x: event.offsetX, y: event.offsetY }
}

// Utilitário para converter RGB para HSV
const rgbToHsv = (r, g, b) => {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, v = max;
  const d = max - min;
  s = max === 0 ? 0 : d / max;
  if (max === min) {
    h = 0;
  } else {
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }
  return { h: h * 360, s: s * 100, v: v * 100 };
}

const processFrame = async () => {
  try {
    if (!videoRef.value || !outputCanvasRef.value) return
    
    const video = videoRef.value
    const outCanvas = outputCanvasRef.value
    const outCtx = outCanvas.getContext('2d', { willReadFrequently: true })

  // GARANTIR DIMENSÕES
  if (outCanvas.width !== video.videoWidth || outCanvas.width === 0) {
    outCanvas.width = video.videoWidth || 640
    outCanvas.height = video.videoHeight || 480
    console.log('Canvas redimensionado para:', outCanvas.width, 'x', outCanvas.height)
  }

  // LIMPAR TELA (Evita que as imagens se somem)
  outCtx.clearRect(0, 0, outCanvas.width, outCanvas.height)
  
  // Atualizar tempo de debug para provar que está rodando
  debugTime.value = new Date().toLocaleTimeString()

  // 1. Detecção de Pose (Mãos) - FORÇA TOTAL
  let handKeypoints = []
  if (aiStore.isModelReady && aiStore.detector) {
    try {
      const poses = await aiStore.detector.estimatePoses(video)
      if (poses && poses.length > 0) {
        handKeypoints = poses[0].keypoints.filter(k => 
          (k.name === 'left_wrist' || k.name === 'right_wrist') && k.score > 0.3
        )
      }
    } catch (e) { console.error('Erro MoveNet:', e) }
  }

  // 2. Desenhar o vídeo na tela (SEM transparência no processamento para não estragar a cor)
  outCtx.save()
  if (isMirrored.value) {
    outCtx.scale(-1, 1)
    outCtx.drawImage(video, -outCanvas.width, 0, outCanvas.width, outCanvas.height)
  } else {
    outCtx.drawImage(video, 0, 0, outCanvas.width, outCanvas.height)
  }
  outCtx.restore()

  // 3. Detecção de Movimento (Frame Differencing)
  const frame = outCtx.getImageData(0, 0, outCanvas.width, outCanvas.height)
  const pixels = frame.data
  const detectedPoints = []
  let pointsFound = 0

  if (prevFrameData) {
    // Comparar frame atual com o anterior
    for (let i = 0; i < pixels.length; i += 4 * 10) { // Salto maior para performance
      const r = pixels[i], g = pixels[i+1], b = pixels[i+2]
      const pr = prevFrameData[i], pg = prevFrameData[i+1], pb = prevFrameData[i+2]
      
      // Diferença absoluta de brilho/cor
      const diff = Math.abs(r - pr) + Math.abs(g - pg) + Math.abs(b - pb)
      
      // Se houve movimento significativo (> 60)
      if (diff > 60) {
        const x = (i / 4) % outCanvas.width
        const y = Math.floor((i / 4) / outCanvas.width)
        
        // MÁSCARA DE MÃO: Ignorar movimento muito perto dos pulsos (ruído da mão)
        const isNearHand = handKeypoints.some(hand => 
          Math.hypot(x - hand.x, y - hand.y) < 50
        )

        if (!isNearHand) {
          detectedPoints.push({ x, y })
          pointsFound++
          
          // Debug visual opcional (pontinho ciano para movimento)
          outCtx.fillStyle = 'rgba(0, 255, 255, 0.5)'
          outCtx.fillRect(x, y, 2, 2)
        }
      }
    }
  }
  
  // Salvar frame atual para a próxima comparação
  prevFrameData = new Uint8ClampedArray(pixels)
  
  debugPointsCount.value = pointsFound

  // Desenhar MIRA e Mãos
  if (mousePos.value.x > 0) {
    outCtx.save()
    outCtx.lineWidth = 2
    outCtx.shadowBlur = 5
    outCtx.shadowColor = '#fff'
    
    // Cruz
    outCtx.moveTo(mousePos.value.x - 15, mousePos.value.y)
    outCtx.lineTo(mousePos.value.x + 15, mousePos.value.y)
    outCtx.moveTo(mousePos.value.x, mousePos.value.y - 15)
    outCtx.lineTo(mousePos.value.x, mousePos.value.y + 15)
    outCtx.stroke()
    
    // Círculo
    outCtx.beginPath()
    outCtx.arc(mousePos.value.x, mousePos.value.y, 8, 0, Math.PI * 2)
    outCtx.stroke()
    outCtx.restore()
  }

  // Desenhar Indicadores das Mãos (Respeitando Espelhamento)
  handKeypoints.forEach(hand => {
    const screenX = isMirrored.value ? (outCanvas.width - hand.x) : hand.x
    outCtx.beginPath()
    outCtx.arc(screenX, hand.y, 50, 0, Math.PI * 2)
    outCtx.strokeStyle = 'rgba(59, 130, 246, 0.8)' 
    outCtx.lineWidth = 4
    outCtx.stroke()
    
    outCtx.fillStyle = 'rgba(59, 130, 246, 0.2)'
    outCtx.fill()
  })

  updateBallTracking(detectedPoints, outCtx, handKeypoints)

  } catch (err) {
    console.error('Erro no loop de frames:', err)
  } finally {
    if (props.active) {
      animationId = requestAnimationFrame(processFrame)
    }
  }
}

const updateBallTracking = (points, ctx, handKeypoints = []) => {
  if (points.length < 3) return // Baixado de 10 para 3 para ser mais sensível

  // 1. Agrupamento (Clustering)
  const clusters = []
  const DIST_THRESHOLD = 60 // Aumentado para agrupar cores diferentes da mesma bola

  points.forEach(p => {
    let joined = false
    for (const cluster of clusters) {
      const dist = Math.hypot(p.x - cluster.avgX, p.y - cluster.avgY)
      if (dist < DIST_THRESHOLD) {
        cluster.points.push(p)
        cluster.avgX = (cluster.avgX * (cluster.points.length - 1) + p.x) / cluster.points.length
        cluster.avgY = (cluster.avgY * (cluster.points.length - 1) + p.y) / cluster.points.length
        joined = true
        break
      }
    }
    if (!joined) {
      clusters.push({ points: [p], avgX: p.x, avgY: p.y })
    }
  })

  const validClusters = clusters
    .filter(c => {
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
      c.points.forEach(p => {
        minX = Math.min(minX, p.x); minY = Math.min(minY, p.y)
        maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y)
      })
      const w = maxX - minX, h = maxY - minY
      const ratio = w / h
      
      // MAIS FLEXÍVEL: No modo movimento, a bola pode ser um rastro alongado (0.3 a 3.0)
      const isBallShape = ratio > 0.3 && ratio < 3.0
      
      return c.points.length >= 4 && w > 10 && h > 10 && w < 180 && h < 180 && isBallShape
    })
    .sort((a, b) => b.points.length - a.points.length)
    .slice(0, MAX_BALLS)

  validClusters.forEach((cluster, index) => {
    if (!balls.value[index]) {
      balls.value[index] = { x: cluster.avgX, y: cluster.avgY, dy: 0, trail: [] }
    }
    
    const ball = balls.value[index]
    const alpha = 0.5
    const oldY = ball.y
    
    ball.x = ball.x * (1 - alpha) + cluster.avgX * alpha
    ball.y = ball.y * (1 - alpha) + cluster.avgY * alpha
    
    const dy = ball.y - oldY
    
    // Calcular Bounding Box do cluster
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    cluster.points.forEach(p => {
      minX = Math.min(minX, p.x); minY = Math.min(minY, p.y)
      maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y)
    })

    const width = maxX - minX
    const height = maxY - minY
    const screenX = isMirrored.value ? (ctx.canvas.width - (minX + width/2)) : (minX + width/2)

    // Visualização: Box Ciano
    ctx.strokeStyle = '#00ffff'
    ctx.lineWidth = 3 // Linha mais grossa
    ctx.strokeRect(
      isMirrored.value ? (ctx.canvas.width - maxX) : minX, 
      minY, 
      width, 
      height
    )
    
    // Indicador de centro
    ctx.beginPath()
    ctx.arc(screenX, minY + height/2, 4, 0, Math.PI * 2)
    ctx.fillStyle = '#00ffff'
    ctx.fill()
    
    // Lógica de Catch (Adaptada para Radar de Movimento)
    const nearHand = handKeypoints.some(hand => 
      Math.hypot(ball.x - hand.x, ball.y - hand.y) < 100
    )

    // Se a bola estava caindo (dy > 0.5)
    if (ball.dy > 0.5) {
      // Caso A: Mudou de direção (rebatida)
      if (dy < 0) {
        handleCatch()
      } 
      // Caso B: Sumiu do radar subitamente perto da mão (foi pega)
      // (Isso será tratado pela persistência abaixo)
    }
    
    ball.dy = dy
    ball.lastSeen = Date.now()
  })

  // 3. Persistência: Remover bolas que sumiram há muito tempo (mais de 500ms)
  // Ou contar como catch se sumiu enquanto caía perto da mão
  balls.value = balls.value.filter(ball => {
    const timeSinceSeen = Date.now() - (ball.lastSeen || 0)
    
    if (timeSinceSeen > 100 && timeSinceSeen < 300 && ball.dy > 0.5) {
      const nearHand = handKeypoints.some(hand => 
        Math.hypot(ball.x - hand.x, ball.y - hand.y) < 100
      )
      if (nearHand) {
        handleCatch()
        ball.dy = 0 // Evita contar o mesmo catch duas vezes
        return false
      }
    }

    return timeSinceSeen < 500
  })
}

const handleCatch = () => {
  count.value++
  audioService.playClick() // Feedback imediato
  emit('count-updated', count.value)
  if (props.targetCount > 0 && count.value >= props.targetCount) {
    emit('completed')
  }
}

const start = async () => {
  console.log('Iniciando Juggling Camera...')
  targetColors.value = [] // Resetar ao iniciar para garantir calibração fresca
  try {
    await initCamera()
    console.log('Câmera OK, iniciando loop de frames')
    processFrame()
    
    if (!aiStore.isModelReady) {
      console.log('IA não está pronta, carregando em background...')
      aiStore.initModel() // Carrega sem dar await para não travar a câmera
    }
  } catch (err) {
    console.error('Falha crítica no start:', err)
  }
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
  if (newVal) start()
  else stop()
})

onMounted(() => {
  if (props.active) start()
})

onUnmounted(() => {
  stop()
})
</script>

<template>
  <div class="juggling-ai-wrapper" @mousemove="updateMousePos">
    <div class="stats-overlay">
      <div class="counter-badge" :class="{ 'is-free': isFreeMode }">
        <span class="label">{{ isFreeMode ? 'TREINO LIVRE' : 'CATCHES' }}</span>
        <span class="value">{{ count }}</span>
      </div>
      <div class="target-badge" v-if="!isFreeMode && targetCount > 0">Meta: {{ targetCount }}</div>
    </div>

    <div class="calibration-hint" v-if="targetColors.length === 0 && active">
      Toque na bola na tela para calibrar a cor
    </div>

    <div class="debug-overlay" v-if="active">
      {{ debugTime }} | {{ debugPointsCount }} pts
    </div>

    <div class="action-toast" v-if="showFeedback">
      {{ lastAction }}
    </div>

    <!-- Mira Física (DOM) -->
    <div 
      class="visual-crosshair" 
      v-if="active && mousePos.x > 0"
      :style="{ left: mousePos.x + 'px', top: mousePos.y + 'px' }"
    ></div>

    <div class="controls-panel" v-if="active">
      <div class="control-item">
        <div class="panel-header">
          <label>Cores Alvo</label>
          <button class="btn-tiny" @click="clearColors">Limpar</button>
        </div>
        <div class="colors-grid">
          <div v-for="(c, i) in targetColors" :key="i" 
               class="color-dot" :style="{ backgroundColor: `rgb(${c.r}, ${c.g}, ${c.b})` }"></div>
        </div>
      </div>
      <div class="control-item">
        <label>Espelhamento</label>
        <button class="btn-tiny" @click="isMirrored = !isMirrored">
          {{ isMirrored ? 'Ligado' : 'Desligado' }}
        </button>
      </div>
      <div class="control-item">
        <label>Sensibilidade</label>
        <input type="range" v-model="tolerance" min="20" max="150" />
      </div>
    </div>

    <!-- Canvas de Saída (Visível) -->
    <canvas 
      ref="outputCanvasRef" 
      class="output-canvas" 
      @click="calibrateColor"
      @mousemove="updateMousePos"
    ></canvas>
    
    <!-- Elementos técnicos (Escondidos mas ativos) -->
    <video ref="videoRef" playsinline muted class="hidden-video"></video>
    <canvas ref="canvasRef" class="hidden-canvas"></canvas>
  </div>
</template>

<style scoped>
.juggling-ai-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #000;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 2px solid var(--border-subtle);
}

.output-canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hidden-canvas {
  display: none;
}

.hidden-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
  opacity: 0; /* Totalmente invisível para não confundir */
  pointer-events: none;
}

.output-canvas {
  position: relative;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
  background: transparent;
  /* Removido o blur e brightness para teste de clareza */
}

.stats-overlay {
  position: absolute;
  top: 1rem;
  left: 1rem;
  right: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  z-index: 10;
  pointer-events: none; /* Permite que o clique passe para o canvas abaixo */
}

.counter-badge, .target-badge {
  pointer-events: auto; /* Mas os botões/crachás em si podem ser clicados se precisarem */
}

.counter-badge {
  background: rgba(15, 17, 21, 0.8);
  backdrop-filter: blur(10px);
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--accent-primary);
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

.counter-badge .label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--accent-primary);
}

.counter-badge .value {
  font-size: 2.5rem;
  font-weight: 900;
  line-height: 1;
  font-family: var(--font-heading);
}

.target-badge {
  background: rgba(0,0,0,0.5);
  padding: 0.5rem 1rem;
  border-radius: var(--radius-full);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.calibration-hint {
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(139, 92, 246, 0.9);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-full);
  font-size: 0.9rem;
  font-weight: 600;
  animation: pulse 2s infinite;
  z-index: 10;
  white-space: nowrap;
  pointer-events: none; /* Não bloqueia o clique */
}

@keyframes pulse {
  0% { opacity: 0.8; transform: translateX(-50%) scale(1); }
  50% { opacity: 1; transform: translateX(-50%) scale(1.05); }
  100% { opacity: 0.8; transform: translateX(-50%) scale(1); }
}

.controls-panel {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  background: rgba(0,0,0,0.7);
  padding: 1rem;
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 20;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.control-item label {
  font-size: 0.7rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.btn-tiny {
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  font-size: 0.6rem;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
}

.colors-grid {
  display: flex;
  gap: 4px;
  margin-bottom: 0.5rem;
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.3);
}

.action-toast {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(16, 185, 129, 0.9);
  color: white;
  padding: 1rem 2rem;
  border-radius: var(--radius-md);
  font-weight: bold;
  z-index: 100;
  animation: popIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes popIn {
  from { opacity: 0; transform: translate(-50%, -40%) scale(0.8); }
  to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
}

.debug-overlay {
  position: absolute;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.5);
  color: #00ff00;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.7rem;
  z-index: 100;
}

.visual-crosshair {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid #ff0000;
  border-radius: 50%;
  pointer-events: none;
  z-index: 999;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 10px #fff, inset 0 0 5px #fff;
}

.visual-crosshair::before,
.visual-crosshair::after {
  content: '';
  position: absolute;
  background: #ff0000;
  box-shadow: 0 0 5px #fff;
}

.visual-crosshair::before {
  top: 50%;
  left: -10px;
  width: 40px;
  height: 2px;
  transform: translateY(-50%);
}

.visual-crosshair::after {
  left: 50%;
  top: -10px;
  width: 2px;
  height: 40px;
  transform: translateX(-50%);
}
</style>
