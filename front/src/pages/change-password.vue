<template>
	<div class="crop-change-container">
		<div class="crop-change-card">
			<div class="crop-change-header">
				<h2 class="crop-title">修改密码</h2>
				<p class="crop-subtitle">验证账户并设置新密码</p>
			</div>
			<div class="crop-form">
				<div class="crop-form-item">
					<label class="crop-label">用户名</label>
					<input
						class="crop-input"
						type="text"
						placeholder="请输入用户名"
						v-model="form.username"
					>
				</div>
				<div class="crop-form-item">
					<label class="crop-label">原密码</label>
					<input
						class="crop-input"
						type="password"
						placeholder="请输入当前密码"
						v-model="form.old_password"
					>
				</div>
				<div class="crop-form-item">
					<label class="crop-label">新密码</label>
					<input
						class="crop-input"
						type="password"
						placeholder="至少8位，包含字母与数字"
						v-model="form.new_password"
						@keyup.enter="onSubmit"
					>
				</div>
				<button class="crop-change-btn" @click="onSubmit">
					<span v-if="!loading">提 交</span>
					<el-icon v-else class="is-loading"><Loading /></el-icon>
				</button>
				<div class="crop-footer">
					<span @click="router.push('/login')">返回登录</span>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { adminRequest } from '~/composables/adminRequest'

const router = useRouter()
const loading = ref(false)
const form = reactive({
	username: '',
	old_password: '',
	new_password: ''
})

const validate = () => {
	if (!form.username) {
		ElMessage.error('请输入用户名')
		return false
	}
	if (!form.old_password) {
		ElMessage.error('请输入原密码')
		return false
	}
	if (!form.new_password) {
		ElMessage.error('请输入新密码')
		return false
	}
	if (form.new_password.length < 8) {
		ElMessage.error('新密码长度不能少于8位')
		return false
	}
	return true
}

const onSubmit = async () => {
	if (!validate()) return
	loading.value = true
	try {
		await adminRequest.post('/change_password', form)
		ElMessage.success('密码修改成功，请使用新密码登录')
		router.push('/login')
	} catch (error: any) {

	} finally {
		loading.value = false
	}
}
</script>

<style scoped>
.crop-change-container {
	width: 100%;
	height: 100vh;
	background: linear-gradient(135deg, #e8f4f8, #d1e9f2);
	display: flex;
	justify-content: center;
	align-items: center;
}

.crop-change-card {
	width: 420px;
	background: #FFF;
	border-radius: 8px;
	box-shadow: 0 4px 30px rgba(0,0,0,0.2);
	padding: 40px 32px;
	z-index: 1;
}

.crop-change-header {
	text-align: center;
	margin-bottom: 32px;
}

.crop-title {
	font-size: 24px;
	color: #00A1D6;
	font-weight: 600;
	margin-bottom: 8px;
}

.crop-subtitle {
	color: #666;
	font-size: 14px;
	letter-spacing: 1px;
}

.crop-form-item {
	margin: 20px 0;
}

.crop-label {
	display: block;
	color: #333;
	font-size: 14px;
	margin-bottom: 8px;
	font-weight: 500;
}

.crop-input {
	width: 100%;
	height: 48px;
	border: 1px solid #e5e5e5;
	border-radius: 4px;
	padding: 0 16px;
	font-size: 14px;
	transition: all 0.3s;
}

.crop-input:focus {
	border-color: #00A1D6;
	box-shadow: 0 0 0 2px rgba(0,161,214,0.12);
}

.crop-change-btn {
	width: 100%;
	height: 48px;
	background: #00A1D6;
	color: #fff;
	font-size: 16px;
	border-radius: 4px;
	margin-top: 10px;
	transition: all 0.3s;
	border: none;
	cursor: pointer;
	display: flex;
	justify-content: center;
	align-items: center;
}

.crop-change-btn:hover {
	background: #0088b8;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0,161,214,0.3);
}

.crop-footer {
	margin-top: 20px;
	text-align: center;
	font-size: 14px;
	color: #00A1D6;
	cursor: pointer;
}

.crop-footer span:hover {
	text-decoration: underline;
}
</style>

<route lang="json">
{
"meta": {
"layout": "notFound"
}
}
</route>


