import { createRouter, createWebHistory } from "vue-router";
import generatedRoutes from "~pages";

export const router = createRouter({
  history: createWebHistory(),
  routes: generatedRoutes,
});
