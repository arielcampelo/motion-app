// Utility for audio feedback using SpeechSynthesis and Beeps
class AudioService {
  constructor() {
    this.synth = window.speechSynthesis
    this.enabled = true
  }

  speak(text) {
    if (!this.enabled || !this.synth) return
    
    // Cancel previous speech to avoid queueing up old messages
    this.synth.cancel()
    
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'pt-BR'
    utterance.rate = 1.1
    this.synth.speak(utterance)
  }

  beep(frequency = 440, duration = 200) {
    if (!this.enabled) return
    
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      const oscillator = audioCtx.createOscillator()
      const gainNode = audioCtx.createGain()

      oscillator.connect(gainNode)
      gainNode.connect(audioCtx.destination)

      oscillator.type = 'sine'
      oscillator.frequency.setValueAtTime(frequency, audioCtx.currentTime)
      
      gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + duration / 1000)

      oscillator.start()
      oscillator.stop(audioCtx.currentTime + duration / 1000)
    } catch (e) {
      console.warn('AudioContext not supported or blocked')
    }
  }

  playCountdown(seconds) {
    if (seconds > 0 && seconds <= 3) {
      this.beep(seconds === 1 ? 880 : 440, 150)
    }
  }

  playStart() {
    this.beep(1200, 400)
    this.speak('Começar!')
  }
}

export const audioService = new AudioService()
