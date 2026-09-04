<template>
  <div class="profile-view">
    <AppHeader />

    <div class="profile-container">
      <h1>个人中心</h1>

      <!-- 基本信息 -->
      <el-card class="profile-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <el-button v-if="!editingProfile" type="primary" text @click="startEditProfile">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <div v-else>
              <el-button @click="cancelEditProfile">取消</el-button>
              <el-button type="primary" @click="saveProfile" :loading="profileSaving">
                保存
              </el-button>
            </div>
          </div>
        </template>

        <div v-if="!editingProfile" class="info-display">
          <div class="info-item">
            <span class="label">用户名</span>
            <span class="value">{{ user?.username }}</span>
          </div>
          <div class="info-item">
            <span class="label">真实姓名</span>
            <span class="value">{{ user?.real_name || '未填写' }}</span>
          </div>
          <div class="info-item">
            <span class="label">学号</span>
            <span class="value">{{ user?.student_id || '未填写' }}</span>
          </div>
          <div class="info-item">
            <span class="label">学校</span>
            <span class="value">{{ user?.school || '未填写' }}</span>
          </div>
          <div class="info-item">
            <span class="label">邮箱</span>
            <span class="value">{{ user?.email || '未填写' }}</span>
          </div>
          <div class="info-item">
            <span class="label">手机号</span>
            <span class="value">{{ user?.phone || '未填写' }}</span>
          </div>
        </div>

        <el-form v-else :model="profileForm" label-width="100px">
          <el-form-item label="真实姓名">
            <el-input v-model="profileForm.real_name" />
          </el-form-item>
          <el-form-item label="学号">
            <el-input v-model="profileForm.student_id" />
          </el-form-item>
          <el-form-item label="学校">
            <el-input v-model="profileForm.school" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="profileForm.email" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="profileForm.phone" />
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 修改密码 -->
      <el-card class="profile-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>修改密码</span>
          </div>
        </template>

        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
          style="max-width: 400px"
        >
          <el-form-item label="原密码" prop="old_password">
            <el-input v-model="passwordForm.old_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="passwordForm.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirm_password">
            <el-input v-model="passwordForm.confirm_password" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              @click="changePassword"
              :loading="passwordSaving"
            >
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 退出登录 -->
      <div class="logout-section">
        <el-button type="danger" plain @click="onLogout">
          <el-icon><SwitchButton /></el-icon>
          退出登录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import { useUserStore } from '@/stores/user'
import { getUserProfile, updateUserProfile, changePassword as apiChangePassword } from '@/api/user'

const router = useRouter()
const userStore = useUserStore()
const user = ref(userStore.user)

// 基本信息编辑
const editingProfile = ref(false)
const profileSaving = ref(false)
const profileForm = reactive({})

function startEditProfile() {
  profileForm.real_name = user.value?.real_name || ''
  profileForm.student_id = user.value?.student_id || ''
  profileForm.school = user.value?.school || ''
  profileForm.email = user.value?.email || ''
  profileForm.phone = user.value?.phone || ''
  editingProfile.value = true
}

function cancelEditProfile() {
  editingProfile.value = false
}

async function saveProfile() {
  profileSaving.value = true
  try {
    const updated = await updateUserProfile(profileForm)
    user.value = updated
    userStore.user = updated
    localStorage.setItem('yishengban_user', JSON.stringify(updated))
    ElMessage.success('保存成功')
    editingProfile.value = false
  } catch (err) {
    console.error('保存失败', err)
  } finally {
    profileSaving.value = false
  }
}

// 密码修改
const passwordFormRef = ref(null)
const passwordSaving = ref(false)
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const validateConfirmNewPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '长度 6-20 字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmNewPassword, trigger: 'blur' }
  ]
}

async function changePassword() {
  if (!passwordFormRef.value) return
  try {
    await passwordFormRef.value.validate()
    passwordSaving.value = true
    await apiChangePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (err) {
    console.error('密码修改失败', err)
  } finally {
    passwordSaving.value = false
  }
}

async function onLogout() {
  try {
    await ElMessageBox.confirm('确定退出登录？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning'
    })
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}

onMounted(async () => {
  try {
    const fresh = await getUserProfile()
    user.value = fresh
    userStore.user = fresh
  } catch (err) {
    // 后端未就绪时使用本地数据
    console.warn('使用本地用户数据', err)
  }
})
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables.scss' as *;

.profile-view {
  min-height: 100vh;
  background: $bg;
}

.profile-container {
  max-width: 900px;
  margin: 0 auto;
  padding: $spacing-lg;

  h1 {
    font-size: 28px;
    margin: 0 0 $spacing;
    color: $text-primary;
  }
}

.profile-card {
  margin-bottom: $spacing-lg;
  border-radius: $radius-lg;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 500;
  }
}

.info-display {
  .info-item {
    display: flex;
    padding: $spacing-sm 0;
    border-bottom: 1px solid $border;

    &:last-child {
      border-bottom: none;
    }

    .label {
      width: 120px;
      color: $text-secondary;
    }

    .value {
      color: $text-primary;
      flex: 1;
    }
  }
}

.logout-section {
  text-align: center;
  margin-top: $spacing-xl;
}

@media (max-width: 640px) {
  .profile-container {
    padding: 22px 12px 40px;

    h1 { margin-bottom: 14px; font-size: 25px; }
  }

  .profile-card {
    margin-bottom: 14px;

    :deep(.el-card__header),
    :deep(.el-card__body) { padding: 15px; }

    .card-header > div { display: flex; gap: 8px; }
    .card-header :deep(.el-button + .el-button) { margin-left: 0; }
  }

  .info-display .info-item {
    display: grid;
    grid-template-columns: 82px minmax(0, 1fr);
    gap: 10px;

    .label { width: auto; }
    .value { min-width: 0; overflow-wrap: anywhere; }
  }

  :deep(.el-form-item) { display: block; }
  :deep(.el-form-item__label) { width: auto !important; height: auto; margin-bottom: 7px; justify-content: flex-start; line-height: 1.4; }
  :deep(.el-form-item__content) { margin-left: 0 !important; }
  .logout-section { margin-top: 20px; }
  .logout-section :deep(.el-button) { width: 100%; min-height: 42px; }
}
</style>
