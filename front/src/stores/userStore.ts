import { defineStore } from 'pinia'

export default defineStore('userStore', {
	state() {
		return {
			isLogin: false,
			userInfo:{},
		}
	},
	actions: {
		inc() {

		},
	},
	persist: true,
})
