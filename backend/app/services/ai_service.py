import google.generativeai as genai
from app.core.config import settings

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def solve_with_rag(self, user_query: str, image_data: bytes = None, context: str = ""):
        """
        Combines RAG context, optional image, and user query to get a solution from Gemini.
        """
        prompt = f"""
        System Instruction: You are EduSolve AI, a helpful study assistant. 
        Solve the following problem accurately using the provided context.
        
        Context: {context}
        
        User Instruction: {user_query}
        
        Output format (JSON):
        {{
            "concept": "Academic concept name",
            "steps": ["Step 1 description", "Step 2 description..."],
            "final_answer": "The final answer with LaTeX formatting"
        }}
        """
        
        # Implementation for image + text or text only
        # This is high-level logic for the boilerplate
        return prompt

ai_service = AIService()
