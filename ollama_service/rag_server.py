from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"  # default ollama endpoint
MODEL_NAME = "gemma3:12b"  

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXAMPLE_QUESTIONS = [
    "Who is most likely to start a conspiracy theory?",
    "Who is most likely to lead a rebellion?",
    "Who is most likely to survive a zombie apocalypse?",
    "Who is most likely to betray the group for a snack?",
]


@app.get("/question")
async def question():
    """
    Return: { "id": str, "text": str }
    """
    # SIMPLE VERSION: just ask the model for one question, seeded with examples
    prompt = (
        "You are a party game engine. Generate one fun 'Who is most likely to...' "
        "question for a group of friends. Do not repeat exactly these, use them only as style examples:\n"
        + "\n".join(f"- {q}" for q in EXAMPLE_QUESTIONS)
        + "\nReturn ONLY the question text, no extra words."
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["message"]["content"].strip()
    except Exception as e:
        print("ollama error", e)
        text = "Who is most likely to survive a zombie apocalypse?"

    qid = "q1"  # you can later make this unique
    return {"id": qid, "text": text}
