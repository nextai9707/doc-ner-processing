import axios from 'axios'
import userStore from '~/stores/userStore'
import router from '~/plugins/router'
export const adminRequest = axios.create({
	baseURL: import.meta.env.VITE_ADMIN_API_BASE_URL
})
// 添加请求拦截器
adminRequest.interceptors.request.use(
	function(config) {
		// 在发送请求之前做些什么
    try {
        const store = userStore()
        const token = (store as any)?.userInfo?.token
        if (token) {
            config.headers = config.headers || {}
            ;(config.headers as any).token = token
        }
    } catch (e) {
        // ignore
    }
		return config
	},
	function(error) {
		toast.warning(error.message ?? '未知请求错误')
		// 对请求错误做些什么
		return Promise.reject(error)
	}
)
// 添加响应拦截器
adminRequest.interceptors.response.use(
	function(response) {
		// 如果是blob响应，直接返回response.data
		if (response.config.responseType === 'blob') {
			return response.data
		}
		const code = response.data.code
		switch (Number(code)) {
			case 500:
				ElMessage.error(response.data.msg)
				return Promise.reject(response.data.msg)
			default:
				return response.data
		}
		return response.data
	},
	function(error) {
		let code = error.response?.data.code
		let msg = error.response?.data.msg
		console.log(error.response)
		switch (Number(code)) {
			case 500:
				ElMessage.error(msg)
				return Promise.reject(msg)
			case 401:
				ElMessage.error(msg)
				router.push('/login')
				return Promise.reject(msg)
			default:
				return Promise.reject(error)
		}
	}
)
