from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PDFChatBot:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0.7)
        self.chat_history = []
        
    def load_pdf(self, pdf_path):
        """Load and process a PDF file"""
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        splits = text_splitter.split_documents(pages)
        
        # Create vector store
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings
        )
        
        # Create conversation chain
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(),
            return_source_documents=True
        )
        
        return f"Processed PDF with {len(splits)} text chunks"
    
    def ask_question(self, question):
        """Ask a question about the loaded PDF"""
        if not hasattr(self, 'qa_chain'):
            return "Please load a PDF first!"
            
        result = self.qa_chain({
            "question": question,
            "chat_history": self.chat_history
        })
        
        # Update chat history
        self.chat_history.append((question, result["answer"]))
        
        return result["answer"] 