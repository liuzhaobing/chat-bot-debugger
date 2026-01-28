from django.core.management.base import BaseCommand
from chat.models import AppType, App, AppCategory


class Command(BaseCommand):
    help = 'Create sample Agent ASR applications'

    def handle(self, *args, **options):
        # 获取Agent ASR类型
        try:
            agent_asr_type = AppType.objects.get(code='agent_asr')
        except AppType.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Agent ASR type not found. Please run init_agent_asr_type first.')
            )
            return

        # 获取或创建分类
        category, _ = AppCategory.objects.get_or_create(name='语音处理')

        # 创建示例ASR应用
        apps_to_create = [
            {
                'name': 'VoiceToText',
                'description': '通用语音转文本服务，支持多种音频格式，提供高精度的语音识别功能',
                'system_prompt': '''你是一个专业的语音识别助手。你的任务是：

1. 接收用户上传的音频文件
2. 将音频内容准确转换为文本
3. 处理各种音频质量和环境噪音
4. 识别专业术语和特殊词汇
5. 保持转录的准确性和完整性

请始终提供清晰、准确的转录结果。如果音频质量较差或有不清楚的部分，请在相应位置标注 [不清楚] 或 [噪音]。''',
                'parameters': {
                    "type": "object",
                    "properties": {
                        "audio_data": {
                            "type": "string",
                            "description": "base64编码的音频数据"
                        },
                        "audio_format": {
                            "type": "string",
                            "enum": ["wav", "mp3", "m4a", "flac"],
                            "description": "音频格式",
                            "default": "wav"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["zh-CN", "en-US", "auto"],
                            "description": "识别语言",
                            "default": "zh-CN"
                        },
                        "context": {
                            "type": "string",
                            "description": "上下文信息，帮助提高识别准确度"
                        }
                    },
                    "required": ["audio_data"]
                }
            },
            {
                'name': 'SmartHomeASR',
                'description': '智能家居专用语音识别，针对家电控制指令进行优化，支持设备型号和操作指令的精确识别',
                'system_prompt': '''你是智能家居语音识别专家。你专门识别与家电控制相关的语音指令，包括：

1. 设备名称：油烟机、空调、洗碗机、热水器、净水器等
2. 设备型号：CQ928、C92U2、W76-i1等具体型号
3. 操作指令：开启、关闭、调节温度、设置模式等
4. 工作模式：澎湃蒸、风焙烤、智能洗、净存消毒等专业模式

请特别注意设备型号的准确识别，包括连字符和大小写。''',
                'parameters': {
                    "type": "object",
                    "properties": {
                        "audio_data": {
                            "type": "string",
                            "description": "base64编码的音频数据"
                        },
                        "device_context": {
                            "type": "string",
                            "description": "设备上下文信息"
                        },
                        "previous_command": {
                            "type": "string",
                            "description": "上一条指令，用于上下文理解"
                        }
                    },
                    "required": ["audio_data"]
                }
            },
            {
                'name': 'CallCenterASR',
                'description': '客服中心语音识别，专门处理客服对话场景，支持多轮对话上下文和客服专业术语',
                'system_prompt': '''你是客服中心语音识别专家。你需要准确识别客服对话中的内容，包括：

1. 客户问题和需求
2. 产品型号和技术参数
3. 安装、维修、售后等服务内容
4. 地址、联系方式等关键信息
5. 情绪表达和语气变化

请保持高度的准确性，特别是涉及产品型号、地址、电话号码等关键信息。''',
                'parameters': {
                    "type": "object",
                    "properties": {
                        "audio_data": {
                            "type": "string",
                            "description": "base64编码的音频数据"
                        },
                        "conversation_history": {
                            "type": "string",
                            "description": "对话历史记录"
                        },
                        "customer_info": {
                            "type": "string",
                            "description": "客户信息上下文"
                        },
                        "service_type": {
                            "type": "string",
                            "enum": ["installation", "repair", "consultation", "complaint"],
                            "description": "服务类型"
                        }
                    },
                    "required": ["audio_data"]
                }
            }
        ]

        for app_data in apps_to_create:
            app, created = App.objects.get_or_create(
                name=app_data['name'],
                defaults={
                    'description': app_data['description'],
                    'app_type': agent_asr_type,
                    'category': category,
                    'system_prompt': app_data['system_prompt'],
                    'parameters': app_data['parameters'],
                    'execution_mode': 'task',
                    'is_featured': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created ASR app: {app.name}')
                )
            else:
                self.stdout.write(f'ASR app already exists: {app.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample Agent ASR applications')
        )