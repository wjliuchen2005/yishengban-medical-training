<template>
  <div class="login-view">
    <div class="login-container">
      <div class="login-left">
        <div class="brand">
          <el-icon class="brand-icon"><FirstAidKit /></el-icon>
          <h1 class="brand-title">“易”生伴</h1>
          <p class="brand-subtitle">高校学生医疗急救对话训练系统</p>
        </div>
        <ul class="brand-features">
          <li>✓ 真实医疗场景对话模拟</li>
          <li>✓ AI 患者角色互动</li>
          <li>✓ 三维度专业评估反馈</li>
          <li>✓ 决策树可视化回放</li>
        </ul>
      </div>

      <div class="login-right">
        <div class="login-form-wrapper">
          <h2>欢迎回来</h2>
          <p class="form-subtitle">登录账号开始训练</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            @submit.prevent="onSubmit"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" />
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                @keyup.enter="onSubmit"
              />
            </el-form-item>

            <el-button
              type="primary"
              :loading="loading"
              class="submit-btn"
              @click="onSubmit"
            >
              登 录
            </el-button>

            <div class="form-footer">
              <span>还没有账号？</span>
              <router-link to="/register">立即注册</router-link>
            </div>

            <div class="test-account">
              <el-alert type="info" :closable="false" show-icon>
                <template #title>测试账号</template>
                用户名：test / 密码：123456
              </el-alert>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function onSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    loading.value = true
    await userStore.login({ username: form.username, password: form.password })
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (err) {
    console.error('登录失败', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;

.login-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #E8F0FE 0%, #F5F7FA 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing;
}

.login-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: 100%;
  max-width: 900px;
  background: white;
  border-radius: $radius-xl;
  overflow: hidden;
  box-shadow: 0 10px 40px rgba(44, 123, 229, 0.12);

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.login-left {
  background: linear-gradient(135deg, $primary 0%, $primary-dark 100%);
  color: white;
  padding: $spacing-xl;
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  .brand {
    text-align: center;

    .brand-icon {
      font-size: 60px;
      margin-bottom: $spacing;
    }

    .brand-title {
      font-size: 36px;
      margin: 0;
      font-weight: 700;
    }

    .brand-subtitle {
      margin: $spacing 0 0;
      font-size: $fs-md;
      opacity: 0.9;
    }
  }

  .brand-features {
    list-style: none;
    padding: 0;
    margin: $spacing-xl 0 0;

    li {
      padding: $spacing-sm 0;
      font-size: $fs-md;
      opacity: 0.95;
    }
  }
}

.login-right {
  padding: $spacing-xl;

  h2 {
    font-size: 28px;
    margin: 0 0 $spacing-sm;
    color: $text-primary;
  }

  .form-subtitle {
    color: $text-secondary;
    margin-bottom: $spacing-lg;
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

.test-account {
  margin-top: $spacing-lg;
}

@media (max-width: 768px) {
  .login-view {
    min-height: 100dvh;
    align-items: stretch;
    padding: 0;
  }

  .login-container {
    min-height: 100dvh;
    border-radius: 0;
  }

  .login-left {
    padding: 28px 20px 22px;

    .brand {
      .brand-icon { margin-bottom: 8px; font-size: 42px; }
      .brand-title { font-size: 29px; }
      .brand-subtitle { margin-top: 8px; font-size: 14px; }
    }

    .brand-features { display: none; }
  }

  .login-right {
    padding: 26px 20px 34px;

    h2 { font-size: 25px; }
    .form-subtitle { margin-bottom: 20px; }
  }
}
</style>
