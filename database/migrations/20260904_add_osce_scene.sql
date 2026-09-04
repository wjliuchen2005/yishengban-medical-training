INSERT INTO scenes (
  title, description, role, background, opening_message, difficulty, is_active
)
SELECT
  'OSCE模拟问诊与病历书写',
  '以问诊为核心，训练规范病史采集、临床归纳和独立病历书写',
  '标准化患者',
  '内科OSCE考站。学生扮演接诊医生，AI扮演标准化患者并快速提供必要检查结果。',
  '请以接诊医生身份开始问诊，并在结束前完成病历记录。',
  4,
  1
WHERE NOT EXISTS (
  SELECT 1 FROM scenes WHERE title = 'OSCE模拟问诊与病历书写'
);
