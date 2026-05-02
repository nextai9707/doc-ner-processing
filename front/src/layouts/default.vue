<template>
	<el-container>
		<!-- 左侧菜单 -->
		<el-aside :width="isCollapse ? '64px' : '200px'" class="custom-aside">
			<div class="system-header">
				<div class="system-title" v-show="!isCollapse">
					<h2>文档处理系统</h2>
					<p class="system-subtitle">智能文档分析与处理平台</p>
				</div>
				<div class="collapse-icon" v-show="isCollapse">
					<el-icon><Document /></el-icon>
				</div>
				<div class="collapse-btn" @click="toggleCollapse">
					<el-icon>
						<component :is="isCollapse ? 'Expand' : 'Fold'" />
					</el-icon>
				</div>
			</div>
			<el-menu
				class="custom-menu"
				:default-active="activePath"
				:collapse="isCollapse"
				router
				@select="handleSelect"
			>
				<el-menu-item
					v-for="r in state.getList"
					:key="r.name"
					:index="r.path"
					class="custom-menu-item"
				>
					<component class="icons" :is="r.icon"/>
					<template #title>{{ r.name }}</template>
				</el-menu-item>
			</el-menu>
		</el-aside>

		<el-container>
			<!-- 顶部导航栏 -->
			<el-header class="top-header">
				<div class="header-left">
						<!-- 面包屑导航 -->
			<div class="breadcrumb-container">
				<el-breadcrumb separator="/">
					<el-breadcrumb-item
						v-for="(item, index) in breadcrumbItems"
						:key="index"
						:to="item.path"
					>
						<el-icon v-if="item.icon" style="margin-right: 4px">
							<component :is="item.icon" />
						</el-icon>
						{{ item.name }}
					</el-breadcrumb-item>
				</el-breadcrumb>
			</div>
				</div>
				<div class="header-right">
					<heads></heads>
				</div>
			</el-header>



			<!-- 主内容区 -->
			<el-main class="main-content">
				<router-view></router-view>
			</el-main>
		</el-container>
	</el-container>
</template>
<script setup lang="ts">
import {getAdminList} from '~/utils/utils'
import navStore from '~/stores/navStore'
import {reactive, computed, watch, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {Document} from '@element-plus/icons-vue'
import userStore from '~/stores/userStore'

const route = useRoute()
const router = useRouter()
const nav = navStore()
const isCollapse = ref(false)

// 先初始化 state
const state = reactive(<any>{
	getList: []
})

// 标签页管理
const tabs = ref<Array<{path: string, name: string, icon?: string}>>([
	{ path: '/', name: '首页', icon: 'House' }
])

// 获取菜单项信息
const getMenuItemByPath = (path: string) => {
    const allItems = [...state.getList]
    const user = userStore()
    if (user.userInfo.role == 0) {
        allItems.push(
            { path: '/user', name: '用户管理', icon: 'UserFilled' },
            { path: '/operation-log', name: '操作日志', icon: 'List' },
        )
    }
    return allItems.find(item => item.path === path)
}

// 添加标签页
const addTab = (path: string) => {
	if (!tabs.value.find(tab => tab.path === path)) {
		const menuItem = getMenuItemByPath(path)
		if (menuItem) {
			tabs.value.push({
				path: menuItem.path,
				name: menuItem.name,
				icon: menuItem.icon
			})
		}
	}
}

// 切换标签页
const switchTab = (path: string) => {
	router.push(path)
	nav.adminPath = path
}

// 关闭标签页
const closeTab = (path: string) => {
	if (tabs.value.length <= 1) return

	const index = tabs.value.findIndex(tab => tab.path === path)
	if (index > -1) {
		tabs.value.splice(index, 1)

		// 如果关闭的是当前激活的标签，切换到最后一个标签
		if (path === activePath.value) {
			const lastTab = tabs.value[tabs.value.length - 1]
			router.push(lastTab.path)
			nav.adminPath = lastTab.path
		}
	}
}

const handleSelect = (key: string, keyPath: string[]) => {
	nav.adminPath = key
	addTab(key)
}

const toggleCollapse = () => {
	isCollapse.value = !isCollapse.value
}

// 计算当前激活的路径
const activePath = computed(() => {
	return nav.adminPath || route.path
})

// 计算面包屑
const breadcrumbItems = computed(() => {
	const items: Array<{path: string, name: string, icon?: string}> = []
	const currentPath = activePath.value

	// 首页
	items.push({ path: '/', name: '首页', icon: 'House' })

	// 当前页面
	if (currentPath !== '/') {
		const menuItem = getMenuItemByPath(currentPath)
		if (menuItem) {
			items.push({
				path: menuItem.path,
				name: menuItem.name,
				icon: menuItem.icon
			})
		}
	}

	return items
})

onMounted(() => {
    state.getList = getAdminList()
    const user = userStore()
    if (user.userInfo.role == 0) {
        // 管理员才能看到的菜单
        state.getList.push(
            { path: '/user', name: '用户管理', icon: 'UserFilled' },
            { path: '/operation-log', name: '操作日志', icon: 'List' },
        )
    }
    if (route.path !== '/') {
        addTab(route.path)
    }
})

// 监听路由变化，更新选中的菜单和标签页（在 state 初始化后）
watch(() => route.path, (newPath) => {
	nav.adminPath = newPath
	// 确保 state 已初始化后再添加标签页
	if (state.getList.length > 0) {
		addTab(newPath)
	}
}, {immediate: true})

</script>

<style scoped>
/* 左侧菜单样式 */
.custom-aside {
	transition: width 0.3s;
	position: relative;
	overflow: hidden;
}

.system-header {
	background: linear-gradient(135deg, #3498db, #2980b9);
	border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	position: relative;
	min-height: 80px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.system-title {
	text-align: center;
	color: #fff;

}

.system-title h2 {
	margin: 0 0 8px 0;
	font-size: 18px;
	font-weight: 600;
	color: #fff;
	letter-spacing: 0.5px;
}

.system-subtitle {
	margin: 0;
	font-size: 12px;
	color: rgba(255, 255, 255, 0.9);
	letter-spacing: 0.3px;
}

.collapse-icon {
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24px;
	color: #fff;
}

.collapse-btn {
	position: absolute;
	top: 10px;
	right: 10px;
	cursor: pointer;
	padding: 5px;
	border-radius: 4px;
	background: rgba(255, 255, 255, 0.2);
	color: #fff;
	transition: all 0.3s;
	display: flex;
	align-items: center;
	justify-content: center;
	width: 28px;
	height: 28px;
}

.collapse-btn:hover {
	background: rgba(255, 255, 255, 0.3);
	transform: scale(1.1);
}

.custom-menu {
	border-right: none;
	transition: all 0.3s;
}

:deep(.el-menu--collapse) {
	width: 64px;
}

:deep(.el-menu--collapse .el-menu-item) {
	padding: 0 20px !important;
}

:deep(.el-menu--collapse .el-submenu__title) {
	padding: 0 20px !important;
}

/* 顶部导航栏 */
.top-header {
	height: 80px !important;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 20px;
}

.header-left {
	display: flex;
	align-items: center;
	gap: 15px;
}

.header-right {
	display: flex;
	align-items: center;
}
/* 主内容区 */
.main-content {
	height: 90vh;
	background: #f5f7fa;
	padding: 20px;
	overflow-y: auto;
}
</style>
