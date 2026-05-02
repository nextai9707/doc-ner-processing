<template>
	<div class="operation-log-container">
		<el-card shadow="never" class="main-card">
			<template #header>
				<div class="card-header">
					<span class="card-title">📋 操作日志</span>
					<span class="card-subtitle">记录用户的登录、操作等行为</span>
				</div>
			</template>

			<!-- 查询条件 -->
			<div class="filter-section">
				<el-form :inline="true" :model="queryForm">
					<el-form-item label="用户名">
						<el-input
							v-model="queryForm.username"
							placeholder="输入用户名"
							clearable
							@clear="handleQuery"
						/>
					</el-form-item>
					<el-form-item label="操作类型">
						<el-select
							v-model="queryForm.action"
							placeholder="选择操作类型"
							clearable
							style="width: 160px"
							@clear="handleQuery"
						>
							<el-option
								v-for="action in actionOptions"
								:key="action"
								:label="getActionLabel(action)"
								:value="action"
							/>
						</el-select>
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="handleQuery">
							<el-icon><Search /></el-icon>
							查询
						</el-button>
						<el-button @click="handleReset">
							<el-icon><Refresh /></el-icon>
							重置
						</el-button>
					</el-form-item>
				</el-form>
			</div>

			<!-- 日志表格 -->
			<div class="log-table-section">
				<el-table :data="logList" stripe border v-loading="loading" size="small">
					<el-table-column type="index" label="序号" width="60" align="center" />
					<el-table-column prop="username" label="用户名" width="120" align="center">
						<template #default="{ row }">
							<el-tag size="small" :type="row.username === 'admin' ? 'danger' : ''">
								{{ row.username }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="action" label="操作类型" width="120" align="center">
						<template #default="{ row }">
							<el-tag :type="getActionTagType(row.action)" size="small">
								{{ getActionLabel(row.action) }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="target_type" label="对象类型" width="100" align="center">
						<template #default="{ row }">
							{{ row.target_type || '-' }}
						</template>
					</el-table-column>
					<el-table-column prop="detail" label="详细描述" min-width="250">
						<template #default="{ row }">
							<div class="detail-text">{{ row.detail || '-' }}</div>
						</template>
					</el-table-column>
					<el-table-column prop="ip_address" label="IP地址" width="120" align="center" />
					<el-table-column prop="created_at" label="操作时间" width="170" align="center">
						<template #default="{ row }">
							{{ formatDateTime(row.created_at) }}
						</template>
					</el-table-column>
				</el-table>
			</div>

			<!-- 分页 -->
			<div class="pagination-section">
				<el-pagination
					background
					layout="total, sizes, prev, pager, next, jumper"
					:total="page.total"
					:page-sizes="[10, 20, 50, 100]"
					v-model:page-size="page.limit"
					v-model:current-page="page.page"
					@size-change="handleSizeChange"
					@current-change="handlePageChange"
				/>
			</div>
		</el-card>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { adminRequest } from '@/composables/adminRequest'

const loading = ref(false)
const logList = ref<any[]>([])
const actionOptions = ref<string[]>([])

const queryForm = reactive({
	username: '',
	action: ''
})

const page = reactive({
	page: 1,
	limit: 10,
	total: 0
})

const getActionLabel = (action: string): string => {
	const labelMap: Record<string, string> = {
		'login': '登录',
		'logout': '退出',
		'register': '注册',
		'change_password': '修改密码',
		'upload_document': '上传文档',
		'parse_document': '解析文档',
		'delete_document': '删除文档',
		'preprocess': '文本预处理',
		'keyword_summary': '关键词摘要',
		'extraction': '信息抽取',
		'batch_process': '批量处理',
		'export': '导出结果',
		'add_user': '新增用户',
		'update_user': '修改用户',
		'delete_user': '删除用户'
	}
	return labelMap[action] || action
}

const getActionTagType = (action: string): string => {
	const typeMap: Record<string, string> = {
		'login': 'success',
		'logout': 'info',
		'register': 'primary',
		'change_password': 'warning',
		'upload_document': 'primary',
		'parse_document': 'primary',
		'delete_document': 'danger',
		'preprocess': 'success',
		'keyword_summary': 'success',
		'extraction': 'success',
		'batch_process': 'success',
		'export': 'warning',
		'add_user': 'primary',
		'update_user': 'warning',
		'delete_user': 'danger'
	}
	return typeMap[action] || ''
}

const formatDateTime = (dateTime: string | null | undefined): string => {
	if (!dateTime) return '-'
	try {
		const date = new Date(dateTime)
		if (isNaN(date.getTime())) return dateTime
		return date.toLocaleString('zh-CN')
	} catch (e) {
		return dateTime
	}
}

const loadActionOptions = async () => {
	try {
		const res: any = await adminRequest.get('/api/operation-logs/actions')
		if (res?.data && Array.isArray(res.data)) {
			actionOptions.value = res.data
		}
	} catch (e) {
		console.log('获取操作类型失败')
	}
}

const loadLogs = async () => {
	loading.value = true
	try {
		const res: any = await adminRequest.get('/api/operation-logs', {
			params: {
				page: page.page,
				limit: page.limit,
				username: queryForm.username || undefined,
				action: queryForm.action || undefined
			}
		})
		if (res?.data?.list) {
			logList.value = res.data.list
			page.total = res.data.page?.total || 0
		} else {
			logList.value = []
			page.total = 0
		}
	} catch (e) {
		ElMessage.error('获取操作日志失败')
	} finally {
		loading.value = false
	}
}

const handleQuery = () => {
	page.page = 1
	loadLogs()
}

const handleReset = () => {
	queryForm.username = ''
	queryForm.action = ''
	page.page = 1
	loadLogs()
}

const handlePageChange = (val: number) => {
	page.page = val
	loadLogs()
}

const handleSizeChange = (val: number) => {
	page.limit = val
	page.page = 1
	loadLogs()
}

onMounted(() => {
	loadActionOptions()
	loadLogs()
})
</script>

<style scoped>
.operation-log-container {
	padding: 20px;
}

.main-card {
	border-radius: 8px;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.card-title {
	font-size: 18px;
	font-weight: 600;
	color: #2c3e50;
}

.card-subtitle {
	font-size: 14px;
	color: #7f8c8d;
}

.filter-section {
	margin-bottom: 20px;
	padding: 15px;
	background: #f8f9fa;
	border-radius: 8px;
}

.log-table-section {
	margin-bottom: 20px;
}

.detail-text {
	color: #606266;
	font-size: 13px;
	overflow: hidden;
	text-overflow: ellipsis;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
}

.pagination-section {
	display: flex;
	justify-content: flex-end;
}
</style>
