# Build a sample vectorDB
from langchain.document_loaders import WebBaseLoader
# from langchain.document_loaders import WebBaseLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

from app.readconfig.myconfig import MyConfig

config = MyConfig()

# Load blog post
loader = WebBaseLoader("http://www.limaoyi.top/2023/06/27/Scrapy-%E5%85%A5%E9%97%A8%E6%8C%87%E5%8D%97-%E4%B8%80-%E5%AE%89%E8%A3%85%E4%B8%8E%E7%AE%80%E5%8D%95%E4%BD%BF%E7%94%A8/")
data = loader.load()

# Split
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
splits = text_splitter.split_documents(data)

# VectorDB
embedding = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)
vectordb = Chroma.from_documents(documents=splits, embedding=embedding)

from langchain.chat_models import ChatOpenAI
from langchain.retrievers.multi_query import MultiQueryRetriever
question="What are the scrapy?"
llm = ChatOpenAI(temperature=0,openai_api_key=config.OPENAI_API_KEY)
retriever_from_llm = MultiQueryRetriever.from_llm(retriever=vectordb.as_retriever(), llm=llm)

# Set logging for the queries
import logging
logging.basicConfig()
logging.getLogger('langchain.retrievers.multi_query').setLevel(logging.INFO)

unique_docs = retriever_from_llm.get_relevant_documents(query=question)
print(unique_docs)
len(unique_docs)

from typing import List
from langchain import LLMChain
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser


# Output parser will split the LLM result into a list of queries
class LineList(BaseModel):
    # "lines" is the key (attribute name) of the parsed output
    lines: List[str] = Field(description="Lines of text")


class LineListOutputParser(PydanticOutputParser):
    def __init__(self) -> None:
        super().__init__(pydantic_object=LineList)

    def parse(self, text: str) -> LineList:
        lines = text.strip().split("\n")
        return LineList(lines=lines)


output_parser = LineListOutputParser()

QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""Вы помощник языковой модели искусственного интеллекта. Ваша задача — создать пять
     различные версии заданного вопроса пользователя для извлечения соответствующих документов из вектора
     база данных. Создавая несколько точек зрения на вопрос пользователя, ваша цель — помочь
     пользователь преодолевает некоторые ограничения поиска по сходству на основе расстояния.
     Укажите эти альтернативные вопросы, разделенные символами новой строки.
     Исходный вопрос: {question}""",
)

llm = ChatOpenAI(temperature=0,openai_api_key=config.OPENAI_API_KEY)

# Chain
llm_chain = LLMChain(llm=llm, prompt=QUERY_PROMPT, output_parser=output_parser)

# Other inputs
# question = "What are the approaches to Task Decomposition?"

# Run
retriever = MultiQueryRetriever(retriever=vectordb.as_retriever(),
                                llm_chain=llm_chain,
                                parser_key="lines")  # "lines" is the key (attribute name) of the parsed output

# Results
unique_docs = retriever.get_relevant_documents(query="Что в курсе говорится о регрессии?")
for e in unique_docs:
    print(e)
len(unique_docs)