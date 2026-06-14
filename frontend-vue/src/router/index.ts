import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '@/layout/AppShell.vue'
import { isAuthenticated } from '@/lib/auth'

// Pages are lazy-loaded so each route becomes its own chunk. This keeps heavy
// dependencies (e.g. ECharts) OUT of the initial bundle — first paint only
// downloads the shell + the page actually being visited.
const HomePage = () => import('@/pages/Home.vue')
const LoginPage = () => import('@/pages/Login.vue')
const ChatPage = () => import('@/pages/Chat.vue')
const FutureWorkPage = () => import('@/pages/FutureWork.vue')
const AboutPage = () => import('@/pages/About.vue')
const SettingsPage = () => import('@/pages/Settings.vue')

const router = createRouter({
  history: createWebHistory(),
  // Landing page scrolls; app pages manage their own scroll containers.
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
  routes: [
    { path: '/', component: HomePage },
    { path: '/login', component: LoginPage, meta: { guestOnly: true } },
    // Public "how it works" page — crawlable, no sign-in required.
    { path: '/about', component: AboutPage },
    {
      path: '/app',
      component: AppShell,
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: 'chat' },
        { path: 'chat', component: ChatPage },
        { path: 'future-work', component: FutureWorkPage },
        { path: 'about', component: AboutPage },
        { path: 'settings', component: SettingsPage },
      ],
    },
  ],
})

// Auth guard: the public marketing site (/ and /login) is open so search
// engines can crawl and index it; only the app (/app/*) requires a signed-in
// account. Anonymous visitors hitting the app are sent to /login with a
// redirect-back; signed-in users skip the login page.
router.beforeEach((to) => {
  const authed = isAuthenticated()
  if (to.meta.guestOnly && authed) {
    return { path: '/app/chat' }
  }
  if (to.matched.some((r) => r.meta.requiresAuth) && !authed) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
