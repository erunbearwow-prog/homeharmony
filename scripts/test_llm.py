# test_llm.py
import os
import sys
from openai import OpenAI

# Выберите вариант, с которого хотите начать
USE_OLLAMA = True  # Поставьте False, если хотите использовать OpenAI

if USE_OLLAMA:
    import ollama
    
    def ask_llm(prompt):
        """Отправляет запрос локальной модели Ollama"""
        response = ollama.chat(
            model='qwen2.5:7b',
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
else:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def ask_llm(prompt):
        """Отправляет запрос GPT через API"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_prompt},
                      {'role': 'system', 'content': system_prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content

# Тестируем
if __name__ == "__main__":
    system_prompt = 'Ты - опытный шеф-повар.'
    user_prompt = "Назови три классических ингредиента для борща."
    print(f"Вопрос: {user_prompt}")
    print(f"Ответ LLM: {ask_llm(user_prompt)}")