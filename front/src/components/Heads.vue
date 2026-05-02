<template>
	<div class="head">


		<el-dropdown>
			<div class="head_r">
				<!--				<img :src="userStore().adminUserInfo.avatar" alt="头像" class="profile" />-->
				<div class="head_user">
					<div class="head_user_name">{{ userStore().userInfo.username }}</div>
					<div class="head_user_desc"> {{ userStore().userInfo.role === 0 ? '管理员' : '普通用户' }}</div>
				</div>
			</div>
			<template #dropdown>
				<el-dropdown-menu slot="dropdown">
					<el-dropdown-item @click="drawer = true">个人中心</el-dropdown-item>
					<el-dropdown-item @click="logout">退出登录</el-dropdown-item>
				</el-dropdown-menu>
			</template>
		</el-dropdown>
		<el-drawer
			v-model="drawer"
			title="个人中心"
		>
			<el-form
				ref="formRef"
				:model="state.form"
				label-position="top"
			>
				<el-form-item
					prop="old_password"
					label="原始密码"
					:rules="[
        {
          required: true,
          message: '原始密码不能为空',
          trigger: 'blur',
        },
      ]"
				>
					<el-input v-model="state.form.old_password" />
				</el-form-item>
				<el-form-item
					prop="new_password"
					label="新密码"
					:rules="[
        {
          required: true,
          message: '新密码不能为空',
          trigger: 'blur',
        },
      ]"
				>
					<el-input v-model="state.form.new_password" />
				</el-form-item>
				<el-form-item>

					<el-button type="primary" @click="submitForm(formRef)">确定修改</el-button>
				</el-form-item>
			</el-form>
		</el-drawer>
	</div>
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { FormInstance } from 'element-plus'

const formRef = ref<FormInstance>()
import { adminRequest } from '~/composables/adminRequest'

const router = useRouter()
const drawer = ref(false)
const state = reactive(<any>{
	form: {}
})

/**
 * 退出登录
 */
const logout = async () => {
	try {
		await adminRequest.post('/api/logout')
		ElMessage.success('退出成功~')
		// 清除用户信息
		const store = userStore()
		store.userInfo = {}
		// 跳转到登录页
		router.push('/login')
	} catch (error) {
		// 即使接口调用失败，也清除本地状态并跳转
		ElMessage.warning('退出登录失败，已清除本地登录状态')
		const store = userStore()
		store.userInfo = {}
		router.push('/login')
	}
}

/**
 * 修改密码
 * @param formEl
 */
const submitForm = (formEl: FormInstance | undefined) => {
	if (!formEl) return
	formEl.validate((valid) => {
		if (valid) {
			if (state.form.old_password !== state.form.new_password) {
				ElMessage.error('两次密码输入不一致')
				return
			}
			state.form.username = userStore().userInfo.username
			adminRequest.post('/change_password', state.form).then(async () => {
				ElMessage.success('修改成功')
				// 修改密码后，调用退出登录接口
				try {
					await adminRequest.post('/api/logout')
				} catch (error) {
					// 忽略退出接口错误，继续执行
				}
				// 清除用户信息
				const store = userStore()
				store.userInfo = {}
				// 跳转到登录页
				router.push('/login')
			})
		}
	})
}


</script>
<style scoped>
.head_user_name {
	font-size: 16px;
	font-weight: 700;
	color: black;
}
.head {
	width: 100%;
	height: 80px;
	display: flex;
	align-items: center;
	justify-content: space-between;

	.head_l img {
		width: 25px;
		height: 25px;
		cursor: pointer;
	}

	.head_r {
		display: flex;
		align-items: center;
		margin-right: 30px;

		.head_user {
			.head_user_desc {
				color: var(--theme-header-user-desc-color);
				font-size: 10px;
				text-align: center;
			}
		}
	}
}
</style>
