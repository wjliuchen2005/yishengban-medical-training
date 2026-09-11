import { onBeforeUnmount, onMounted, ref } from 'vue'

// Match the CSS breakpoint, including rotation and desktop window resizing.
export function useMobileViewport() {
  // WeChat's embedded browser can report a 980px layout viewport on phones.
  // Use the same explicit breakpoint as CSS; do not depend on pointer/hover
  // capabilities, which vary between WeChat WebViews.
  const query = window.matchMedia('(max-width: 980px)')
  const isMobile = ref(query.matches)
  const update = () => { isMobile.value = query.matches }
  onMounted(() => query.addEventListener('change', update))
  onBeforeUnmount(() => query.removeEventListener('change', update))
  return isMobile
}
