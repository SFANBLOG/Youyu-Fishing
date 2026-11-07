type Handler = (payload?: any) => void

const events = new Map<string, Set<Handler>>()

export const bus = {
  on(name: string, fn: Handler) {
    if (!events.has(name)) events.set(name, new Set())
    events.get(name)!.add(fn)
    return () => bus.off(name, fn)
  },
  off(name: string, fn: Handler) {
    events.get(name)?.delete(fn)
  },
  emit(name: string, payload?: any) {
    events.get(name)?.forEach((fn) => fn(payload))
  },
}

export const CART_CHANGED = 'cart-changed'
