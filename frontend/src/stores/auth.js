import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: !!localStorage.getItem('token')
  }),

  actions: {
    login(username, password) {
      // 这里应该调用API进行登录
      return new Promise((resolve, reject) => {
        // 模拟API调用
        setTimeout(() => {
          if (username === 'admin' && password === 'admin123') {
            this.user = { username }
            this.token = 'fake-jwt-token'
            this.isAuthenticated = true
            localStorage.setItem('token', this.token)
            resolve({ success: true })
          } else {
            reject(new Error('用户名或密码错误'))
          }
        }, 500)
      })
    },

    logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
    }
  }
})