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
      // Freshness-aware mount/focus refetching: with staleTime > 0, a cache
      // entry younger than its staleTime renders immediately with no
      // network call on mount or window focus; once it's past staleTime,
      // the next mount/focus/reconnect triggers a background refetch.
      // Previously `refetchOnMount: 'always'` + `staleTime: 0` forced every
      // page navigation (Status/Students/Documents, which all load the
      // same ~5000-row roster) to redownload it regardless of freshness -
      // over a long-haul connection that cost was paid on every navigation.
      refetchOnWindowFocus: true,
      refetchOnMount: true,
      refetchOnReconnect: true,
      staleTime: 5 * 60 * 1000,
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
