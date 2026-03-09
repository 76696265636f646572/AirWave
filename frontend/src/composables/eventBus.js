const listeners = new Map();

export function emitEventBus(eventName, payload = null) {
  const handlers = listeners.get(eventName);
  if (!handlers || handlers.size === 0) return;
  for (const handler of Array.from(handlers)) {
    try {
      handler(payload);
    } catch {
      // Keep the bus resilient even when one subscriber throws.
    }
  }
}

export function onEventBus(eventName, handler) {
  const handlers = listeners.get(eventName) ?? new Set();
  handlers.add(handler);
  listeners.set(eventName, handlers);
  return () => {
    const currentHandlers = listeners.get(eventName);
    if (!currentHandlers) return;
    currentHandlers.delete(handler);
    if (currentHandlers.size === 0) {
      listeners.delete(eventName);
    }
  };
}
