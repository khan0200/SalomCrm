import type { Directive } from 'vue'

/**
 * v-reveal: a lightweight fade + slight rise, triggered once the element
 * scrolls into view (or immediately if it's already visible on mount - which
 * is what makes above-the-fold content feel like it "arrives" on page load
 * without a separate mechanism). Pure inline-style + CSS transition, so it
 * never fights with the element's existing Tailwind classes.
 *
 * Usage: `v-reveal` (no stagger) or `v-reveal="idx * 40"` (ms delay, e.g. for
 * staggering a v-for list) - kept deliberately short/capped by callers so a
 * long list doesn't turn into a slow cascade.
 */
export const vReveal: Directive<HTMLElement, number | void> = {
  mounted(el, binding) {
    const delay = typeof binding.value === 'number' ? Math.max(0, binding.value) : 0

    el.style.opacity = '0'
    el.style.transform = 'translateY(8px)'
    el.style.transition = `opacity 0.35s ease ${delay}ms, transform 0.35s ease ${delay}ms`
    el.style.willChange = 'opacity, transform'

    const reveal = () => {
      el.style.opacity = '1'
      el.style.transform = 'translateY(0)'
    }

    if (typeof IntersectionObserver === 'undefined') {
      reveal()
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            reveal()
            observer.unobserve(el)
          }
        }
      },
      { threshold: 0.08, rootMargin: '0px 0px -32px 0px' }
    )
    observer.observe(el)
    ;(el as any).__revealObserver = observer
  },
  unmounted(el) {
    const observer: IntersectionObserver | undefined = (el as any).__revealObserver
    observer?.disconnect()
  },
}
