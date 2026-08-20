import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import router from './router'
import App from './App.vue'
import './style.css'

const app = createApp(App)

const pinia = createPinia()
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: true,
      refetchOnMount: 'always',
      staleTime: 0,
      retry: 1,
    },
  },
})

// Cross-tab real-time sync via BroadcastChannel
if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
  const syncChannel = new BroadcastChannel('salom_crm_sync')

  syncChannel.onmessage = (event) => {
    if (event.data?.type === 'SYNC_ALL') {
      queryClient.invalidateQueries()
    }
  }

  ;(window as any).__broadcastSync = () => {
    try {
      syncChannel.postMessage({ type: 'SYNC_ALL', timestamp: Date.now() })
    } catch {
      // ignore
    }
  }
}

app.use(pinia)
app.use(router)
app.use(VueQueryPlugin, { queryClient })

app.mount('#app')
