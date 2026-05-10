import { defineStore } from 'pinia'

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
        // Garantir que o TFJS está pronto e usando WebGL
        if (window.tf) {
          await window.tf.ready()
          await window.tf.setBackend('webgl')
          console.log('TFJS Backend:', window.tf.getBackend())
        }

        if (window.poseDetection) {
          const model = window.poseDetection.SupportedModels.MoveNet
          const detectorConfig = { 
            modelType: window.poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING,
            enableSmoothing: true
          }
          this.detector = await window.poseDetection.createDetector(model, detectorConfig)
          this.isModelReady = true
          console.log('Modelo MoveNet carregado com sucesso.')
        }
      } catch (e) {
        console.error('Erro ao carregar modelo de IA:', e)
      } finally {
        this.isModelLoading = false
      }
    }
  }
})
