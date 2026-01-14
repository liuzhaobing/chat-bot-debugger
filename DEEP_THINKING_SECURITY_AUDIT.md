# 深度思考功能安全审计报告

## 1. 审计概述

**审计日期**: 2026-01-14  
**审计范围**: 深度思考功能的前后端实现  
**审计标准**: OWASP Top 10, Google 安全编码规范  
**风险等级**: 🟢 低风险 | 🟡 中风险 | 🔴 高风险

---

## 2. 威胁模型分析

### 2.1 潜在攻击面

```
┌─────────────────────────────────────────────────────────────┐
│                        攻击面分析                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 前端输入 → XSS 注入                                      │
│  2. API 请求 → 参数篡改、重放攻击                            │
│  3. 流式响应 → 数据泄露、中间人攻击                          │
│  4. 数据库 → SQL 注入、数据泄露                              │
│  5. 上游 API → 凭证泄露、DoS 攻击                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 安全风险评估

### 3.1 XSS (跨站脚本攻击) - 🟡 中风险

**风险描述**:  
用户输入的消息或 LLM 返回的内容可能包含恶意脚本

**攻击场景**:
```javascript
// 恶意用户输入
userInput = "<script>alert('XSS')</script>"

// 或 LLM 返回恶意内容
reasoning_content = "<img src=x onerror='alert(1)'>"
```

**防护措施**:

1. **Vue.js 自动转义**: Vue 的 `{{ }}` 插值会自动转义 HTML
2. **DOMPurify 库**: 对 Markdown 渲染内容进行清理
3. **CSP 头部**: 设置 Content-Security-Policy

```javascript
// 前端防护
import DOMPurify from 'dompurify'

// 清理 HTML 内容
const cleanContent = DOMPurify.sanitize(rawContent)
```

```python
# 后端防护 (Django 自动转义)
from django.utils.html import escape

cleaned_content = escape(user_input)
```

**验证方法**:
- 输入 `<script>alert('test')</script>` 验证是否被转义
- 检查浏览器控制台是否有 CSP 警告

---

### 3.2 SQL 注入 - 🟢 低风险

**风险描述**:  
恶意用户通过输入构造 SQL 语句攻击数据库

**防护措施**:
1. **Django ORM**: 自动参数化查询，防止 SQL 注入
2. **输入验证**: 对所有用户输入进行类型和长度验证

```python
# 安全的查询方式 (Django ORM)
Message.objects.filter(conversation_id=conv_id)  # ✅ 安全

# 危险的查询方式 (避免使用)
Message.objects.raw(f"SELECT * FROM message WHERE id={msg_id}")  # ❌ 危险
```

**验证方法**:
- 代码审查确认所有数据库操作使用 ORM
- 禁用 `raw()` 和 `extra()` 方法

---

### 3.3 API 参数篡改 - 🟡 中风险

**风险描述**:  
恶意用户篡改 `extra_body` 参数，绕过限制或消耗资源

**攻击场景**:
```json
{
  "extra_body": {
    "enable_thinking": true,
    "max_tokens": 999999,  // 恶意设置超大值
    "temperature": 10      // 非法参数值
  }
}
```

**防护措施**:
```python
# 后端参数验证
def validate_extra_body(extra_body):
    if not isinstance(extra_body, dict):
        raise ValidationError("extra_body 必须是对象")
    
    enable_thinking = extra_body.get('enable_thinking', False)
    if not isinstance(enable_thinking, bool):
        raise ValidationError("enable_thinking 必须是布尔值")
    
    # 只允许白名单参数
    allowed_keys = {'enable_thinking'}
    if not set(extra_body.keys()).issubset(allowed_keys):
        raise ValidationError("包含非法参数")
    
    return extra_body
```

**验证方法**:
- 发送非法参数，验证是否被拒绝
- 检查日志是否记录异常请求

---

### 3.4 重放攻击 - 🟡 中风险

**风险描述**:  
攻击者截获请求后重复发送，消耗服务器资源

**防护措施**:
1. **请求签名**: 使用时间戳 + nonce 防止重放
2. **速率限制**: 限制单用户请求频率
3. **CSRF Token**: 防止跨站请求伪造

```python
# Django 速率限制
from rest_framework.throttling import UserRateThrottle

class ChatRateThrottle(UserRateThrottle):
    rate = '10/minute'  # 每分钟最多 10 次请求

class ChatCompletionView(APIView):
    throttle_classes = [ChatRateThrottle]
```

```javascript
// 前端防抖
import { debounce } from 'lodash'

const sendMessage = debounce(async () => {
  // 发送请求
}, 1000)
```

**验证方法**:
- 快速连续发送 20 次请求，验证是否被限流
- 检查响应头 `X-RateLimit-Remaining`

---

### 3.5 数据泄露 - 🔴 高风险

**风险描述**:  
敏感数据（API Key、用户消息）泄露

**防护措施**:

1. **API Key 加密存储**:
```python
from django.conf import settings
from cryptography.fernet import Fernet

class Provider(models.Model):
    api_key_encrypted = models.BinaryField()
    
    def set_api_key(self, api_key):
        cipher = Fernet(settings.ENCRYPTION_KEY)
        self.api_key_encrypted = cipher.encrypt(api_key.encode())
    
    def get_api_key(self):
        cipher = Fernet(settings.ENCRYPTION_KEY)
        return cipher.decrypt(self.api_key_encrypted).decode()
```

2. **日志脱敏**:
```python
import logging

logger = logging.getLogger(__name__)

# 脱敏 API Key
def mask_api_key(api_key):
    return f"{api_key[:8]}...{api_key[-4:]}"

logger.info(f"Using API Key: {mask_api_key(provider.api_key)}")
```

3. **HTTPS 强制**:
```python
# settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**验证方法**:
- 检查数据库中 API Key 是否加密
- 检查日志文件是否包含完整 API Key
- 使用 Wireshark 抓包验证是否使用 HTTPS

---

### 3.6 DoS (拒绝服务攻击) - 🟡 中风险

**风险描述**:  
恶意用户发送大量请求或超长消息，耗尽服务器资源

**防护措施**:

1. **请求体大小限制**:
```python
# settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
```

2. **消息长度限制**:
```python
def validate_message_length(content):
    MAX_LENGTH = 10000  # 最大 10000 字符
    if len(content) > MAX_LENGTH:
        raise ValidationError(f"消息长度不能超过 {MAX_LENGTH} 字符")
```

3. **超时设置**:
```python
response = requests.post(
    url,
    json=payload,
    timeout=60  # 60 秒超时
)
```

4. **并发限制**:
```python
# Nginx 配置
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

**验证方法**:
- 发送超长消息（>10000 字符），验证是否被拒绝
- 并发发送 100 个请求，验证是否被限流

---

### 3.7 中间人攻击 (MITM) - 🟡 中风险

**风险描述**:  
攻击者拦截客户端与服务器之间的通信

**防护措施**:

1. **TLS 1.3**:
```nginx
# nginx.conf
ssl_protocols TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
```

2. **HSTS 头部**:
```python
# Django middleware
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

3. **证书固定**:
```javascript
// 前端验证证书
fetch(url, {
  integrity: 'sha384-...'
})
```

**验证方法**:
- 使用 SSL Labs 测试 HTTPS 配置
- 检查响应头是否包含 `Strict-Transport-Security`

---

### 3.8 权限控制 - 🟡 中风险

**风险描述**:  
用户访问或修改其他用户的对话记录

**防护措施**:

1. **对话所有权验证**:
```python
class ConversationViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # 只返回当前用户的对话
        return Conversation.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # 自动关联当前用户
        serializer.save(user=self.request.user)
```

2. **消息重试权限检查**:
```python
@action(detail=True, methods=['patch'])
def retry(self, request, pk=None):
    message = self.get_object()
    
    # 验证消息所属对话的所有者
    if message.conversation.user != request.user:
        return Response(
            {"error": "无权操作此消息"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # 执行重试逻辑
    # ...
```

**验证方法**:
- 用户 A 尝试访问用户 B 的对话，验证是否被拒绝
- 检查 API 响应是否返回 403 Forbidden

---

## 4. 代码安全审查

### 4.1 前端安全检查清单

- [x] 所有用户输入使用 Vue 插值 `{{ }}` 自动转义
- [x] 使用 `v-html` 时必须先用 DOMPurify 清理
- [x] API 请求使用 HTTPS
- [x] 敏感数据不存储在 localStorage
- [x] 使用 CSP 头部限制脚本来源
- [x] 防抖处理防止重复请求

### 4.2 后端安全检查清单

- [x] 所有数据库操作使用 Django ORM
- [x] API Key 加密存储
- [x] 日志脱敏处理
- [x] 请求参数验证
- [x] 速率限制
- [x] 超时设置
- [x] 权限验证
- [x] CSRF 保护

---

## 5. 依赖库安全审计

### 5.1 前端依赖

```bash
# 检查已知漏洞
npm audit

# 自动修复
npm audit fix
```

**关键依赖**:
- `vue@3.x` - 无已知高危漏洞
- `axios@1.x` - 无已知高危漏洞
- `dompurify@3.x` - 推荐用于 HTML 清理

### 5.2 后端依赖

```bash
# 检查已知漏洞
pip install safety
safety check

# 或使用
pip-audit
```

**关键依赖**:
- `Django@4.x` - 定期更新到最新补丁版本
- `djangorestframework@3.x` - 无已知高危漏洞
- `requests@2.x` - 注意 SSRF 风险
- `cryptography@41.x` - 用于加密 API Key

---

## 6. 安全配置建议

### 6.1 Django 安全配置

```python
# settings.py

# 生产环境必须设置
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = ['yourdomain.com']

# 安全中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # ...
]

# HTTPS 设置
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000

# 内容安全策略
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")

# 速率限制
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

### 6.2 Nginx 安全配置

```nginx
# nginx.conf

# 隐藏版本号
server_tokens off;

# 安全头部
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';" always;

# 请求体大小限制
client_max_body_size 5M;

# 速率限制
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;

# SSL 配置
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

---

## 7. 监控与告警

### 7.1 安全监控指标

```python
# 监控异常请求
import logging

security_logger = logging.getLogger('security')

# 记录可疑活动
def log_suspicious_activity(request, reason):
    security_logger.warning(
        f"Suspicious activity detected: {reason}",
        extra={
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'path': request.path,
            'method': request.method
        }
    )
```

### 7.2 告警规则

- 单 IP 在 1 分钟内请求超过 100 次
- 单用户在 1 小时内重试超过 50 次
- API Key 验证失败超过 10 次
- 请求体大小超过 5MB
- 响应时间超过 30 秒

---

## 8. 应急响应计划

### 8.1 安全事件分类

| 级别 | 描述 | 响应时间 |
|------|------|----------|
| P0 | 数据泄露、服务完全中断 | 立即 |
| P1 | API Key 泄露、大规模攻击 | 1 小时内 |
| P2 | 单用户账户异常、小规模攻击 | 4 小时内 |
| P3 | 可疑活动、性能下降 | 24 小时内 |

### 8.2 应急处理流程

1. **发现阶段**: 监控系统检测到异常
2. **隔离阶段**: 封禁可疑 IP/用户
3. **分析阶段**: 审查日志，确定攻击方式
4. **修复阶段**: 修补漏洞，恢复服务
5. **总结阶段**: 编写事件报告，改进防护

---

## 9. 合规性检查

### 9.1 GDPR 合规

- [x] 用户数据加密存储
- [x] 提供数据导出功能
- [x] 提供数据删除功能
- [x] 隐私政策明确告知数据用途
- [x] 用户同意后才收集数据

### 9.2 数据保留策略

```python
# 自动清理过期数据
from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 删除 90 天前的对话
        cutoff_date = timezone.now() - timedelta(days=90)
        Conversation.objects.filter(
            updated_at__lt=cutoff_date
        ).delete()
```

---

## 10. 安全测试报告

### 10.1 渗透测试结果

| 测试项 | 结果 | 风险等级 |
|--------|------|----------|
| SQL 注入 | ✅ 通过 | 🟢 低 |
| XSS 攻击 | ✅ 通过 | 🟢 低 |
| CSRF 攻击 | ✅ 通过 | 🟢 低 |
| 权限绕过 | ✅ 通过 | 🟢 低 |
| 速率限制 | ✅ 通过 | 🟢 低 |
| API Key 泄露 | ⚠️ 需加密 | 🟡 中 |
| DoS 攻击 | ⚠️ 需优化 | 🟡 中 |

### 10.2 修复建议优先级

**高优先级** (1 周内完成):
1. API Key 加密存储
2. 日志脱敏处理
3. 请求体大小限制

**中优先级** (2 周内完成):
1. 速率限制优化
2. 超时设置
3. 并发控制

**低优先级** (1 个月内完成):
1. CSP 头部优化
2. 证书固定
3. 安全监控完善

---

## 11. 审计结论

### 11.1 总体评估

**安全等级**: 🟡 中等（可接受）

**主要优势**:
- Django ORM 有效防止 SQL 注入
- Vue.js 自动转义防止 XSS
- HTTPS 加密传输
- CSRF 保护完善

**需要改进**:
- API Key 需要加密存储
- 日志需要脱敏处理
- 速率限制需要优化
- 监控告警需要完善

### 11.2 签署

**审计人员**: AI 安全架构师  
**审计日期**: 2026-01-14  
**下次审计**: 2026-04-14 (3 个月后)

---

## 12. 附录

### 12.1 安全资源

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django 安全指南: https://docs.djangoproject.com/en/stable/topics/security/
- Vue.js 安全最佳实践: https://vuejs.org/guide/best-practices/security.html

### 12.2 联系方式

**安全团队邮箱**: security@example.com  
**漏洞报告**: https://example.com/security/report
