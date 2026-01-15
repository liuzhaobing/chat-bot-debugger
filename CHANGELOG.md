# 更新日志

## [1.1.1] - 2026-01-15

### 🐛 紧急修复

#### 1. 修复模型广场跳转模型调试报错
**问题**: 从模型广场点击"对话"按钮进入模型调试页面时，报错"缺少模型参数"

**原因**: 
- UUID迁移后，provider ID 从整数变为字符串
- `ModelDebugView.vue` 中使用 `parseInt(this.$route.query.provider)` 将UUID字符串转换为整数，导致解析失败

**解决方案**:
- 移除 `parseInt` 转换，直接使用字符串形式的 provider ID
- 修改 `loadModel()` 方法中的 `providerId` 获取逻辑

**影响文件**:
- `frontend/src/views/ModelDebugView.vue`

#### 2. 统一文本对话页侧边栏样式
**问题**: 文本对话页的侧边栏使用CSS变量主题，与模型调试页、应用调试页的浅色主题不一致

**改进内容**:
- 移除所有 CSS 变量（`var(--*)`），改为固定的浅色主题颜色
- 统一背景色：`#ffffff`
- 统一边框色：`#f1f5f9`、`#e2e8f0`
- 统一文本色：`#1e293b`、`#64748b`、`#94a3b8`
- 统一悬停色：`#f8fafc`
- 统一激活色：`#eef2ff`（紫色系）
- 统一删除按钮悬停色：`#fee2e2`（红色系）

**影响文件**:
- `frontend/src/components/Sidebar.vue`

### 📊 统计

- **修复文件**: 2个
- **代码行数**: ~50行

---

## [1.1.0] - 2026-01-15

### 🔧 修复

#### 1. 模型查询错误修复
**问题**: 当多个供应商提供同名模型时，`LLMModel.objects.get(name=model_name)` 会抛出 `MultipleObjectsReturned` 错误

**解决方案**:
- 修改所有模型查询逻辑，使用 `provider_id + model_name` 组合查询
- 更新 `ChatCompletionView.post()` 方法，要求必须传递 `provider_id`
- 更新 `ConversationViewSet.retry_message()` 方法，使用组合查询
- 前端模型调试页面确保传递 `provider_id` 参数

**影响文件**:
- `backend/chat/views.py`
- `frontend/src/views/ModelDebugView.vue`
- `frontend/src/components/app-configs/Agent1ConfigComponent.vue`

#### 2. UUID主键迁移
**问题**: Provider 和 LLMModel 使用自增ID，辨识度低

**解决方案**:
- 将 Provider 和 LLMModel 的主键改为 UUID（32位hex字符串，不带`-`）
- 创建数据迁移脚本自动转换现有数据
- 更新 App 模型中的 provider_id 字段类型为 CharField

**技术细节**:
```python
# 模型定义
id = models.CharField(max_length=32, primary_key=True, editable=False)

# 自动生成UUID
def save(self, *args, **kwargs):
    if not self.id:
        self.id = uuid.uuid4().hex
    super().save(*args, **kwargs)
```

**迁移文件**:
- `backend/chat/migrations/0013_auto_20260115_0535.py` - 修改字段类型
- `backend/chat/migrations/0014_migrate_ids_to_uuid.py` - 数据迁移

**影响文件**:
- `backend/chat/models.py`

### 🎨 UI改进

#### 3. 文本对话页面优化
**改进内容**:
- 统一UI风格：与模型调试页、应用调试页保持一致的设计语言
- 采用浅色主题（#f8fafc背景色）
- 优化输入框样式：白色背景、圆角边框、阴影效果
- 改进按钮样式：发送按钮使用主题色（#4f46e5）
- 移除主题切换功能，简化侧边栏
- 保留对话历史存储功能（与调试页的主要区别）

**影响文件**:
- `frontend/src/components/ChatArea.vue`
- `frontend/src/components/Sidebar.vue`

### 📚 文档整理

#### 4. 精简项目文档
**删除的文档**（重复或过时）:
- `DEEP_THINKING_ARCHITECTURE.md` (26K)
- `DEEP_THINKING_SECURITY_AUDIT.md` (15K)
- `FINAL_SUMMARY.md` (10K)
- `IMPLEMENTATION_SUMMARY_MODEL_DEBUG.md` (14K)
- `MODEL_DEBUG_README.md` (6.5K)
- `QUICK_START_MODEL_DEBUG.md` (7.6K)
- `README_IMPLEMENTATION.md` (8.9K)
- `UPDATE_NOTES_MODEL_DEBUG.md` (6.0K)
- `UPDATE_NOTES_V2.md` (9.9K)
- `UPDATE_NOTES.md` (8.8K)
- `VERIFICATION_CHECKLIST.md` (6.7K)

**保留的核心文档**:
- `README.md` - 项目主文档
- `ARCHITECTURE.md` - 系统架构
- `SECURITY_AUDIT.md` - 安全审计
- `IMPLEMENTATION_GUIDE.md` - 实现指南
- `MODEL_DEBUG_GUIDE.md` - 模型调试指南
- `PROJECT_STRUCTURE.md` - 项目结构
- `CHANGELOG.md` - 更新日志（新增）

**更新内容**:
- 更新 README.md，添加 UUID 和模型唯一标识说明
- 添加技术亮点章节
- 更新文档索引表

### 🔄 数据库迁移

**迁移步骤**:
```bash
cd backend
python manage.py migrate chat
```

**注意事项**:
- 迁移会自动将现有的整数ID转换为UUID
- 迁移不可逆，请在生产环境执行前备份数据库
- 迁移完成后，所有API响应中的ID都将是32位hex字符串

### 📊 统计

- **代码修改**: 5个文件
- **新增迁移**: 2个
- **删除文档**: 11个（约120KB）
- **保留文档**: 6个核心文档
- **文档精简率**: 约65%

### ⚠️ 破坏性变更

1. **ID格式变更**: Provider 和 LLMModel 的ID从整数变为32位hex字符串
2. **API变更**: `/api/chat/completions` 现在要求必须传递 `provider_id` 参数
3. **前端兼容**: 需要重新构建前端以使用新的API

### 🔜 后续计划

- [ ] 添加ID格式验证
- [ ] 优化UUID生成性能
- [ ] 添加API版本控制
- [ ] 完善错误提示信息

---

## [1.0.0] - 2026-01-14

### ✨ 初始版本

- 模型广场与调试功能
- 应用类型系统（Agent 1.0, Agent 2.0, Workflow）
- 应用广场与配置
- Function Calling 支持
- 文本对话功能
- 多模态输入支持
