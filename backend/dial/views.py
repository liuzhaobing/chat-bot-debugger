import copy
import json
import time
import urllib3
import logging
import datetime
import threading

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import StreamingHttpResponse

from .models import CallSession, CallTranscript
from .serializers import CallSessionSerializer, CallTranscriptSerializer
from .client import DialClient, generate_trace_id, text_to_speech

from chat.models import App, AppScenario
from chat.views import AppViewSet

from utils import extract_output_json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ScenarioTestRunner:
    """
    场景测试执行器
    实现AI USER -> TTS -> DIAL ASSISTANT -> AI JUDGER的循环
    """

    def __init__(
            self,
            scenario,
            app_id,
            stop_event,
            logger: logging.LoggerAdapter = logging.getLogger(__name__),
    ):
        self.logger = logger
        self.scenario = scenario
        self.app_id = app_id
        self.stop_event = stop_event
        self.session_id = generate_trace_id(prefix="DIAL")
        self.chat_history = []
        self.max_rounds = 30  # 最大对话轮数
        self.current_round = 0

        # 初始化客户端
        self.dial_client = DialClient(
            address="https://call-center-test.myroki.com",
            consumer_id="17744270115",
        )

        # AI USER应用ID (生成用户查询)
        self.ai_user_app_id = "37ccee2a148f46199061c955fa70f9b7"
        # AI JUDGER应用ID (判断是否继续)
        self.ai_judger_app_id = "a989422993664696b7ffdabae68d94b6"

    def run(self):
        """运行场景测试"""
        try:
            yield {
                "type": "status",
                "data": {"message": f"开始场景测试: {self.scenario.name}"}
            }

            # 1. 开始通话会话
            success, result = self.dial_client.dialogue_start(
                session_id=self.session_id
            )

            if not success:
                yield {
                    "type": "error",
                    "data": {"message": f"启动通话失败: {result}"}
                }
                return

            yield {
                "type": "status",
                "data": {"message": "通话会话已建立"}
            }

            # 2. 开始Agent循环
            while self.current_round < self.max_rounds and not self.stop_event.is_set():
                self.current_round += 1

                yield {
                    "type": "status",
                    "data": {"message": f"第 {self.current_round} 轮对话开始"}
                }

                # Step 1: AI USER生成查询
                user_query = self.generate_user_query()
                if not user_query:
                    break

                yield {
                    "type": "ai_user_query",
                    "data": {"query": user_query.get("user_input")}
                }

                # Step 2: TTS合成音频
                tts_audio = text_to_speech(user_query.get("user_input"))
                if tts_audio:
                    yield {
                        "type": "tts_audio",
                        "data": {
                            "audio_data": tts_audio,
                            "sample_rate": 24000
                        }
                    }

                # Step 3: 调用DIAL ASSISTANT
                dial_response = self.call_dial_assistant(user_query, tts_audio)
                if not dial_response:
                    break

                yield {
                    "type": "dial_response",
                    "data": {"response": dial_response}
                }

                # 更新聊天历史
                self.chat_history.append({
                    "role": "user",
                    "content": user_query
                })
                self.chat_history.append({
                    "role": "assistant",
                    "content": dial_response
                })

                # Step 4: AI JUDGER判断是否继续
                is_continue, reason = self.judge_continue()

                yield {
                    "type": "judger_result",
                    "data": {
                        "is_continue": is_continue,
                        "reason": reason,
                        "round": self.current_round
                    }
                }

                if not is_continue:
                    yield {
                        "type": "status",
                        "data": {"message": f"测试完成: {reason}"}
                    }
                    break

                # 短暂延迟
                time.sleep(1)

            # 结束通话
            self.dial_client.dialogue_end(
                session_id=self.session_id,
                call_duration=self.current_round * 30  # 估算通话时长
            )

            yield {
                "type": "completed",
                "data": {
                    "total_rounds": self.current_round,
                    "scenario_name": self.scenario.name
                }
            }

        except Exception as e:
            self.logger.error(f"场景测试运行异常: {e}")
            yield {
                "type": "error",
                "data": {"message": str(e)}
            }

    def generate_user_query(self) -> dict | None:
        """使用AI USER应用生成用户查询"""
        try:
            # 从场景参数中提取必要信息
            scenario_params = copy.deepcopy(self.scenario.parameters)
            scenario_params["history_messages"] = self.chat_history
            scenario_params["now_time"] = datetime.datetime.now().strftime("%Y年%m月%d日 %H点%M分%S秒")

            # 如果是第一轮对话，使用first_input
            if self.current_round == 1 and scenario_params.get("first_input"):
                return {"user_input": scenario_params["first_input"]}

            # 调用AI USER应用
            app_viewset = AppViewSet()
            app = App.objects.get(id=self.ai_user_app_id)

            result = app_viewset._execute_app(app=app, parameters=scenario_params)

            if result["status"] == "success":
                content = result["content"].strip()
                return extract_output_json(content) or {"user_input": content}
            else:
                self.logger.error(f'AI USER生成query失败: {result.get("error")}')
                return None

        except Exception as e:
            self.logger.error(f"生成用户query异常: {e}")
            return None

    def call_dial_assistant(self, query, audio_data=None):
        """调用DIAL ASSISTANT"""
        try:
            result, costs, exception = self.dial_client.completions_stream(
                session_id=self.session_id,
                index=self.current_round - 1,
                query=query,
                user_audio=audio_data,
                traceId=generate_trace_id("DIAL")
            )

            if exception:
                self.logger.error(f"DIAL ASSISTANT调用失败: {exception}")
                return None

            return result.get("answer", "")

        except Exception as e:
            self.logger.error(f"调用DIAL ASSISTANT异常: {e}")
            return None

    def judge_continue(self):
        """使用AI JUDGER判断是否继续对话"""
        try:
            # 从场景参数中提取必要信息
            scenario_params = copy.deepcopy(self.scenario.parameters)
            scenario_params["history_messages"] = self.chat_history
            scenario_params["now_time"] = datetime.datetime.now().strftime("%Y年%m月%d日 %H点%M分%S秒")

            # 调用AI JUDGER应用
            app_viewset = AppViewSet()
            app = App.objects.get(id=self.ai_judger_app_id)

            result = app_viewset._execute_app(app=app, parameters=scenario_params)

            if result["status"] == "success":
                try:
                    judge_result = json.loads(result["content"].strip())
                    return judge_result.get("is_continue", False), judge_result.get("analysis", "未知原因")
                except json.JSONDecodeError:
                    # 如果返回的不是JSON，尝试解析文本
                    content = result["content"].lower()
                    if "false" in content or "不继续" in content or "结束" in content:
                        return False, "判断器建议结束对话"
                    else:
                        return True, "继续对话"
            else:
                self.logger.error(f'AI JUDGER判断失败: {result.get("error")}')
                # 默认继续，但不超过最大轮数
                return self.current_round < self.max_rounds, "判断器调用失败，使用默认策略"

        except Exception as e:
            self.logger.error(f"判断是否继续异常: {e}")
            return False, f"判断异常: {str(e)}"

    def stop(self):
        """停止测试"""
        self.stop_event.set()


# 全局变量存储当前运行的场景测试
current_scenario_test: ScenarioTestRunner = None
scenario_test_stop_event: threading.Event = None


class CallSessionViewSet(viewsets.ModelViewSet):
    """通话会话管理"""
    queryset = CallSession.objects.all()
    serializer_class = CallSessionSerializer

    @action(detail=False, methods=["post"])
    def create_session(self, request):
        """创建新的通话会话"""
        data = request.data
        session = CallSession.objects.create(
            session_id=data.get("session_id"),
            room_id=data.get("room_id"),
            user_id=data.get("user_id"),
            participant_id=data.get("participant_id"),
            agent_type=data.get("agent_type", "robam_workflow"),
            config_template=data.get("config_template", "ai_telephone"),
            status="active"
        )
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def end_session(self, request, pk=None):
        """结束通话会话"""
        session = self.get_object()
        from django.utils import timezone
        session.status = "ended"
        session.ended_at = timezone.now()
        if session.started_at:
            duration = (session.ended_at - session.started_at).total_seconds()
            session.duration = int(duration)
        session.save()
        serializer = self.get_serializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_transcript(self, request, pk=None):
        """添加字幕记录"""
        session = self.get_object()
        data = request.data
        transcript = CallTranscript.objects.create(
            session=session,
            speaker=data.get("speaker"),
            text=data.get("text"),
            is_final=data.get("is_final", False)
        )
        serializer = CallTranscriptSerializer(transcript)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def transcripts(self, request, pk=None):
        """获取会话的所有字幕"""
        session = self.get_object()
        transcripts = session.transcripts.all()
        serializer = CallTranscriptSerializer(transcripts, many=True)
        return Response(serializer.data)


class ScenarioTestView(APIView):
    """
    场景测试视图
    实现AI USER自动测试场景的功能
    """

    def post(self, request):
        """开始场景测试"""
        global current_scenario_test, scenario_test_stop_event

        scenario_id = request.data.get("scenario_id")
        app_id = request.data.get("app_id")

        if not scenario_id or not app_id:
            return Response({
                "error": "缺少必要参数 scenario_id 或 app_id"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            scenario = AppScenario.objects.get(id=scenario_id)
            app = App.objects.get(id=app_id)
        except (AppScenario.DoesNotExist, App.DoesNotExist) as e:
            return Response({
                "error": "场景或应用不存在"
            }, status=status.HTTP_404_NOT_FOUND)

        # 检查是否已有测试在运行
        if current_scenario_test is not None:
            return Response({
                "error": "已有场景测试在运行中"
            }, status=status.HTTP_409_CONFLICT)

        # 创建停止事件
        scenario_test_stop_event = threading.Event()

        # 创建SSE响应
        def event_stream():
            global current_scenario_test

            try:
                current_scenario_test = ScenarioTestRunner(
                    scenario=scenario,
                    app_id=app_id,
                    stop_event=scenario_test_stop_event
                )

                # 开始测试
                for event in current_scenario_test.run():
                    if scenario_test_stop_event.is_set():
                        break
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            except Exception as e:
                yield f'data: {json.dumps({"type": "error", "data": {"message": str(e)}}, ensure_ascii=False)}\n\n'
            finally:
                current_scenario_test = None
                yield "data: [DONE]\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"

        return response


class ScenarioTestStopView(APIView):
    """停止场景测试"""

    def post(self, request):
        global current_scenario_test, scenario_test_stop_event

        if scenario_test_stop_event:
            scenario_test_stop_event.set()

        if current_scenario_test:
            current_scenario_test.stop()

        return Response({"message": "场景测试已停止"})
