import { createApp } from "vue";
import ui from "@nuxt/ui/vue-plugin";

import App from "./App.vue";
import { startWebsocketBus } from "./composables/websocketBus";
import { router } from "./router";
import "./style.css";

startWebsocketBus();

const app = createApp(App);
app.use(router);
app.use(ui);
app.mount("#app");
