from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import openai
import PyPDF2

class PDFChatBot:
    def __init__(self):
        # Initialize the sentence transformer model for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize FAISS for vector search
        self.dimension = 384  # Dimension of the embeddings
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Knowledge base (will store chunks of text from the PDF)
        self.knowledge_base = []
        
        # Set your OpenAI API key
        openai.api_key = 'sk-OOMMKS2qwt1tsKq9BLL7h2hdXNpfY_N-imtNXzWJkqT3BlbkFJ-ZOAM1TlNm1w0zSCOJ2w7ST3p4RSto8FN1X4VufYwA'

    def load_pdf(self, pdf_path):
        """Extract text from the PDF and add it to the knowledge base."""
        try:
            # Extract text from the PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            # Split text into chunks
            chunks = self.split_text_into_chunks(text)
            
            # Add chunks to the knowledge base
            self.knowledge_base.extend(chunks)
            
            # Generate embeddings for the chunks and add them to FAISS
            embeddings = self.model.encode(chunks)
            self.index.add(np.array(embeddings))
            
            return "PDF loaded successfully!"
        except Exception as e:
            return f"Error loading PDF: {str(e)}"

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file."""
        with open(pdf_path, 'rb') as file:
            if hasattr(PyPDF2, 'PdfReader'):  # For PyPDF2 >= 3.0.0
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            else:  # For PyPDF2 < 3.0.0
                reader = PyPDF2.PdfFileReader(file)
                text = ""
                for page_num in range(reader.getNumPages()):
                    page = reader.getPage(page_num)
                    text += page.extract_text()
        return text

    def split_text_into_chunks(self, text, chunk_size=500):
        """Split text into smaller chunks."""
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        return chunks

    def retrieve_relevant_documents(self, query, top_k=3):
        """Retrieve relevant documents from the knowledge base."""
        if not self.knowledge_base:
            return []  # Return an empty list if the knowledge base is empty
    
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Ensure indices are valid
        valid_indices = [i for i in indices[0] if i < len(self.knowledge_base)]
        return [self.knowledge_base[i] for i in valid_indices]
    
    def generate_answer_with_rag(self, question):
        """Generate an answer using RAG."""
        # Retrieve relevant documents
        relevant_docs = self.retrieve_relevant_documents(question)
        context = "\n".join(relevant_docs)
        
        # Define the AI's persona
        system_message = {
            "role": "system",
            "content": "You are Elon Musk, a friendly and knowledgeable STEM tutor. Your goal is to help students understand complex concepts in a simple and engaging way. Always be patient, encouraging, and provide clear explanations. Remember to act as Elon Musk and use your knowledge to help students learn."
        }
        
        # Generate an answer using GPT-3.5 Turbo
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Use GPT-3.5 Turbo
                messages=[
                    system_message,  # Add the persona
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            return f"Error generating answer with OpenAI: {str(e)}"

    def ask_question(self, question):
        """Ask a question and get an answer using RAG."""
        try:
            return self.generate_answer_with_rag(question)
        except Exception as e:
            return f"Error generating answer: {str(e)}"