<template>
	<div class="document-import-container">
		<el-card class="main-card">
			<template #header>
				<div class="card-header">
					<span class="card-title">📄 文档导入与解析</span>
					<span class="card-subtitle">支持TXT、Word、PDF等格式</span>
				</div>
			</template>

			<!-- 文件上传区域 -->
			<el-upload
				class="upload-area"
				drag
				:action="uploadUrl"
				:headers="uploadHeaders"
				:on-success="handleUploadSuccess"
				:on-error="handleUploadError"
				:before-upload="beforeUpload"
				:file-list="fileList"
				multiple
				accept=".txt,.doc,.docx,.pdf"
			>
				<el-icon class="el-icon--upload"><upload-filled /></el-icon>
				<div class="el-upload__text">
					将文件拖到此处，或<em>点击上传</em>
				</div>
				<template #tip>
					<div class="el-upload__tip">
						支持上传 TXT、Word、PDF 格式文件，单个文件不超过 50MB
					</div>
				</template>
			</el-upload>

			<!-- 文档列表 -->
			<div class="document-list-section">
				<div class="section-header">
					<h3>已上传文档</h3>
					<el-button type="primary" @click="refreshList" :loading="loading">
						<el-icon><Refresh /></el-icon>
						刷新
					</el-button>
				</div>

				<el-table :data="documentList" v-loading="loading" stripe>
					<el-table-column prop="original_filename" label="文件名" min-width="200">
						<template #default="{ row }">
							<div class="file-name-cell">
								<el-icon class="file-icon">
									<Document v-if="row.file_type === 'pdf'" />
									<Document v-else-if="row.file_type === 'docx'" />
									<Document v-else />
								</el-icon>
								<span>{{ row.original_filename }}</span>
							</div>
						</template>
					</el-table-column>
					<el-table-column prop="file_type" label="类型" width="100">
						<template #default="{ row }">
							<el-tag :type="getFileTypeTag(row.file_type)">
								{{ row.file_type.toUpperCase() }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="file_size" label="大小" width="120">
						<template #default="{ row }">
							{{ formatFileSize(row.file_size) }}
						</template>
					</el-table-column>
					<el-table-column prop="status" label="状态" width="120">
						<template #default="{ row }">
							<el-tag :type="getStatusTag(row.status)">
								{{ getStatusText(row.status) }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column prop="created_at" label="上传时间" width="180">
						<template #default="{ row }">
							{{ formatTime(row.created_at) }}
						</template>
					</el-table-column>
					<el-table-column label="操作" width="200" fixed="right">
						<template #default="{ row }">
							<el-button
								type="primary"
								size="small"
								@click="parseDocument(row)"
								:disabled="row.status === 'parsed' || row.status === 'processed'"
								:loading="row.parsing"
							>
								解析
							</el-button>
							<el-button
								type="info"
								size="small"
								@click="viewContent(row)"
								:disabled="!row.content"
							>
								查看
							</el-button>
							<el-button
								type="danger"
								size="small"
								@click="deleteDocument(row)"
							>
								删除
							</el-button>
						</template>
					</el-table-column>
				</el-table>

				<!-- 分页 -->
				<div class="pagination-wrapper">
					<el-pagination
						v-model:current-page="pagination.page"
						v-model:page-size="pagination.limit"
						:total="pagination.total"
						:page-sizes="[10, 20, 50, 100]"
						layout="total, sizes, prev, pager, next, jumper"
						@size-change="handleSizeChange"
						@current-change="handlePageChange"
					/>
				</div>
			</div>
		</el-card>

		<!-- 内容查看对话框 -->
		<el-dialog v-model="contentDialogVisible" title="文档内容" width="80%">
			<div class="content-viewer">
				<pre>{{ currentContent }}</pre>
			</div>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Refresh, Document } from '@element-plus/icons-vue'
import { adminRequest } from '@/composables/adminRequest'
import userStore from '@/stores/userStore'

const user = userStore()
const loading = ref(false)
const fileList = ref<any[]>([])
const documentList = ref<any[]>([])
const contentDialogVisible = ref(false)
const currentContent = ref('')

const pagination = reactive({
	page: 1,
	limit: 10,
	total: 0
})

const uploadUrl = computed(() => {
	const baseURL = import.meta.env.VITE_ADMIN_API_BASE_URL || ''
	return `${baseURL}/api/document/upload`
})

const uploadHeaders = computed(() => {
	return {
		token: user.userInfo?.token || ''
	}
})

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
	if (!bytes) return '0 B'
	const k = 1024
	const sizes = ['B', 'KB', 'MB', 'GB']
	const i = Math.floor(Math.log(bytes) / Math.log(k))
	return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

// 格式化时间
const formatTime = (time: string): string => {
	if (!time) return ''
	const date = new Date(time)
	return date.toLocaleString('zh-CN')
}

// 获取文件类型标签
const getFileTypeTag = (type: string): string => {
	const typeMap: Record<string, string> = {
		'txt': 'info',
		'docx': 'success',
		'pdf': 'danger'
	}
	return typeMap[type] || ''
}

// 获取状态标签
const getStatusTag = (status: string): string => {
	const statusMap: Record<string, string> = {
		'uploaded': 'info',
		'parsed': 'success',
		'processed': 'success',
		'error': 'danger'
	}
	return statusMap[status] || ''
}

// 获取状态文本
const getStatusText = (status: string): string => {
	const statusMap: Record<string, string> = {
		'uploaded': '已上传',
		'parsed': '已解析',
		'processed': '已处理',
		'error': '处理失败'
	}
	return statusMap[status] || status
}

// 上传前验证
const beforeUpload = (file: File) => {
	const allowedTypes = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
	const isValidType = allowedTypes.includes(file.type) ||
		file.name.endsWith('.txt') ||
		file.name.endsWith('.docx') ||
		file.name.endsWith('.pdf')

	if (!isValidType) {
		ElMessage.error('只能上传 TXT、Word、PDF 格式的文件!')
		return false
	}

	const isLt50M = file.size / 1024 / 1024 < 50
	if (!isLt50M) {
		ElMessage.error('文件大小不能超过 50MB!')
		return false
	}

	return true
}

// 上传成功
const handleUploadSuccess = (response: any, file: File) => {
	if (response.code === 200) {
		ElMessage.success('文件上传成功!')
		refreshList()
	} else {
		ElMessage.error(response.message || '上传失败')
	}
}

// 上传失败
const handleUploadError = (error: any) => {
	ElMessage.error('文件上传失败，请重试')
}

// 解析文档
const parseDocument = async (row: any) => {
	try {
		row.parsing = true
		const res: any = await adminRequest.post(`/api/document/${row.id}/parse`)
			ElMessage.success('文档解析成功!')
			refreshList()
	} catch (e: any) {
		ElMessage.error(e?.message || '解析失败')
	} finally {
		row.parsing = false
	}
}

// 查看内容
const viewContent = async (row: any) => {
	try {
		const res: any = await adminRequest.get(`/api/document/${row.id}/content`)
		if (res?.data) {
			currentContent.value = res.data.content || ''
			contentDialogVisible.value = true
		}
	} catch (e) {
		ElMessage.error('获取内容失败')
	}
}

// 删除文档
const deleteDocument = async (row: any) => {
	try {
		await ElMessageBox.confirm('确定要删除这个文档吗?', '提示', {
			confirmButtonText: '确定',
			cancelButtonText: '取消',
			type: 'warning'
		})

		const res: any = await adminRequest.delete(`/api/document/${row.id}`)
		if (res?.code === 200) {
			ElMessage.success('删除成功!')
			refreshList()
		}
	} catch (e) {
		if (e !== 'cancel') {
			ElMessage.error('删除失败')
		}
	}
}

// 刷新列表
const refreshList = async () => {
	loading.value = true
	try {
		const res: any = await adminRequest.get(`/api/document/list?page=${pagination.page}&limit=${pagination.limit}`)
		if (res?.data) {
			documentList.value = res.data.list || []
			pagination.total = res.data.total || 0
		}
	} catch (e) {
		ElMessage.error('获取文档列表失败')
	} finally {
		loading.value = false
	}
}

// 分页处理
const handleSizeChange = (val: number) => {
	pagination.limit = val
	pagination.page = 1
	refreshList()
}

const handlePageChange = (val: number) => {
	pagination.page = val
	refreshList()
}

onMounted(() => {
	refreshList()
})
</script>

<style scoped>
.document-import-container {
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

.upload-area {
	margin-bottom: 30px;
}

:deep(.el-upload-dragger) {
	width: 100%;
	padding: 40px;
}

.file-name-cell {
	display: flex;
	align-items: center;
	gap: 8px;
}

.file-icon {
	font-size: 20px;
	color: #3498db;
}

.document-list-section {
	margin-top: 30px;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
}

.section-header h3 {
	margin: 0;
	color: #2c3e50;
	font-size: 16px;
}

.pagination-wrapper {
	margin-top: 20px;
	display: flex;
	justify-content: flex-end;
}

.content-viewer {
	max-height: 500px;
	overflow-y: auto;
	padding: 20px;
	background: #f5f5f5;
	border-radius: 4px;
}

.content-viewer pre {
	margin: 0;
	white-space: pre-wrap;
	word-wrap: break-word;
	font-family: 'Courier New', monospace;
	font-size: 14px;
	line-height: 1.6;
}
</style>

