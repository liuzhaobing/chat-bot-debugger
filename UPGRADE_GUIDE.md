# 升级指南 v1.0.0 → v1.1.0

本指南帮助您从 v1.0.0 升级到 v1.1.0。

## 🔄 主要变更

### 1. UUID 主键迁移
Provider 和 LLMModel 的主键从自增整数改为 32 位 hex UUID 字符串。

### 2. 模型查询修复
修复了多供应商同名模型导致的查询错误。

### 3. UI 统一优化
文本对话页面与模型调试页面采用统一的设计风格。

## 📋 升级步骤

### 步骤 1: 备份数据库

**重要**: 在执行任何迁移之前，请务必备份数据库！

```bash
# 备份 SQLite 数据库
cp backend/db.sqlite3 backend/db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)
```

### 步骤 2: 更新代码

```bash
# 拉取最新代码
git pull origin main

# 或者如果您有本地修改
git stash
git pull origin main
git stash pop
```

### 步骤 3: 更新后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 步骤 4: 执行数据库迁移

```bash
cd backend
python manage.py migrate chat
```

**预期输出**:
```
Operations to perform:
  Apply all migrations: chat
Running migrations:
  Applying chat.0013_auto_20260115_0535... OK
  Applying chat.0014_migrate_ids_to_uuid... OK
```

### 步骤 5: 验证迁移

运行测试脚本验证迁移是否成功：

```bash
cd backend
python test_uuid.py
python test_model_query.py
```

**预期结果**:
- 所有 Provider 和 LLMModel 的 ID 都是 32 位 hex 字符串
- 组合查询（provider_id + model_name）正常工作
- 单独使用 model_name 查询会抛出 MultipleObjectsReturned 异常（如果有重复）

### 步骤 6: 更新前端

```bash
cd frontend
npm install
npm run build  # 生产环境
# 或
npm run serve  # 开发环境
```

### 步骤 7: 重启服务

```bash
# 使用启动脚本
./stop.sh
./start.sh

# 或手动重启
# 后端
cd backend
python manage.py runserver

# 前端
cd frontend
npm run serve
```

## ⚠️ 破坏性变更

### API 变更

#### 1. ID 格式变更

**之前**:
```json
{
  "id": 1,
  "name": "OpenAI"
}
```

**现在**:
```json
{
  "id": "adbf322a7fcb417c9a68aafb746ea18b",
  "name": "OpenAI"
}
```

**影响**: 如果您的前端代码或外部系统依赖整数 ID，需要更新为支持字符串 ID。

#### 2. Chat Completions API

**之前**（可选 provider_id）:
```json
{
  "model": "gpt-4",
  "messages": [...]
}
```

**现在**（必需 provider_id）:
```json
{
  "provider_id": "adbf322a7fcb417c9a68aafb746ea18b",
  "model": "gpt-4",
  "messages": [...]
}
```

**影响**: 所有调用 `/api/chat/completions` 的代码都需要添加 `provider_id` 参数。

### 数据库变更

#### 表结构变更

**chat_provider**:
- `id`: INTEGER → VARCHAR(32)

**chat_llmmodel**:
- `id`: INTEGER → VARCHAR(32)
- `provider_id`: INTEGER → VARCHAR(32)

**chat_app**:
- `provider_id`: INTEGER → VARCHAR(32)

## 🔧 故障排查

### 问题 1: 迁移失败

**症状**: 
```
django.db.utils.IntegrityError: ...
```

**解决方案**:
1. 恢复备份数据库
2. 检查是否有外键约束冲突
3. 手动清理问题数据后重新迁移

```bash
# 恢复备份
cp backend/db.sqlite3.backup.YYYYMMDD_HHMMSS backend/db.sqlite3

# 重新迁移
python manage.py migrate chat
```

### 问题 2: 前端显示 ID 错误

**症状**: 前端显示 UUID 而不是友好名称

**解决方案**: 
- 确保前端使用 `name` 或 `display_name` 字段显示，而不是 `id`
- 检查序列化器是否正确返回所需字段

### 问题 3: API 调用失败

**症状**:
```json
{
  "error": "provider_id is required"
}
```

**解决方案**:
更新 API 调用，添加 `provider_id` 参数：

```javascript
// 错误
const response = await fetch('/api/chat/completions', {
  method: 'POST',
  body: JSON.stringify({
    model: 'gpt-4',
    messages: [...]
  })
})

// 正确
const response = await fetch('/api/chat/completions', {
  method: 'POST',
  body: JSON.stringify({
    provider_id: 'adbf322a7fcb417c9a68aafb746ea18b',
    model: 'gpt-4',
    messages: [...]
  })
})
```

### 问题 4: 模型查询返回多个结果

**症状**:
```
MultipleObjectsReturned: get() returned more than one LLMModel
```

**解决方案**:
使用组合查询：

```python
# 错误
model = LLMModel.objects.get(name='gpt-4')

# 正确
model = LLMModel.objects.get(
    provider_id=provider_id,
    name='gpt-4'
)
```

## 📊 验证清单

升级完成后，请验证以下功能：

- [ ] 后端服务正常启动
- [ ] 前端页面正常加载
- [ ] 模型广场显示正常
- [ ] 模型调试功能正常
- [ ] 应用广场显示正常
- [ ] 应用配置和调试正常
- [ ] 文本对话功能正常
- [ ] 对话历史正常保存和加载
- [ ] 多模态输入（图片）正常工作

## 🔙 回滚方案

如果升级后遇到严重问题，可以回滚到 v1.0.0：

### 步骤 1: 恢复数据库备份

```bash
cp backend/db.sqlite3.backup.YYYYMMDD_HHMMSS backend/db.sqlite3
```

### 步骤 2: 回滚代码

```bash
git checkout v1.0.0
```

### 步骤 3: 重新安装依赖

```bash
cd backend
pip install -r requirements.txt

cd ../frontend
npm install
```

### 步骤 4: 重启服务

```bash
./stop.sh
./start.sh
```

## 📞 获取帮助

如果您在升级过程中遇到问题：

1. 查看 [CHANGELOG.md](./CHANGELOG.md) 了解详细变更
2. 查看 [README.md](./README.md) 了解系统架构
3. 运行测试脚本诊断问题：
   ```bash
   cd backend
   python test_uuid.py
   python test_model_query.py
   ```

## 🎉 升级完成

恭喜！您已成功升级到 v1.1.0。

新版本带来了以下改进：
- ✅ 更好的 ID 辨识度（UUID）
- ✅ 修复了多供应商同名模型的查询问题
- ✅ 统一的 UI 设计风格
- ✅ 更简洁的文档结构

享受新版本带来的改进吧！
