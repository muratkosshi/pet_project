# Импортируем необходимые модули из стандартной библиотеки Python, а также из пакетов langchain и langchain_community.
import os

from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.callbacks.streaming_stdout import \
    StreamingStdOutCallbackHandler  # Коллбэк для потоковой передачи вывода в stdout.
from langchain.chains import LLMChain  # Цепочка моделей языковых моделей для комбинирования нескольких операций.
from langchain.memory import RedisChatMessageHistory, ConversationBufferMemory  # Для управления историей чата в Redis.
from langchain.prompts import PromptTemplate  # Используется для создания шаблонов запросов для ИИ.
from langchain_community.chat_models import ChatOpenAI  # Модель чата для OpenAI.
from langchain_core.callbacks import BaseCallbackHandler


# Определение класса GptChain.
class TokenCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.total_tokens = 0

    def on_llm_new_token(self, token: str, **kwargs):
        # Увеличиваем общий счётчик токенов
        self.total_tokens += 1

    def get_total_tokens(self):
        return self.total_tokens


class GptChain:
    # Атрибуты класса для шаблона, ключа API OpenAI, идентификатора сессии, URL Redis, экземпляра LLMChain и истории сообщений.
    template: str = """ Вы чат-бот, разговаривающий с человеком.
    Человек: {human_input} """
    openai_api_key: str = None
    session_id: str = None
    redis_url: str = None
    llm_chain: LLMChain = None
    message_history: RedisChatMessageHistory = None
    gpt_version: str = None

    # Конструктор для инициализации GptChain с ключом API OpenAI, идентификатором сессии, URL Redis и базовым URL OpenAI.
    def __init__(self, openai_api_key, session_id, redis_url, openai_base_url):
        self.callback = None
        self.openai_api_key = openai_api_key
        self.session_id = session_id
        self.redis_url = redis_url
        self.openai_base_url = openai_base_url
        if self.gpt_version:
            self.redis_llm_chain_factory()  # Вызов метода, который настраивает LLMChain.
        self.callback = AsyncIteratorCallbackHandler()

    # Метод для создания LLMChain с историей чата на базе Redis и буферной памятью для диалогов.
    def redis_llm_chain_factory(self, gpt_version):
        # Создаём обработчик токенов
        self.token_handler = TokenCallbackHandler()



        prompt = PromptTemplate(
            input_variables=["human_input"], template=self.template
        )

        # Инициализация LLMChain с обработчиком токенов
        llm_chain = LLMChain(
            llm=ChatOpenAI(
                model_name=gpt_version,
                openai_api_key=self.openai_api_key,
                streaming=True,
                callbacks=[StreamingStdOutCallbackHandler(), self.token_handler],
                max_tokens=1000,
            ),
            prompt=prompt,
            verbose=True,
        )
        self.llm_chain = llm_chain

    # Метод для генерации предсказания/ответа на основе входящего вопроса.
    async def predict(self, question):
        result = self.llm_chain.predict(human_input=question)
        # Получаем общее количество токенов
        total_tokens = self.token_handler.get_total_tokens()
        print(f"Tokens used: {total_tokens}")
        return result

    # Метод для очистки истории чата в Redis.
    def clear_redis(self):
        self.message_history.clear()

    # async def send_message(self, content: str) -> AsyncIterable[str]:
    #
    #     model = ChatOpenAI(
    #         openai_api_key=os.getenv('OPENAI_API_KEY'),
    #         streaming=True,
    #         verbose=True,
    #         callbacks=[self.callback],
    #     )
    #
    #     task = asyncio.create_task(
    #         model.agenerate(messages=[[HumanMessage(content=content)]])
    #     )
    #     await task


# Основной блок для создания экземпляра GptChain и выполнения предсказания.
if __name__ == "__main__":
    # Инициализация экземпляра GptChain с ключом API OpenAI.
    chain = GptChain(os.getenv('OPENAI_API_KEY'))
    # Использование метода predict для генерации песни о газированной воде.
    song = chain.predict(question="Write me a song about sparkling water.")
    # Результат сохраняется в переменной 'song', но не выводится. Раскомментируйте следующую строку для вывода.
    # print(song)
