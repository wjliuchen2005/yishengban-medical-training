<template>
  <div class="register-view">
    <div class="register-container">
      <div class="register-header">
        <el-icon class="brand-icon"><FirstAidKit /></el-icon>
        <h1>注册账号</h1>
        <p>加入“易”生伴，开始医疗对话训练</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="onSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="3-20字符" :prefix-icon="User" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="6-20字符"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入真实姓名（可选）" />
        </el-form-item>

        <el-form-item label="学号" prop="student_id">
          <el-input v-model="form.student_id" placeholder="请输入学号（可选）" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>

        <el-button
          type="primary"
          :loading="loading"
          class="submit-btn"
          @click="onSubmit"
        >
          注 册
        </el-button>

        <div class="form-footer">
          <span>已有账号？</span>
          <router-link to="/login">立即登录</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { register as apiRegister } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  real_name: '',
  student_id: '',
  email: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度 3-20 字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度 6-20 字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ]
}

async function onSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    loading.value = true
    const { confirmPassword, ...registerData } = form
    const res = await apiRegister(registerData)
    // 注册成功后自动登录
    userStore.token = res.token
    userStore.user = res.user
    localStorage.setItem('yishengban_token', res.token)
    localStorage.setItem('yishengban_user', JSON.stringify(res.user))
    ElMessage.success('注册成功')
    router.push('/')
  } catch (err) {
    console.error('注册失败', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;

.register-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #E8F0FE 0%, #F5F7FA 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-lg;
}

.register-container {
  width: 100%;
  max-width: 500px;
  background: white;
  border-radius: $radius-xl;
  padding: $spacing-xl;
  box-shadow: 0 10px 40px rgba(44, 123, 229, 0.12);
}

.register-header {
  text-align: center;
  margin-bottom: $spacing-lg;

  .brand-icon {
    font-size: 50px;
    color: $primary;
    margin-bottom: $spacing-sm;
  }

  h1 {
    font-size: 28px;
    margin: 0 0 $spacing-xs;
    color: $text-primary;
  }

  p {
    color: $text-secondary;
    margin: 0;
  }
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: $fs-md;
  margin-top: $spacing;
}

.form-footer {
  text-align: center;
  margin-top: $spacing;
  color: $text-secondary;

  a {
    color: $primary;
    font-weight: 500;
    margin-left: $spacing-xs;
  }
}

@media (max-width: 640px) {
  .register-view {
    min-height: 100dvh;
    align-items: flex-start;
    padding: 0;
  }

  .register-container {
    min-height: 100dvh;
    max-width: none;
    padding: 24px 20px 32px;
    border-radius: 0;
  }

  .register-header {
    margin-bottom: 20px;

    .brand-icon { margin-bottom: 5px; font-size: 38px; }
    h1 { font-size: 25px; }
    p { font-size: 14px; }
  }
}
</style>
