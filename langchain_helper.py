from langchain_community.utilities import SQLDatabase
import langchain_google_genai
from langchain.chains import create_sql_query_chain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.sql_database.prompt import PROMPT_SUFFIX
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from operator import itemgetter

from few_shots import few_shots

import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env (especially google api key)


def get_few_shot_db_chain():
    db_user = "root"
    db_password = ""
    db_host = "localhost"
    db_name = "atliq_tshirts"

    db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",
                              sample_rows_in_table_info=3)
    
    # Updated to use Google Gemini instead of Palm
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",  # or "gemini-1.5-flash" for faster responses
        google_api_key=os.environ["GOOGLE_API_KEY"],
        temperature=0.1,
        convert_system_message_to_human=True  # Important for compatibility
    )

    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    to_vectorize = [" ".join(example.values()) for example in few_shots]
    vectorstore = Chroma.from_texts(to_vectorize, embeddings, metadatas=few_shots)
    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=2,
    )
    
    mysql_prompt = """You are a MySQL expert. Given an input question, first create a syntactically correct MySQL query to run, then look at the results of the query and return the answer to the input question.
    Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per MySQL. You can order the results to return the most informative data in the database.
    Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in backticks (`) to denote them as delimited identifiers.
    Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
    Pay attention to use CURDATE() function to get the current date, if the question involves "today".
    
    Use the following format:
    
    Question: Question here
    SQLQuery: Query to run with no pre-amble
    SQLResult: Result of the SQLQuery
    Answer: Final answer here
    
    No pre-amble.
    """

    example_prompt = PromptTemplate(
        input_variables=["Question", "SQLQuery", "SQLResult","Answer",],
        template="\nQuestion: {Question}\nSQLQuery: {SQLQuery}\nSQLResult: {SQLResult}\nAnswer: {Answer}",
    )

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix=mysql_prompt,
        suffix=PROMPT_SUFFIX,
        input_variables=["input", "table_info", "top_k"], #These variables are used in the prefix and suffix
    )
    
    # Create the SQL query chain using the modern approach
    write_query = create_sql_query_chain(llm, db, prompt=few_shot_prompt)
    
    # Create a proper Runnable for executing queries
    from langchain_core.runnables import RunnableLambda
    
    def execute_query(inputs):
        if isinstance(inputs, dict):
            query = inputs.get("query", inputs)
        else:
            query = inputs
        result = db.run(query)
        return result
    
    execute_query_runnable = RunnableLambda(execute_query)
    
    # Create answer prompt
    answer_prompt = PromptTemplate.from_template(
        """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

Question: {question}
SQL Query: {query}
SQL Result: {result}
Answer: """
    )

    # Chain that: writes query -> executes query -> formats answer
    chain = (
        RunnablePassthrough.assign(query=write_query).assign(
            result=itemgetter("query") | execute_query_runnable
        )
        | answer_prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

if __name__ == "__main__":
    # Test the chain
    chain = get_few_shot_db_chain()
    print("Chain created successfully!")
    
    # Test a simple query
    try:
        result = chain.invoke({"question": "How many t-shirts do we have in total?"})
        print(f"Test result: {result}")
    except Exception as e:
        print(f"Test failed: {e}")