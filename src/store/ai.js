import { defineStore } from 'pinia'
import { markRaw } from 'vue'
import * as tf from '@tensorflow/tfjs-core'
import '@tensorflow/tfjs-backend-webgl'
import '@tensorflow/tfjs-backend-cpu'
import '@tensorflow/tfjs-converter'


export const useAIStore = defineStore('ai', {
  state: () => ({
    detector: null,
    isModelLoading: false,
    isModelReady: false
  }),
  actions: {
    async initModel() {
      if (this.detector || this.isModelLoading) return
      
      console.log('Iniciando carregamento do modelo MoveNet...')
      this.isModelLoading = true
      
      try {
        // Garantir que o TFJS está pronto
        await tf.ready()
        
        // Tentar definir WebGL, caso contrário cair no CPU de segurança
        try {
          await tf.setBackend('webgl')
          console.log('TFJS Backend definido com sucesso para: webgl')
        } catch (webglError) {
          console.warn('Falha ao iniciar WebGL, tentando CPU:', webglError)
          try {
            await tf.setBackend('cpu')
            console.log('TFJS Backend definido com sucesso para: cpu')
          } catch (cpuError) {
            console.error('Falha crítica ao iniciar CPU backend:', cpuError)
          }
        }
        
        console.log('TFJS Backend Ativo Final:', tf.getBackend())

        // Anexar no window ANTES de importar o UMD do pose-detection
        window.tf = tf

        const poseDetection = await import('@tensorflow-models/pose-detection/dist/pose-detection.js')
        
        if (poseDetection) {
          const model = poseDetection.SupportedModels.MoveNet
          const detectorConfig = { 
            modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING,
            enableSmoothing: true
          }
          const rawDetector = await poseDetection.createDetector(model, detectorConfig)
          this.detector = markRaw(rawDetector)
          this.isModelReady = true
          console.log('Modelo MoveNet carregado com sucesso.')
        } else {
          console.error("PoseDetection não foi importado corretamente.")
          alert("Falha local ao importar o PoseDetection.")
        }
        console.log('Modelo MoveNet carregado com sucesso.')
      } catch (e) {
        console.error('Erro ao carregar modelo de IA:', e)
        alert("Erro crítico ao carregar a IA: " + e.message)
      } finally {
        this.isModelLoading = false
      }
    }
  }
})
