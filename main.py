from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("O_R_API"),
)
context="you are a helpful creer guidence insturctor your job is to gentrate a one page ATS frindly resume from provided information:"

with open('EmaadAkhter/README.md','r',encoding='utf-8') as file:
    read_content = file.read()

test_context=read_content


completion = client.chat.completions.create(
  model="mistralai/mistral-small-3.2-24b-instruct:free",
  max_tokens=1000,
  messages=[
              {
                "role":"system",
                "content": f"{context}\n{read_content}"
              },
              {
                "role": "user",
                "content": "genrate a resume for me i am a 2nd year engineering student based on the context "
              }
            ]
)
print(completion.choices[0].message.content)