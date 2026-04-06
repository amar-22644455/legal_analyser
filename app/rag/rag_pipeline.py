# src/rag_pipeline.py

from .retriever import Retriever
from openai import OpenAI
from dotenv import load_dotenv
import os
import json


load_dotenv()

COMPARISON_PROMPT_TEMPLATE = """
You are an expert Legal AI comparing two legal documents (e.g., Terms & Conditions, Contracts).

You MUST return ONLY valid JSON. No extra text, no markdown block formatting.

--------------------------------------------------
STRICT RULES:
1. TARGET PARAMETERS: Identify what the user is specifically asking to compare in the USER QUERY (e.g., refunds, liability, data sharing). Base your comparison strictly on those requested parameters.
2. DEFAULT PARAMETERS: If the user's query is generic (e.g., "compare these documents" or "what is the difference"), you MUST evaluate and compare these core legal categories: 
   - Data Privacy & Sharing
   - Liability Limitations
   - Payment & Refund Terms
   - Cancellation & Termination Policies
3. Use ONLY the provided context. Do NOT hallucinate external laws.
4. If Document A has a clause but Document B does not, explicitly state "Not mentioned in Document B" (and vice versa).
5. "evidence" MUST be an array of exact chunk labels (e.g., ["[DocA - Chunk 1]"]).
6. ALWAYS follow the JSON format EXACTLY. DO NOT add explanations outside the JSON object.

--------------------------------------------------
RETURN FORMAT (STRICT JSON):

{{
  "summary": "A concise overview of how the two documents differ fundamentally.",
  "comparison": [
    {{
      "category": "The specific parameter being compared (e.g., Refund Policy, Liability)",
      "document_a": "Summary of Doc A's stance on this parameter",
      "document_b": "Summary of Doc B's stance on this parameter",
      "difference": "The exact material difference between them regarding this parameter"
    }}
  ],
  "risks": [
    {{
      "risk": "Name of the risk (e.g., Unilateral Modification)",
      "docA_severity": "Low | Medium | High | None",
      "docB_severity": "Low | Medium | High | None",
      "explanation": "Why this creates a liability or risk for the user",
      "evidence": ["exact chunk reference 1", "exact chunk reference 2"]
    }}
  ],
  "verdict": "Clear, definitive statement on which document is overall riskier or more restrictive, and why.",
  "final_answer": "Direct answer to the specific user query based on the comparison."
}}

--------------------------------------------------
DOCUMENT A:
{context_a}

DOCUMENT B:
{context_b}

USER QUERY:
{query}

RETURN ONLY JSON:
"""


LEGAL_PROMPT_TEMPLATE = """
You are an expert Legal Risk Analysis AI conducting a strict audit of a legal document.

You MUST return ONLY valid JSON. No extra text, no markdown block formatting.

--------------------------------------------------
STRICT RULES:
1. Use ONLY the provided context. DO NOT assume standard industry practices.
2. If the answer is not in the context, output "Information not found in the provided text."
3. Severity Guidelines: 
   - High: Financial traps, severe privacy violations, loss of legal rights.
   - Medium: Vague terms, difficult cancellation, aggressive data sharing.
   - Low: Standard boilerplate but slightly skewed against the user.
4. "evidence" MUST be an array of chunk labels (e.g., ["[Document - Chunk 2]"]).
5. Output MUST be valid JSON.

--------------------------------------------------
FOCUS ON AUDITING FOR:
- Data collection, selling, & sharing
- Payment / subscription traps & Auto-renewals
- Liability limitations & forced arbitration
- Account suspension / unilateral termination
- Hidden, vague, or predatory clauses

--------------------------------------------------
RETURN FORMAT (STRICT JSON):

{{
  "summary": "Detailed, objective explanation of the document's overall intent and user obligations.",
  "risks": [
    {{
      "title": "Clear, concise risk name",
      "severity": "Low | Medium | High",
      "explanation": "Detailed explanation of how this clause harms or limits the user",
      "user_impact": "Direct real-world consequence for the user",
      "evidence": ["chunk reference"]
    }}
  ],
  "key_clauses": [
    {{
      "clause_title": "e.g., Forced Arbitration",
      "clause_summary": "What the clause actually dictates in plain English"
    }}
  ],
  "final_answer": "Detailed, direct answer to the user query based solely on the text."
}}

--------------------------------------------------
CONTEXT:
{context}

--------------------------------------------------
USER QUERY:
{query}

--------------------------------------------------
RETURN ONLY JSON:
"""


CHAT_PROMPT_TEMPLATE = """
You are a helpful and precise AI answering user questions based strictly on the provided document context.

You MUST return ONLY valid JSON. No extra text, no markdown block formatting.

--------------------------------------------------
STRICT RULES:
1. Use ONLY the provided context. 
2. If the context does not contain the answer, state: "The provided document does not contain information to answer this query."
3. If the query is a simple factual question with no inherent risks, return an empty array [] for "risks".
4. Be helpful, clear, and concise.

--------------------------------------------------
RETURN FORMAT (STRICT JSON):

{{
  "final_answer": "Your detailed, helpful answer to the user query.",
  "risks": [
    {{
      "title": "Name of the risk (if applicable)",
      "severity": "Low | Medium | High"
    }}
  ]
}}

--------------------------------------------------
CONTEXT:
{context}

--------------------------------------------------
USER QUERY:
{query}

--------------------------------------------------
RETURN ONLY JSON:
"""

class RAGPipeline:
    def __init__(self, model="llama-3.1-8b-instant"):
        self.retriever = Retriever()
        self.model = model

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY not found in environment variables.")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    # ==========================================
    # HELPER METHODS (Keeps code DRY)
    # ==========================================
    def _call_llm(self, prompt, max_tokens=1500):
        """Handles the Groq API call and JSON parsing to avoid duplicate code."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a strict legal AI. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=max_tokens,
            )
            answer_text = response.choices[0].message.content.strip()
            
            if answer_text.startswith("```"):
                answer_text = answer_text.strip("`").removeprefix("json").strip()
                
            return json.loads(answer_text)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON output from LLM", "raw_output": answer_text}
        except Exception as e:
            return {"error": str(e)}

    def _build_context(self, results, label, max_chars=4000):
        """Safely builds the context string without exceeding token limits."""
        context_parts = []
        current_length = 0
        source_name = label if label else "Document"

        for i, r in enumerate(results):
            chunk_text = r["chunk"].strip()
            labeled_chunk = f"[{source_name} - Chunk {i+1}]\n{chunk_text}"
            
            if current_length + len(labeled_chunk) > max_chars:
                break
                
            context_parts.append(labeled_chunk)
            current_length += len(labeled_chunk)
            
        return "\n\n".join(context_parts)


    # ==========================================
    # CORE PIPELINE METHODS
    # ==========================================

    def query_document(self, query, target_file=None, is_chat=False, top_k=8):
        """
        FN 1: Use this for standard Q&A chat or searching a single file.
        """
        print(f"Querying {'Global' if not target_file else target_file}...")
        results = self.retriever.retrieve(query, top_k, source_filter=target_file)
        
        if not results:
            return {"answer": {"error": "No relevant context found."}, "sources": []}

        context = self._build_context(results, target_file, max_chars=6000)
        
        prompt = CHAT_PROMPT_TEMPLATE.format(context=context, query=query) if is_chat else LEGAL_PROMPT_TEMPLATE.format(context=context, query=query)
        
        answer_json = self._call_llm(prompt)
        
        return {
            "answer": answer_json,
            "sources": results
        }


    def compare_documents(self, query, file_a, file_b, top_k=8):
        """
        FN 2: Use this ONLY when the user explicitly hits the "Compare" button.
        """
        print(f"Comparing {file_a} vs {file_b}...")
        if not file_a or not file_b:
            return {"answer": {"error": "Comparison requires two files."}, "sources": []}

        results_a = self.retriever.retrieve(query, top_k, source_filter=file_a)
        results_b = self.retriever.retrieve(query, top_k, source_filter=file_b)

        if not results_a or not results_b:
            return {"answer": {"error": "Insufficient data in one or both documents for comparison."}, "sources": []}

        context_a = self._build_context(results_a, file_a)
        context_b = self._build_context(results_b, file_b)

        prompt = COMPARISON_PROMPT_TEMPLATE.format(context_a=context_a, context_b=context_b, query=query)
        
        answer_json = self._call_llm(prompt, max_tokens=1800)

        return {
            "answer": answer_json,
            "sources": {
                "docA": results_a,
                "docB": results_b
            }
        }


    def generate_summaries(self, files: list, top_k=5):
        """
        FN 3: Use this on page load. Pass a list of files (e.g., [file_a] or [file_a, file_b]).
        It returns a dictionary keyed by filename, perfect for your UI display sections.
        """
        print(f"Generating standard summaries for {len(files)} files...")
        
        # We give the LLM a generic prompt to trigger a good overall summary
        summary_query = "Provide a comprehensive summary of this document, extracting key clauses and outlining any potential risks to the user."
        
        ui_summary_data = {}

        for file in files:
            if not file:
                continue
                
            results = self.retriever.retrieve(summary_query, top_k, source_filter=file)
            
            if not results:
                ui_summary_data[file] = {"answer": {"error": "No data found for summary."}, "sources": []}
                continue

            context = self._build_context(results, file)
            prompt = LEGAL_PROMPT_TEMPLATE.format(context=context, query=summary_query)
            
            ui_summary_data[file] = {
                "answer": self._call_llm(prompt),
                "sources": results
            }

        return ui_summary_data