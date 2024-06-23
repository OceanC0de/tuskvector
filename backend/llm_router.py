from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import LLMQueryRequest, LLMQueryResponse, SimilaritySearchRequest, SimilaritySearchResponse
from openai import OpenAI
import os
from dotenv import load_dotenv
from embeddings_router import similarity_search

load_dotenv()

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/query", response_model=LLMQueryResponse)
async def llm_query(query_request: LLMQueryRequest, db: Session = Depends(get_db)):
    try:
        similarity_request = SimilaritySearchRequest(text=query_request.text)
        similarity_response = await similarity_search(similarity_request, db)
        context = similarity_response.result

        messages = [
            {"role": "system", "content": f"You are a helpful assistant. Use the following facts to inform your responses, but only if they match the context of the user prompt:\n\n{context}"},
            {"role": "user", "content": query_request.text}
        ]

        llm_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )

        return LLMQueryResponse(response=llm_response.choices[0].message.content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")