let activeGuard = null

/** Register the active 易心 conversation guard while /psych is mounted. */
export function registerPsychExitGuard(guard) {
  activeGuard = guard
  return () => {
    if (activeGuard === guard) activeGuard = null
  }
}

export function getPsychExitGuard() {
  return activeGuard
}
