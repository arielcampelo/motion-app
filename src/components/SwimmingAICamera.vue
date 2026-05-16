<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  active:      { type: Boolean, default: false },
  laneLength:  { type: Number,  default: 25 }
})
const emit = defineEmits(['distance-updated', 'lap-completed', 'close'])

// ── DOM refs ──────────────────────────────────────────────────────────────────
const videoRef      = ref(null)
const processCanvas = ref(null)   // hidden – pixel work
const displayCanvas = ref(null)   // shown – overlay

// ── Phase ─────────────────────────────────────────────────────────────────────
// 'setup' | 'calibrating' | 'tracking'
const phase = ref('setup')

// ── Cap color (persisted) ─────────────────────────────────────────────────────
const stored = localStorage.getItem('motion-swim-cap-color')
const capColor      = ref(stored ? JSON.parse(stored) : { r: 255, g: 50, b: 50 })
const tolerance     = ref(Number(localStorage.getItem('motion-swim-tolerance') || '60'))
const isPickingColor = ref(false)
const colorPreview  = computed(() => `rgb(${capColor.value.r},${capColor.value.g},${capColor.value.b})`)
const detectedCount = ref(0)   // pixel confidence

const saveColor = () => {
  localStorage.setItem('motion-swim-cap-color', JSON.stringify(capColor.value))
  localStorage.setItem('motion-swim-tolerance', String(tolerance.value))
}

// ── Camera ────────────────────────────────────────────────────────────────────
let stream = null
let animId = null
const cameraReady = ref(false)
const cameraError = ref(null)

const startCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } }
    })
    videoRef.value.srcObject = stream
    videoRef.value.onloadedmetadata = () => {
      videoRef.value.play()
      cameraReady.value = true
      loop()
    }
  } catch (e) {
    cameraError.value = 'Câmera indisponível: ' + e.message
  }
}

const stopCamera = () => {
  if (animId) cancelAnimationFrame(animId)
  stream?.getTracks().forEach(t => t.stop())
  animId = stream = null
  cameraReady.value = false
}

// ── Detection ─────────────────────────────────────────────────────────────────
const capPos = ref(null)   // { x, y } normalized 0-1
const smoothHistory = []
const SMOOTH_N = 8

function colorDist(r1, g1, b1, r2, g2, b2) {
  return Math.sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2)
}

function detectCap(imageData) {
  const { data, width, height } = imageData
  const { r: tr, g: tg, b: tb } = capColor.value
  const tol = tolerance.value
  let sx = 0, sy = 0, cnt = 0
  const step = 4
  for (let y = 0; y < height; y += step)
    for (let x = 0; x < width; x += step) {
      const i = (y * width + x) * 4
      if (colorDist(data[i], data[i+1], data[i+2], tr, tg, tb) < tol) {
        sx += x; sy += y; cnt++
      }
    }
  detectedCount.value = cnt
  if (cnt < 10) return null
  return { x: sx / cnt / width, y: sy / cnt / height }
}

function smoothX(raw) {
  smoothHistory.push(raw)
  if (smoothHistory.length > SMOOTH_N) smoothHistory.shift()
  return smoothHistory.reduce((a, b) => a + b, 0) / smoothHistory.length
}

// ── Calibration ───────────────────────────────────────────────────────────────
const wallA       = ref(0.10)   // normalized
const wallB       = ref(0.90)
const calibXs     = ref([])
const calibProgress = ref(0)
const autoCalibRunning = ref(false)
const calibDone   = ref(false)
const CALIB_FRAMES = 300

const startAutoCalib = () => {
  calibXs.value = []
  calibProgress.value = 0
  calibDone.value = false
  autoCalibRunning.value = true
}

function feedCalib(x) {
  if (!autoCalibRunning.value) return
  calibXs.value.push(x)
  calibProgress.value = Math.min(100, Math.round(calibXs.value.length / CALIB_FRAMES * 100))
  if (calibXs.value.length >= CALIB_FRAMES) {
    const sorted = [...calibXs.value].sort((a, b) => a - b)
    wallA.value = sorted[Math.floor(sorted.length * 0.05)]
    wallB.value = sorted[Math.floor(sorted.length * 0.95)]
    autoCalibRunning.value = false
    calibDone.value = true
  }
}

const confirmCalib = () => {
  phase.value = 'tracking'
  lastZone.value = null
  lapCount.value = 0
  totalDist.value = 0
}

// ── Lap counting ──────────────────────────────────────────────────────────────
const lapCount  = ref(0)
const totalDist = ref(0)
const lastZone  = ref(null)
const lapFlash  = ref(false)
const DEADBAND  = 0.15

function getZone(x) {
  const span = wallB.value - wallA.value
  if (x < wallA.value + span * DEADBAND) return 'A'
  if (x > wallB.value - span * DEADBAND) return 'B'
  return 'MID'
}

function checkLap(x) {
  const zone = getZone(x)
  if (zone === 'MID') return
  if (lastZone.value && lastZone.value !== zone) {
    lapCount.value++
    totalDist.value += props.laneLength
    emit('distance-updated', totalDist.value)
    emit('lap-completed', { lap: lapCount.value, distance: totalDist.value })
    lapFlash.value = true
    setTimeout(() => lapFlash.value = false, 700)
  }
  lastZone.value = zone
}

// ── Click to pick color ───────────────────────────────────────────────────────
const handleCanvasClick = (e) => {
  if (!isPickingColor.value || !cameraReady.value) return
  const pc = processCanvas.value
  const rect = displayCanvas.value.getBoundingClientRect()
  const sx = (e.clientX - rect.left) * (pc.width  / rect.width)
  const sy = (e.clientY - rect.top)  * (pc.height / rect.height)
  const ctx = pc.getContext('2d')
  ctx.drawImage(videoRef.value, 0, 0, pc.width, pc.height)
  const px = ctx.getImageData(Math.floor(sx), Math.floor(sy), 1, 1).data
  capColor.value = { r: px[0], g: px[1], b: px[2] }
  saveColor()
  isPickingColor.value = false
}

// ── Drawing ───────────────────────────────────────────────────────────────────
function drawOverlay(ctx, W, H) {
  // Cap circle
  if (capPos.value) {
    const cx = capPos.value.x * W
    const cy = capPos.value.y * H
    ctx.beginPath()
    ctx.arc(cx, cy, 22, 0, Math.PI * 2)
    ctx.strokeStyle = colorPreview.value
    ctx.lineWidth = 4
    ctx.stroke()
    ctx.beginPath()
    ctx.arc(cx, cy, 6, 0, Math.PI * 2)
    ctx.fillStyle = 'white'
    ctx.fill()
  }

  // Wall lines (calibration + tracking)
  if (phase.value !== 'setup') {
    const aX = wallA.value * W
    const bX = wallB.value * W
    ctx.setLineDash([10, 5])
    ctx.lineWidth = 3
    ;[aX, bX].forEach(x => {
      ctx.beginPath()
      ctx.strokeStyle = 'rgba(59,130,246,0.85)'
      ctx.moveTo(x, 0); ctx.lineTo(x, H)
      ctx.stroke()
    })
    ctx.setLineDash([])

    // Wall labels
    ctx.font = 'bold 14px sans-serif'
    ctx.fillStyle = '#60a5fa'
    ctx.fillText('A', aX + 6, 20)
    ctx.fillText('B', bX - 18, 20)
  }

  // Lap flash
  if (lapFlash.value) {
    ctx.fillStyle = 'rgba(59,130,246,0.25)'
    ctx.fillRect(0, 0, W, H)
    ctx.font = 'bold 64px sans-serif'
    ctx.fillStyle = 'white'
    ctx.textAlign = 'center'
    ctx.fillText('🔔 ' + lapCount.value, W / 2, H / 2)
    ctx.textAlign = 'left'
  }
}

// ── Main loop ─────────────────────────────────────────────────────────────────
function loop() {
  const video = videoRef.value
  const pc    = processCanvas.value
  const dc    = displayCanvas.value
  if (!video || !pc || !dc) { animId = requestAnimationFrame(loop); return }

  if (video.videoWidth && pc.width !== video.videoWidth) {
    pc.width = dc.width = video.videoWidth
    pc.height = dc.height = video.videoHeight
  }

  const W = pc.width, H = pc.height
  const pCtx = pc.getContext('2d')
  const dCtx = dc.getContext('2d')

  pCtx.drawImage(video, 0, 0, W, H)
  const imgData = pCtx.getImageData(0, 0, W, H)
  const detected = detectCap(imgData)

  if (detected) {
    capPos.value = detected
    const sx = smoothX(detected.x)
    if (phase.value === 'calibrating') feedCalib(sx)
    if (phase.value === 'tracking')    checkLap(sx)
  } else {
    capPos.value = null
  }

  dCtx.drawImage(video, 0, 0, W, H)
  drawOverlay(dCtx, W, H)

  animId = requestAnimationFrame(loop)
}

// ── Lane length local state ───────────────────────────────────────────────────
const localLaneLength = ref(props.laneLength)

// ── Lifecycle ─────────────────────────────────────────────────────────────────
onMounted(startCamera)
onUnmounted(stopCamera)
</script>

<template>
  <div class="swim-cam">

    <!-- Canvas display -->
    <div
      class="canvas-wrap"
      :class="{ 'is-picking': isPickingColor }"
      @click="handleCanvasClick"
    >
      <video ref="videoRef" class="hidden-video" playsinline muted />
      <canvas ref="processCanvas" class="hidden-video" />
      <canvas ref="displayCanvas" class="display-canvas" />
      <div v-if="!cameraReady && !cameraError" class="cam-placeholder">
        <div class="cam-spinner"></div>
        <p>Iniciando câmera…</p>
      </div>
      <div v-if="cameraError" class="cam-placeholder error">
        <span>⚠️</span>
        <p>{{ cameraError }}</p>
      </div>
      <div v-if="isPickingColor" class="pick-cursor-hint">👆 Clique na toca do nadador</div>
    </div>

    <!-- ── SETUP ── -->
    <div v-if="phase === 'setup'" class="panel">
      <h3>⚙️ Configurar Câmera</h3>

      <div class="color-row">
        <div class="color-swatch" :style="{ background: colorPreview }"></div>
        <div class="color-info">
          <p class="label-sm">Cor da Toca</p>
          <p class="conf-text">{{ detectedCount > 10 ? `✅ ${detectedCount} px detectados` : '⚠️ Aponte para a toca' }}</p>
        </div>
        <button class="btn-pick" :class="{ active: isPickingColor }" @click="isPickingColor = !isPickingColor">
          {{ isPickingColor ? '✕ Cancelar' : '🎯 Clicar na Toca' }}
        </button>
      </div>

      <div class="form-group">
        <label>Tolerância de cor: {{ tolerance }}</label>
        <input v-model="tolerance" type="range" min="20" max="120" @change="saveColor" />
      </div>

      <div class="form-group">
        <label>Distância da raia (m)</label>
        <div class="lane-btns">
          <button
            v-for="l in [25, 50]" :key="l"
            :class="['btn-lane', localLaneLength === l ? 'active' : '']"
            @click="localLaneLength = l"
          >{{ l }}m</button>
          <input v-model.number="localLaneLength" type="number" min="5" class="input-lane" />
        </div>
      </div>

      <button class="btn-primary blue-btn" @click="phase = 'calibrating'">
        Próximo: Calibrar Pista →
      </button>
    </div>

    <!-- ── CALIBRATION ── -->
    <div v-if="phase === 'calibrating'" class="panel">
      <h3>📐 Calibrar Pista</h3>

      <div v-if="!calibDone">
        <p class="hint-text">Ajuste as linhas A/B manualmente ou use a auto-detecção nadando uma ida e volta.</p>

        <div class="wall-sliders">
          <div class="form-group">
            <label>Parede A: {{ Math.round(wallA * 100) }}%</label>
            <input v-model.number="wallA" type="range" min="0" max="0.49" step="0.01" />
          </div>
          <div class="form-group">
            <label>Parede B: {{ Math.round(wallB * 100) }}%</label>
            <input v-model.number="wallB" type="range" min="0.51" max="1" step="0.01" />
          </div>
        </div>

        <div v-if="autoCalibRunning" class="calib-progress">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: calibProgress + '%' }"></div>
          </div>
          <p>Gravando posições: {{ calibProgress }}%</p>
        </div>

        <button v-if="!autoCalibRunning" class="btn-outline blue-outline" @click="startAutoCalib">
          🏊 Auto-detectar (nadar ida e volta)
        </button>

        <button class="btn-primary blue-btn" style="margin-top:1rem" @click="calibDone = true">
          Usar configuração atual →
        </button>
      </div>

      <div v-else class="calib-done">
        <p>✅ Pista calibrada: A={{ Math.round(wallA * 100) }}% / B={{ Math.round(wallB * 100) }}%</p>
        <p class="hint-text">Confirme as linhas azuis no vídeo e inicie o rastreamento.</p>
        <div class="calib-actions">
          <button class="btn-outline" @click="calibDone = false">← Ajustar</button>
          <button class="btn-primary blue-btn" @click="confirmCalib">🚀 Iniciar Rastreamento</button>
        </div>
      </div>
    </div>

    <!-- ── TRACKING ── -->
    <div v-if="phase === 'tracking'" class="panel tracking-panel">
      <div class="stat-row">
        <div class="stat-box">
          <div class="stat-value">{{ lapCount }}</div>
          <div class="stat-label">comprimentos</div>
        </div>
        <div class="stat-box blue">
          <div class="stat-value">{{ totalDist }}m</div>
          <div class="stat-label">distância</div>
        </div>
        <div class="stat-box" :class="detectedCount > 10 ? 'ok' : 'warn'">
          <div class="stat-value">{{ detectedCount > 10 ? '✅' : '⚠️' }}</div>
          <div class="stat-label">detecção</div>
        </div>
      </div>
      <button class="btn-outline close-btn" @click="emit('close')">✕ Fechar Câmera</button>
    </div>

  </div>
</template>

<style scoped>
.swim-cam {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 100%;
}

/* ── Canvas ── */
.canvas-wrap {
  position: relative;
  width: 100%;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: #000;
  min-height: 200px;
  cursor: default;
}
.canvas-wrap.is-picking { cursor: crosshair; }

.hidden-video { display: none; }
.display-canvas {
  width: 100%;
  height: auto;
  display: block;
  max-height: 300px;
  object-fit: contain;
}

.cam-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: var(--text-secondary);
  background: rgba(0,0,0,0.6);
}
.cam-placeholder.error { color: #ef4444; }

.cam-spinner {
  width: 36px; height: 36px;
  border: 3px solid rgba(255,255,255,0.2);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.pick-cursor-hint {
  position: absolute;
  bottom: 10px; left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 6px 16px;
  border-radius: 99px;
  font-size: 0.85rem;
  pointer-events: none;
}

/* ── Panel ── */
.panel {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.panel h3 { font-size: 1.05rem; margin: 0; }

/* ── Color row ── */
.color-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(0,0,0,0.2);
  padding: 1rem;
  border-radius: var(--radius-sm);
}
.color-swatch {
  width: 40px; height: 40px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.2);
  flex-shrink: 0;
}
.color-info { flex: 1; }
.label-sm { font-size: 0.78rem; color: var(--text-tertiary); margin-bottom: 2px; }
.conf-text { font-size: 0.85rem; color: var(--text-secondary); }

.btn-pick {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}
.btn-pick:hover, .btn-pick.active { background: rgba(59,130,246,0.15); border-color: #3b82f6; color: #60a5fa; }

/* ── Form ── */
.form-group { display: flex; flex-direction: column; gap: 0.4rem; }
label { font-size: 0.82rem; color: var(--text-secondary); }
input[type="range"] { accent-color: #3b82f6; }

.lane-btns { display: flex; gap: 0.5rem; align-items: center; }
.btn-lane {
  padding: 6px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}
.btn-lane.active { background: #3b82f6; border-color: #3b82f6; color: white; }
.input-lane {
  width: 70px;
  background: rgba(0,0,0,0.3);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  color: var(--text-primary);
  font-size: 0.9rem;
}

/* ── Buttons ── */
.blue-btn {
  background: #3b82f6;
  box-shadow: 0 4px 15px rgba(59,130,246,0.35);
}
.blue-btn:hover { box-shadow: 0 6px 20px rgba(59,130,246,0.55); }

.blue-outline {
  border-color: rgba(59,130,246,0.4);
  color: #60a5fa;
}
.blue-outline:hover { background: rgba(59,130,246,0.08); }

/* ── Calibration ── */
.wall-sliders { display: flex; flex-direction: column; gap: 0.8rem; }
.calib-progress { display: flex; flex-direction: column; gap: 0.4rem; }
.progress-track { height: 6px; background: rgba(255,255,255,0.1); border-radius: 99px; overflow: hidden; }
.progress-fill { height: 100%; background: #3b82f6; border-radius: 99px; transition: width 0.3s; }
.hint-text { font-size: 0.85rem; color: var(--text-tertiary); }
.calib-done { display: flex; flex-direction: column; gap: 0.8rem; }
.calib-actions { display: flex; gap: 0.8rem; }

/* ── Tracking stats ── */
.tracking-panel { gap: 1.2rem; }
.stat-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.8rem; }
.stat-box {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 1rem;
  text-align: center;
}
.stat-box.blue  { border-color: rgba(59,130,246,0.4); }
.stat-box.ok    { border-color: rgba(16,185,129,0.4); }
.stat-box.warn  { border-color: rgba(245,158,11,0.4); }
.stat-value { font-size: 1.5rem; font-weight: 800; font-family: var(--font-heading); }
.stat-label { font-size: 0.75rem; color: var(--text-tertiary); margin-top: 2px; }

.close-btn { align-self: flex-start; color: var(--text-tertiary); font-size: 0.85rem; padding: 6px 14px; }
</style>
