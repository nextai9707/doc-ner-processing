<template>
	<div class="crop-login-container">
		<div class="crop-login-card">
			<div class="crop-login-header">
				<h2 class="crop-title">文档处理系统</h2>
				<p class="crop-subtitle">智能文档分析与处理平台</p>
			</div>
			<div class="crop-form">
				<div class="crop-form-item">
					<label class="crop-label">账号</label>
					<input
						class="crop-input"
						type="text"
						placeholder="请输入账号或注册邮箱"
						v-model="login.username"
					>
				</div>
				<div class="crop-form-item">
					<label class="crop-label">密码</label>
					<input
						class="crop-input"
						type="password"
						placeholder="请输入密码"
						v-model="login.password"
					>
				</div>
				<button class="crop-login-btn" @click="onLogin">登 录</button>
				<div class="crop-footer">
					<span @click="router.push('/register')">新用户注册</span>
					<span @click="router.push('/change-password')">忘记密码</span>
				</div>
			</div>
		</div>

	</div>
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router'
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { adminRequest } from '~/composables/adminRequest'
import userStore from '~/stores/userStore'

const router = useRouter()
const login = reactive({
	username: '',
	password: ''
})
const onLogin = () => {
	adminRequest.post("/api/login", login).then(res =>	{
		const  user = userStore()
		user.userInfo = res.data
		user.isLogin = true
		ElMessage.success("登录成功")
		router.push('/')
	})
}
</script>

<style scoped>
.crop-login-container {
	width: 100%;
	height: 100vh;
	background: linear-gradient(135deg, #f5f7fa, #e8edf3);
	display: flex;
	justify-content: center;
	align-items: center;
}

.crop-login-card {
	width: 420px;
	background: #FFF;
	border-radius: 8px;
	box-shadow: 0 4px 30px rgba(0,0,0,0.2);
	padding: 40px 32px;
	z-index: 1;
}

.crop-login-header {
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
	border-color: #3498db;
	box-shadow: 0 0 0 2px rgba(52,152,219,0.12);
	outline: none;
}

.crop-login-btn {
	width: 100%;
	height: 48px;
	background: #3498db;
	color: #fff;
	font-size: 16px;
	border-radius: 4px;
	margin-top: 24px;
	transition: all 0.3s;
	border: none;
	cursor: pointer;
	font-weight: 500;
}

.crop-login-btn:hover {
	background: #2980b9;
	transform: translateY(-1px);
	box-shadow: 0 4px 12px rgba(52,152,219,0.3);
}

.crop-footer {
	margin-top: 20px;
	display: flex;
	justify-content: space-between;
	font-size: 13px;
	color: #3498db;
	cursor: pointer;
}

.crop-footer span:hover {
	text-decoration: underline;
}

.crop-login-banner {
	position: absolute;
	right: 10%;
	color: white;
	max-width: 400px;
}

.crop-login-banner h3 {
	font-size: 28px;
	margin-bottom: 15px;
}

.crop-login-banner p {
	font-size: 16px;
	opacity: 0.9;
}

.crop-banner-features {
	margin-top: 30px;
}
.crop-banner-features p {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 12px 0;
	font-size: 15px;
}
</style>

<route lang="json">
{
"meta": {
"layout": "notFound"
}
}
</route>
