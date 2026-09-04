-- =====================================================
-- 易生伴医疗急救对话训练系统 - 数据库初始化脚本
-- 数据库：MySQL 8.0 (MySQL Workbench 8.0 CE)
-- 执行方式：用 MySQL Workbench 打开此文件并执行
-- =====================================================

-- 1. 创建数据库
DROP DATABASE IF EXISTS yishengban;
CREATE DATABASE yishengban DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE yishengban;

-- =====================================================
-- 2. 用户表
-- =====================================================
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
  username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
  password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
  real_name VARCHAR(50) DEFAULT NULL COMMENT '真实姓名',
  student_id VARCHAR(20) DEFAULT NULL COMMENT '学号',
  school VARCHAR(100) DEFAULT '南京医科大学' COMMENT '学校',
  email VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
  phone VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  avatar_url VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX idx_username (username),
  INDEX idx_student_id (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- =====================================================
-- 3. 场景表
-- =====================================================
CREATE TABLE scenes (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '场景ID',
  title VARCHAR(100) NOT NULL COMMENT '场景标题',
  description TEXT COMMENT '场景描述',
  cover VARCHAR(255) DEFAULT NULL COMMENT '场景封面图URL',
  role VARCHAR(50) DEFAULT NULL COMMENT '角色信息',
  role_avatar VARCHAR(255) DEFAULT NULL COMMENT '角色头像URL',
  background TEXT COMMENT '场景背景',
  opening_message TEXT COMMENT '角色开场白',
  config JSON DEFAULT NULL COMMENT '场景配置JSON',
  difficulty INT DEFAULT 1 COMMENT '难度等级 1-5',
  is_active INT DEFAULT 1 COMMENT '是否启用 0/1',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='场景表';

-- =====================================================
-- 4. 对话会话表
-- =====================================================
CREATE TABLE chat_sessions (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '会话ID',
  user_id INT NOT NULL COMMENT '用户ID',
  scene_id INT NOT NULL COMMENT '场景ID',
  started_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  ended_at DATETIME DEFAULT NULL COMMENT '结束时间',
  is_rated INT DEFAULT 0 COMMENT '是否已评分 0/1',
  INDEX idx_user_id (user_id),
  INDEX idx_scene_id (scene_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话会话表';

-- =====================================================
-- 5. 对话消息表
-- =====================================================
CREATE TABLE chat_messages (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
  session_id INT NOT NULL COMMENT '会话ID',
  role VARCHAR(20) NOT NULL COMMENT '角色 system/user/ai/coach',
  content TEXT NOT NULL COMMENT '消息内容',
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
  extra JSON DEFAULT NULL COMMENT '额外信息（评分标注、教练提示）',
  INDEX idx_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话消息表';

-- =====================================================
-- 6. 评分结果表
-- =====================================================
CREATE TABLE results (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '评分ID',
  session_id INT NOT NULL UNIQUE COMMENT '会话ID',
  user_id INT NOT NULL COMMENT '用户ID',
  total_score INT DEFAULT NULL COMMENT '总分',
  accuracy INT DEFAULT NULL COMMENT '医学准确性',
  warmth INT DEFAULT NULL COMMENT '沟通温度',
  decision INT DEFAULT NULL COMMENT '决策合理性',
  details JSON DEFAULT NULL COMMENT '详细评分JSON',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX idx_session_id (session_id),
  INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评分结果表';

-- =====================================================
-- 7. 插入测试账号
-- =====================================================
-- 用户名：test
-- 密码：123456
-- 密码哈希（bcrypt $2b$12$）：123456 的真实哈希
-- 由 backend/app/auth.py 的 hash_password() 生成

INSERT INTO users (username, password_hash, real_name, student_id, school, email)
VALUES (
  'test',
  '$2b$12$LvNvORO79yYZQoI5TwNWb.K95eYJleaKp0QPpZokZKG5DdNwDx.LG',
  '测试用户',
  '20260001',
  '南京医科大学',
  'test@njmu.edu.cn'
);

-- =====================================================
-- 8. 插入示例场景
-- =====================================================
INSERT INTO scenes (title, description, role, background, opening_message, difficulty, is_active)
VALUES
(
  '异物梗阻急救',
  '面对突发异物梗阻患者，进行海姆立克急救法指导与情绪安抚',
  '成人患者',
  '一位 35 岁男性，在餐厅用餐时不慎被食物卡住气管，面色通红，无法说话，伴随咳嗽和呼吸困难。',
  '（患者捂喉咙，无法说话，表情痛苦，呼吸急促）',
  4,
  1
),
(
  '第一次独立看病',
  '模拟从挂号选科到问诊、取药和医保结算的完整首次就医流程',
  '医院流程角色',
  '用户扮演第一次独自就医的大学生，AI按阶段扮演医院APP、挂号员、医生、药师和收费员。',
  '你第一次需要独自去医院看病。请先选择线上预约、线下现场挂号或智能导诊。',
  2,
  1
),
(
  'OSCE模拟问诊与病历书写',
  '以问诊为核心，训练规范病史采集、临床归纳和独立病历书写',
  '标准化患者',
  '内科OSCE考站。学生扮演接诊医生，AI扮演标准化患者并快速提供必要检查结果。',
  '请以接诊医生身份开始问诊，并在结束前完成病历记录。',
  5,
  1
);

-- =====================================================
-- 9. 验证
-- =====================================================
SELECT '=== 数据库创建完成 ===' AS '状态';

SELECT '=== 用户表 ===' AS '表名';
SELECT id, username, real_name, student_id, school FROM users;

SELECT '=== 场景表 ===' AS '表名';
SELECT id, title, role, difficulty FROM scenes;
