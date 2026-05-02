<template>
	<el-row :gutter="20">
		<el-col :span="24">
			<el-card shadow="hover">
				<el-form :inline="true" :model="state.queryParams">
					<el-form-item label="用户账号">
						<el-input v-model="state.queryParams.username" placeholder="请输入账号" clearable @clear="handleReset" />
					</el-form-item>
					<el-form-item>
						<el-button type="primary" @click="handleQuery">
							<el-icon><Search /></el-icon> 查询
						</el-button>
						<el-button @click="handleReset">
							<el-icon><Refresh /></el-icon> 重置
						</el-button>
						<el-button type="success" @click="handleAdd">
							<el-icon><Plus /></el-icon> 新增
						</el-button>
					</el-form-item>
				</el-form>
			</el-card>
		</el-col>
	</el-row>

	<!-- 用户表格 -->
	<el-row style="margin-top: 20px">
		<el-col :span="24">
			<el-table :data="state.getList" style="width: 100%" border stripe>
				<el-table-column prop="id" label="用户编号" align="center" width="90" />
				<el-table-column prop="username" label="用户账号" align="center" min-width="120" />
				<el-table-column prop="role" label="角色" align="center" width="100">
					<template #default="scope">
						<el-tag :type="scope.row.role === 0 ? 'danger' : 'primary'">
							{{ scope.row.role === 0 ? '管理员' : '普通用户' }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="status" label="账号状态" align="center" width="100">
					<template #default="scope">
						<el-tag :type="scope.row.status === 1 ? 'success' : 'info'">
							{{ scope.row.status === 1 ? '正常' : '已禁用' }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="created_at" label="创建时间" align="center" width="170">
					<template #default="scope">
						{{ formatDateTime(scope.row.created_at) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" align="center" width="240" fixed="right">
					<template #default="scope">
						<el-button size="small" @click="handleEdit(scope.row)">
							<el-icon><Edit /></el-icon> 编辑
						</el-button>
						<el-button
							size="small"
							:type="scope.row.status === 1 ? 'warning' : 'success'"
							@click="handleToggleStatus(scope.row)"
						>
							{{ scope.row.status === 1 ? '禁用' : '启用' }}
						</el-button>
						<el-button size="small" type="danger" @click="handleDelete(scope.row)">
							<el-icon><Delete /></el-icon> 删除
						</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-col>
	</el-row>

	<!-- 分页 -->
	<el-row style="margin-top: 20px">
		<el-col :span="24" style="text-align: right">
			<el-pagination
				background
				layout="total, sizes, prev, pager, next, jumper"
				:total="state.page.total"
				:page-sizes="[10, 20, 50]"
				v-model:page-size="state.page.limit"
				v-model:current-page="state.page.page"
				@size-change="handleSizeChange"
				@current-change="handlePageChange"
			/>
		</el-col>
	</el-row>

	<!-- 新增/编辑对话框 -->
	<el-dialog :title="state.dialog.title" v-model="state.dialog.visible" width="500px">
		<el-form :model="state.form" :rules="rules" ref="formRef" label-width="80px">
			<el-form-item label="用户账号" prop="username">
				<el-input v-model="state.form.username" placeholder="请输入账号" :disabled="!state.dialog.isAdd" />
			</el-form-item>
			<el-form-item label="密码" prop="password" v-if="state.dialog.isAdd">
				<el-input v-model="state.form.password" placeholder="请输入密码" show-password />
			</el-form-item>
			<el-form-item label="角色" prop="role">
				<el-select v-model="state.form.role" placeholder="请选择角色">
					<el-option label="管理员" :value="0" />
					<el-option label="普通用户" :value="1" />
				</el-select>
			</el-form-item>
			<el-form-item label="账号状态" prop="status">
				<el-radio-group v-model="state.form.status">
					<el-radio :label="1">正常</el-radio>
					<el-radio :label="0">禁用</el-radio>
				</el-radio-group>
			</el-form-item>
		</el-form>
		<template #footer>
			<el-button @click="state.dialog.visible = false">取消</el-button>
			<el-button type="primary" @click="submitForm">确定</el-button>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { adminRequest } from '@/composables/adminRequest'

interface User {
	id?: number
	username: string
	role: number
	status: number
	password?: string
	created_at?: string
}

const formRef = ref<FormInstance>()
const state = reactive({
	getList: [] as User[],
	page: {
		page: 1,
		limit: 10,
		total: 0
	},
	queryParams: {
		username: ''
	},
	form: {
		id: undefined,
		username: '',
		role: 1,
		status: 1,
		password: ''
	} as User,
	dialog: {
		visible: false,
		title: '',
		isAdd: false
	}
})

const rules = reactive<FormRules>({
	username: [{ required: true, message: '请输入用户账号', trigger: 'blur' }],
	role: [{ required: true, message: '请选择角色', trigger: 'change' }],
	password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
})

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

function init() {
	adminRequest.get("/api/users/page", {
		params: {
			page: state.page.page,
			limit: state.page.limit,
			username: state.queryParams.username
		}
	}).then((res: any) => {
		state.getList = res.data.list
		state.page = res.data.page
	})
}

function handleQuery() {
	state.page.page = 1
	init()
}

function handleReset() {
	state.queryParams.username = ''
	handleQuery()
}

function handlePageChange(page: number) {
	state.page.page = page
	init()
}

function handleSizeChange(limit: number) {
	state.page.limit = limit
	state.page.page = 1
	init()
}

function handleAdd() {
	state.dialog = {
		visible: true,
		title: '新增用户',
		isAdd: true
	}
	state.form = {
		username: '',
		role: 1,
		status: 1,
		password: ''
	}
}

function handleEdit(row: User) {
	state.dialog = {
		visible: true,
		title: '编辑用户',
		isAdd: false
	}
	state.form = JSON.parse(JSON.stringify(row))
}

function handleToggleStatus(row: User) {
	const newStatus = row.status === 1 ? 0 : 1
	const actionText = newStatus === 1 ? '启用' : '禁用'
	ElMessageBox.confirm(`确认${actionText}用户【${row.username}】吗？`, '提示', {
		type: 'warning'
	}).then(() => {
		adminRequest.put(`/api/users/${row.id}`, { status: newStatus }).then(() => {
			ElMessage.success(`${actionText}成功`)
			init()
		})
	}).catch(() => {})
}

function handleDelete(row: User) {
	ElMessageBox.confirm(`确认删除用户【${row.username}】吗？`, '提示', {
		type: 'warning'
	}).then(() => {
		adminRequest.delete(`/api/users/${row.id}`).then(() => {
			ElMessage.success('删除成功')
			init()
		})
	}).catch(() => {})
}

function submitForm() {
	formRef.value?.validate((valid) => {
		if (valid) {
			const url = state.dialog.isAdd ? '/api/users' : `/api/users/${state.form.id}`
			const method = state.dialog.isAdd ? 'post' : 'put'
			adminRequest[method](url, state.form).then(() => {
				ElMessage.success(state.dialog.isAdd ? '新增成功' : '修改成功')
				state.dialog.visible = false
				init()
			})
		}
	})
}

onMounted(() => {
	init()
})
</script>

<style scoped>
.el-form--inline .el-form-item {
	margin-right: 10px;
}
</style>
