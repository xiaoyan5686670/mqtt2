<template>
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-md-6">
        <div class="card mt-5">
          <div class="card-header">
            <h3 class="text-center">登录</h3>
          </div>
          <div class="card-body">
            <form @submit.prevent="handleLogin">
              <div class="mb-3">
                <label for="username" class="form-label">用户名</label>
                <input
                  type="text"
                  class="form-control"
                  id="username"
                  v-model="username"
                  required
                />
              </div>
              <div class="mb-3">
                <label for="password" class="form-label">密码</label>
                <input
                  type="password"
                  class="form-control"
                  id="password"
                  v-model="password"
                  required
                />
              </div>
              <div class="d-grid">
                <button type="submit" class="btn btn-primary">登录</button>
              </div>
            </form>
            <div v-if="error" class="alert alert-danger mt-3">
              {{ error }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

export default {
  name: 'Login',
  setup() {
    const username = ref('')
    const password = ref('')
    const error = ref('')
    const authStore = useAuthStore()
    const router = useRouter()

    const handleLogin = async () => {
      error.value = ''
      try {
        await authStore.login(username.value, password.value)
        router.push('/dashboard')
      } catch (err) {
        error.value = err.message
      }
    }

    return {
      username,
      password,
      error,
      handleLogin
    }
  }
}
</script>