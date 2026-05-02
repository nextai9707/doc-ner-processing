import { setupLayouts } from 'virtual:meta-layouts'
import { createRouter, createWebHashHistory } from 'vue-router'
import { routes as fileRoutes } from 'vue-router/auto-routes'
import { safeResolve } from '~/composables/path'
import { adminRequest } from '~/composables/adminRequest'
import userStore from '~/stores/userStore'
import { ElMessage } from 'element-plus'

declare module 'vue-router' {}

fileRoutes.flat(Infinity).forEach((route) => {
    route.path = safeResolve(route.path)
})

export const router = createRouter({
    history: createWebHashHistory(),
    routes: setupLayouts(fileRoutes),
})

// 仅管理员可访问的路径
const ADMIN_ONLY_PATHS = ['/user', '/operation-log']

router.beforeEach(async (to, from, next) => {
    const noAuthPaths = ['/login', '/register', '/change-password']
    if (noAuthPaths.includes(to.path)) {
        return next()
    }
    try {
        const res = await adminRequest.get('/sys/user/info')
        const store = userStore()
        store.userInfo = res.data
        // ⭐ 角色级拦截
        if (ADMIN_ONLY_PATHS.includes(to.path) && store.userInfo.role !== 0) {
            ElMessage.warning('权限不足，无法访问该页面')
            return next('/')
        }
        next()
    } catch (e) {
        next('/login')
    }
})

export default router
