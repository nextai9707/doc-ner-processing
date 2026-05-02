import { defineStore } from 'pinia'

export default defineStore('navStore', {
	state() {
		return {
			adminPath: "/",
			frontPath: "/front/",
		}
	},
	actions: {
		inc() {

		},
	},
	persist: true,
})
