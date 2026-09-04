# 数据库说明

## 数据库：MySQL 8.0（MySQL Workbench 8.0 CE）

### 快速开始

1. 打开 **MySQL Workbench 8.0 CE**
2. 连接你的本地 MySQL 服务
3. `File` → `Open SQL Script` → 选择 `init.sql`
4. 点击 ⚡ 执行按钮（Execute）
5. 数据库 `yishengban` 创建完成

### 表清单

| 表名 | 用途 | 已创建 |
|---|---|---|
| `users` | 用户表 | ✅ |
| `scenes` | 场景表 | ✅ |
| `chat_sessions` | 对话会话表 | ✅ |
| `chat_messages` | 对话消息表 | ✅ |
| `results` | 评分结果表 | ✅ |

### 测试账号

```
用户名：test
密码：123456
学校：南京医科大学
```

✅ **init.sql 里的密码哈希是真实的**（用 `bcrypt.hashpw("123456")` 生成），可以直接登录。

如果数据库已建好但 test 账号还是登不上，可能是早期版本的 init.sql（占位哈希）。请用以下 SQL 更新：

```sql
USE yishengban;
UPDATE users SET password_hash = '$2b$12$LvNvORO79yYZQoI5TwNWb.K95eYJleaKp0QPpZokZKG5DdNwDx.LG'
WHERE username = 'test';
```

### 验证

执行 `init.sql` 后，可以运行以下 SQL 验证：

```sql
USE yishengban;
SELECT * FROM users;
SELECT * FROM scenes;
```

应该看到：
- 1 个测试用户（test）
- 3 个示例场景（异物梗阻急救、第一次独立看病、OSCE 模拟问诊与病历书写）
