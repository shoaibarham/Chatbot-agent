import os
import sqlite3
from typing import Dict, List, Union

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from prompt import system_prompt


class DatabaseAgent:
    def __init__(self, db_path: str = 'gtfs.db', model_name: str = 'gemini-2.0-flash'):
        """
        Initialize the DatabaseAgent with a specified database and LLM.
        
            :param db_path: Path to the SQLite database
            :param model_name: Google Gemini model to use
        """
        
        self.db_path = db_path

        self.chat_histories: Dict[str, List[Union[HumanMessage, AIMessage, SystemMessage]]] = {}
        
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1 , api_key="")
        
        # This can be used to get the latest DB CONTEXT and merge with the system PROMPT
        # self.database_context = self.get_db_context()
        
        self.system_prompt = system_prompt
        
        
        self.sql_tool = Tool(
            name="sql_query_tool",
            func=self.run_sql_query,
            description="Execute SQL queries on the GTFS database. Input should be a valid SQL query."
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                self.system_prompt
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = create_tool_calling_agent(
            llm=self.llm, 
            tools=[self.sql_tool], 
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=[self.sql_tool], 
            # verbose=True
        )
    
    def run_sql_query(self, query: str) -> str:
        """
        Execute an SQL query against the database with enhanced error handling and safety.
        
        :param query: SQL query to execute
        :return: Query results or error message
        """
        forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE']
        if any(keyword in query.upper() for keyword in forbidden_keywords):
            return "Error: Potentially dangerous SQL query detected."
        
        try:
            print(f"Executing query: {query}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
                    
            conn.close()
            
            if not rows:
                return "No results found."
            
            result_str = "Columns: " + ", ".join(columns) + "\n"
            result_str += "\n".join([str(row) for row in rows])
            
            print(f"Result: {result_str}")
            return result_str
        
        except sqlite3.Error as e:
            return f"Database error: {e}"
        except Exception as e:
            return f"Unexpected error executing query: {e}"
    
    def query(self, input_text: str, session_id: str = 'default') -> str:
        """
        Main method to process user queries with conversational context.
            :param input_text: User's input query
            :param session_id: Unique identifier for the chat session
            :return: Agent's response
        """
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = []
        
        session_history = self.chat_histories[session_id]
        
        result = self.agent_executor.invoke({
            "input": input_text,
            "chat_history": session_history
        })
        
        session_history.append(HumanMessage(content=input_text))
        session_history.append(AIMessage(content=result['output']))
            
        return result['output']
    
    def get_db_context(self):
        """
        Connects to the SQLite database specified by db_path and retrieves
        all table names along with their column names.

            :param db_path: Path to the SQLite database file.
            :return: A dictionary where keys are table names and values are lists of column names.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        db_context = {}
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                if table_name == "sqlite_sequence":
                    continue

                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                column_names = [column[1] for column in columns]

                db_context[table_name] = column_names

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()

        db_context_str = str(db_context)
        print("db_context : " ,db_context_str)
        
        return db_context_str


def main():
    agent = DatabaseAgent(db_path='gtfs.db', model_name='gemini-2.0-flash')
    
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break 
        print("Agent:", agent.query(user_input))

if __name__ == "__main__":
    main()