import logging
import os

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler,
    AbstractExceptionHandler,
)
from ask_sdk_core.utils import is_request_type, is_intent_name

from google import genai


# ===== Gemini 設定 =====
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)

MODEL_NAME = "gemini-2.5-flash"


# ===== ログ設定 =====
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

sb = SkillBuilder()


# ===== Gemini 呼び出し関数 =====
def ask_gemini(question: str) -> str:
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"日本語で、短く、音声向けに答えてください。\n質問: {question}"
        )

        return response.text if response.text else "すみません、回答できませんでした。"

    except Exception as e:
        logger.error(f"Gemini error: {e}", exc_info=True)
        return "すみません、うまく答えられませんでした。"


# ===== 例外ハンドラ =====
class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        return (
            handler_input.response_builder
            .speak("エラーが発生しました。もう一度試してください。")
            .ask("もう一度試しますか？")
            .response
        )


sb.add_exception_handler(CatchAllExceptionHandler())


# ===== LaunchRequest =====
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        logger.info("LaunchRequest received")
        return (
            handler_input.response_builder
            .speak("こんにちは。何について聞きたいですか？")
            .ask("何について聞きたいですか？")
            .response
        )


# ===== FreeAnswerIntent =====
class FreeAnswerIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("FreeAnswerIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("FreeAnswerIntent received")

        intent = handler_input.request_envelope.request.intent
        slots = intent.slots

        user_text = None
        if "anyText" in slots and slots["anyText"].value:
            user_text = slots["anyText"].value

        logger.info(f"USER_INPUT: {user_text}")

        if not user_text:
            speech = "質問が聞き取れませんでした。"
        else:
            speech = ask_gemini(user_text)

        return (
            handler_input.response_builder
            .speak(speech)
            .ask("他にも聞きたいことはありますか？")
            .response
        )


# ===== Handler 登録 =====
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(FreeAnswerIntentHandler())

lambda_handler = sb.lambda_handler()
