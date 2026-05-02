import { adminRequest } from '~/composables/adminRequest'

/**
 * 验证码
 * @param data
 */
export  function captchaAdmin(uid: Number) {
	return adminRequest.get("/captcha",{
		params:{uuid:uid}
	})
}
/**
 * 注册
 * @param data
 */
export  function registerAdmin(data: any) {
	return adminRequest.post("/api/register", data)
}

/**
 * 退出
 */
export  function logoutAdmin() {
	return adminRequest.post("/logout")
}


/**
 * 获取用户信息
 * @param userId
 */
export  function userInfoAdmin() {
	return adminRequest.get("/sys/user/info")
}
/**
 * 修改密码
 * @param userId
 */
export  function updatePasswordAdmin(data:any) {
	return adminRequest.put("/sys/user/password",data)
}
