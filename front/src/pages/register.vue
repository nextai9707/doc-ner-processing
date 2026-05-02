<template>
	<div class="crop-register-container">
		<div class="crop-register-card">
			<div class="crop-register-header">
				<h2 class="crop-title">文档处理系统</h2>
				<p class="crop-subtitle">智能文档分析与处理平台</p>
			</div>
			<div class="crop-form">
				<div class="crop-form-item">
					<label class="crop-label">用户名</label>
					<input
						class="crop-input"
						type="text"
						placeholder="请输入用户名"
						v-model="register.username"
					>
				</div>

				<div class="crop-form-item">
					<label class="crop-label">密码</label>
					<input
						class="crop-input"
						type="password"
						placeholder="至少8位字符，包含大小写字母和数字"
						v-model="register.password"
						@keyup.enter="onRegister"
					>
				</div>
				<div class="crop-form-item">
					<label class="crop-label">确认密码</label>
					<input
						class="crop-input"
						type="password"
						placeholder="请再次输入密码"
						v-model="register.confirmPassword"
						@keyup.enter="onRegister"
					>
				</div>

				<button class="crop-register-btn" @click="onRegister">
					<span v-if="!loading">注 册</span>
					<el-icon v-else class="is-loading"><Loading /></el-icon>
				</button>

				<div class="crop-agreement">
					<el-checkbox v-model="register.agreed">
						我已阅读并同意<a href="#" @click.prevent>《用户协议》</a>和<a href="#" @click.prevent>《隐私政策》</a>
					</el-checkbox>
				</div>

				<div class="crop-footer">
					<span @click="router.push('/login')">已有账号？立即登录</span>
				</div>
			</div>
		</div>

	</div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { adminRequest } from '~/composables/adminRequest'

const router = useRouter();
const loading = ref(false)

const register = reactive({
	username: '',
	email: '',
	password: '',
	confirmPassword: '',
	agreed: false
})

const validateForm = () => {
	if (!register.username) {
		ElMessage.error("请输入用户名")
		return false
	}


	if (!register.password) {
		ElMessage.error("请输入密码")
		return false
	}
	if (register.password.length < 5) {
		ElMessage.error("密码长度不能少于8位")
		return false
	}

	if (register.password !== register.confirmPassword) {
		ElMessage.error("两次输入的密码不一致")
		return false
	}
	if (!register.agreed) {
		ElMessage.error("请先同意用户协议和隐私政策")
		return false
	}
	return true
}

const onRegister = async () => {
	if (!validateForm()) return
	loading.value = true
	try {
		await adminRequest.post("/api/register", register)
		ElMessage.success("注册成功")
		router.push("/login")
	} catch (error) {
	} finally {
		loading.value = false
	}
}
</script>

<style scoped>
.crop-register-container {
	width: 100%;
	height: 100vh;
	background: linear-gradient(135deg, #f5f7fa, #e8edf3);
	display: flex;
	justify-content: center;
	align-items: center;
	position: relative;
}

.crop-register-card {
	width: 450px;
	background: #FFF;
	border-radius: 8px;
	box-shadow: 0 10px 30px rgba(0,0,0,0.2);
	padding: 40px;
	z-index: 1;
	animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
	from { opacity: 0; transform: translateY(20px); }
	to { opacity: 1; transform: translateY(0); }
}

.crop-register-header {
	text-align: center;
	margin-bottom: 32px;
}

.crop-title {
	font-size: 26px;
	color: #2c3e50;
	font-weight: 600;
	margin-bottom: 8px;
	letter-spacing: 0.5px;
}

.crop-subtitle {
	color: #7f8c8d;
	font-size: 14px;
	letter-spacing: 0.5px;
	margin-top: 4px;
}

.crop-form-item {
	margin-bottom: 20px;
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
	border-color: #3498db;
	box-shadow: 0 0 0 2px rgba(52,152,219,0.12);
	outline: none;
}

.crop-register-btn {
	width: 100%;
	height: 48px;
	background: #3498db;
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
	font-weight: 500;
}

.crop-register-btn:hover {
	background: #2980b9;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(52,152,219,0.3);
}

.crop-agreement {
	margin-top: 15px;
	font-size: 12px;
	color: #666;
}

.crop-agreement a {
	color: #3498db;
	margin: 0 3px;
	text-decoration: none;
}

.crop-agreement a:hover {
	text-decoration: underline;
}

.crop-footer {
	margin-top: 20px;
	text-align: center;
	font-size: 14px;
	color: #3498db;
	cursor: pointer;
}

.crop-footer span:hover {
	text-decoration: underline;
}

.crop-register-banner {
	position: absolute;
	right: 10%;
	color: white;
	max-width: 400px;
	animation: slideIn 0.8s ease;
}

@keyframes slideIn {
	from { opacity: 0; transform: translateX(50px); }
	to { opacity: 1; transform: translateX(0); }
}

.crop-register-banner h3 {
	font-size: 28px;
	margin-bottom: 15px;
	text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.crop-register-banner p {
	font-size: 16px;
	opacity: 0.9;
	margin-bottom: 20px;
	text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.crop-features {
	list-style: none;
	padding-left: 0;
}

.crop-features li {
	position: relative;
	padding-left: 25px;
	margin-bottom: 12px;
	font-size: 15px;
	display: flex;
	align-items: center;
}

.crop-features li i {
	margin-right: 8px;
	color: #ffcc00;
	font-size: 18px;
}

@media (max-width: 992px) {
	.crop-register-banner {
		display: none;
	}
	.crop-register-card {
		width: 90%;
		max-width: 450px;
	}
}
</style>

<route lang="json">
{
"meta": {
"layout": "notFound"
}
}
</route>
