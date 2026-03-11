import { onMounted, onUnmounted, ref } from "vue";

const MOBILE_MAX_WIDTH = 767;

export function useBreakpoint() {
  const isMobile = ref(typeof window !== "undefined" && window.innerWidth <= MOBILE_MAX_WIDTH);

  function update() {
    if (typeof window === "undefined") return;
    isMobile.value = window.innerWidth <= MOBILE_MAX_WIDTH;
  }

  let mql;
  onMounted(() => {
    update();
    mql = window.matchMedia(`(max-width: ${MOBILE_MAX_WIDTH}px)`);
    mql.addEventListener("change", update);
  });
  onUnmounted(() => {
    if (mql) mql.removeEventListener("change", update);
  });

  return { isMobile };
}
