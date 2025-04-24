from typing import AsyncIterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db.database import get_async_session
from app.common.services.settings_service import SettingsService
from app.readconfig.myconfig import MyConfig
from app.engine.chain.gpt_memory import GptChain


class Gen:
    config: MyConfig = None
    GptChain: GptChain = None
    gpt_version: str = None
    session: AsyncSession = None

    def __init__(self, session_id, session: AsyncSession):
        self.config = MyConfig()
        self.session = session  # Передаем сессию явно
        self.GptChain = None  # Избегаем использования NoneType в дальнейшем
        self.session_id = session_id
    async def initialize_gpt_chain(self, session_id):
        """Асинхронно инициализируем GPT Chain с API-ключом"""
        openai_api_key = await SettingsService.get_or_set(
            session=self.session,
            key="openai_api_key",
            default=self.config.OPENAI_API_KEY,
            description="Ключ от GPT (https://platform.openai.com/)"
        )

        self.GptChain = GptChain(
            openai_api_key=openai_api_key,
            session_id=session_id,
            redis_url=self.config.REDIS_URL,
            openai_base_url=self.config.OPENAI_BASE_URL
        )


class GenOutline(Gen):
    def __init__(self, session_id, session: AsyncSession):
        super().__init__(session_id, session)  # ✅ Передаем session

    async def predict_outline_v2(self, title, topic_num, language='ru', ) -> AsyncIterable[str]:
        await self.initialize_gpt_chain(session_id=self.session_id)
        gpt_version = "gpt-4o-mini"
        if language == 'ru':
            text = f"""Используй разметку правила форматирования для создания структуры с {topic_num} заголовками для презентации, на основе темы ```{title}```, и выполни следующие требования:
                             2. Если вы хотите создать заголовок, добавьте знак решетки (#) перед словом или фразой. Символ # обозначает уровень титула.         
                             4. Вы не можете использовать неупорядоченные или упорядоченные списки. Для выражения структурной структуры необходимо использовать знаки решетки (#).
                             5. Для схемы требуется четкое соблюдения правилам и хорошая структура
                             6. Первая глава плана представляет собой введение в ``{title}```, а последняя глава представляет собой краткое изложение;
                             7. Нужно вернуть лишь вернуть разметку, БЕЗ ДОПОЛНИТЕЛЬНЫХ КОММЕНТАРИЕВ И БЕЗ НОМЕРАЦИЙ СЛАЙДОВ
                """
        elif language == 'en':
            text = f"""Use the formatting rule markup to create a structure in English with {topic_num} headings for the presentation, based on the ``{title}'' topic, and fulfill the following requirements:
                                              2. If you want to create a title, add a pound sign (#) before the word or phrase. The symbol # indicates the level of the title.
                                              4. You can either use unordered or ordered lists. To express the structural structure, it is necessary to use the sign grid (#).
                                              5. The scheme requires clear compliance with rules and a good structure
                                              6. The first chapter of the plan is an introduction to ``{title}'', and the last chapter is a summary;
                                              7. It is necessary to return only the marking, WITHOUT ADDITIONAL COMMENTS AND WITHOUT NUMBERING OF SLIDES
                                """
        elif language == 'kz':
            text = f"""Форматтау ережелерінің белгілеуін пайдаланып, {title} тақырыбына негізделген презентация үшін {topic_num} тақырыптары бар құрылым жасаңыз және келесі талаптарды орындаңыз:
                        2. Егер сіз тақырып атауын жасағыңыз келсе, сөз немесе сөйлем алдында диез белгісін (#) қосыңыз. Диез белгісі тақырып атауының деңгейін білдіреді.
                        4. Сіз реттелмеген немесе реттелген тізімдерді қолдана алмайсыз. Құрылымдық құрылымды білдіру үшін диез белгілерін (#) пайдалану керек.
                        5. Схема үшін ережелердің анық сақталуы және жақсы құрылым қажет
                        6. Жоспардың алғашқы тарауы {title} туралы кіріспе болып табылады, ал соңғы тарау қорытынды болып табылады;
                        7. Тек белгілеуді қайтару керек, ҚОСЫМША ТҮСІНІКТЕМЕЛЕРСІЗ ЖӘНЕ СЛАЙДТАРДЫҢ НӨМІРЛЕНУІСІЗ.
                                           """
            gpt_version = "gpt-4o-mini"
        self.GptChain.redis_llm_chain_factory(gpt_version)  # ✅ Теперь GptChain не будет None!
        return await self.GptChain.predict(text)


class GenBody(Gen):
    def __init__(self, session_id, session):
        super().__init__(session_id, session=session)

    async def predict_body(self, fix_outline=None, language='ru'):
        await self.initialize_gpt_chain(session_id=self.session_id)
        gpt_version = "gpt-4o-mini"
        if language == 'ru':
            text = f""" ```{fix_outline}```
                             Пожалуйста составь текст для призентации по данной схеме
                            Первый уровень (#) указывает заголовок структуры, второй уровень (##) указывает заголовок слайда, а третий уровень (###) указывает на смысл подзаголовка слайда.
                            1.Если вы хотите создать заголовок, добавьте знак решетки (#) перед словом или фразой. Символ # обозначает заголовок слайда и его начало. Символ <p> начало подзаголовка, а символ </p> конец подзаголовка.  
                             2. Не потеряйте исходную информацию и правила форматирования;
                             3. Каждый абзац подзаголовка должен быть обернут тегами <p></p>. Вам необходимо добавить как можно больше содержательной иформации и фактов на основе информации каждого заголовка и контекста. ;
                             4. Вам необходимо разместить сгенерированные абзацы в правильном положении;
                             5. Никаких дополнительных предложений, только лишь отформатированный и сгенерированный текст
                        
                """
        elif language == 'en':
            text = f""" ```{fix_outline}```
                                                     Please write the text for the presentation in English according to this scheme
                             The first level (#) indicates the title of the structure, the second level (##) indicates the title of the slide, and the third level (###) indicates the meaning of the subtitle of the slide.
                             1. If you want to create a title, add a pound sign (#) before the word or phrase. The symbol # indicates the title of the slide and its beginning. The symbol <p> is the beginning of the subheading, and the symbol </p> is the end of the subheading.
                              2. Don't lose the original information and formatting rules;
                              3. Each paragraph of the subheading should be wrapped with a <p></p> tag. You need to add as much meaningful information and facts as possible based on the information of each title and context. ;
                              4. You need to place the generated paragraphs in the correct position;
                              5. No additional offers, only formatted and generated text"""
        elif language == 'kz':
            text = f""" ```{fix_outline}```Келесі схема бойынша презентация үшін мәтін құрастырыңыз:
                Бірінші деңгей (#) құрылымның тақырып атауын көрсетеді, екінші деңгей (##) слайдтың тақырып атауын көрсетеді, ал үшінші деңгей (###) слайдтың төменгі тақырып атауының мәнін көрсетеді.
                
                1.Егер сіз тақырып атауын жасағыңыз келсе, сөз немесе сөйлем алдында диез белгісін (#) қосыңыз. Диез белгісі слайдтың тақырып атауын және оның басталуын білдіреді. <p> белгісі төменгі тақырып атауының басталуын, ал </p> белгісі төменгі тақырып атауының аяқталуын білдіреді.
                2.Бастапқы ақпарат пен форматтау ережелерін жоғалтпаңыз;
                3.Әрбір төменгі тақырып атауының абзацы <p></p> тегтерімен оралған болуы керек. Әрбір тақырып атауының және контекстің ақпаратына негізделген мазмұнды ақпарат пен деректерді мүмкіндігінше көп қосуыңыз керек.
                4.Жасалған абзацтарды дұрыс орналастыру қажет;
                5.Қосымша сөйлемдер жоқ, тек форматталған және жасалған мәтін ғана болуы керек."""
            gpt_version = "gpt-4o-mini"
        self.GptChain.redis_llm_chain_factory(gpt_version)
        return await self.GptChain.predict(text)


class GenPrompt(Gen):
    def __init__(self, session_id):
        super().__init__(session_id)

    def predict_promt(self, title):
        gpt_version = "gpt-4o-mini"
        text = f""" Create a prompt for an image generator. You need an original image related to the topic of your presentation: {title}. Use this prompt to inspire and unleash your imagination to visualize ideas and concepts for your presentation."""

        self.GptChain.redis_llm_chain_factory(gpt_version)
        return self.GptChain.predict(text)
