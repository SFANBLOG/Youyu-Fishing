import { reactive } from 'vue'
import { api } from '../api'
import { bus, CART_CHANGED } from '../utils/eventBus'

export const cartState = reactive({ count: 0 })

export async function refreshCart() {
  if (!localStorage.getItem('yy_token')) {
    cartState.count = 0
    return
  }
  try {
    const res: any = await api.cart()
    cartState.count = res.data?.count || 0
  } catch {
    cartState.count = 0
  }
}

bus.on(CART_CHANGED, () => refreshCart())
