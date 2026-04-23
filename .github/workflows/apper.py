import requests
import json

query = "python tutorial"
url = f"https://serpapi.com/search.json?engine=google&q={query}&api_key=demo"

response = requests.get(url)
data = response.json()

results = []
for result in data.get('organic_results', [])[:5]:
    results.append(f"عنوان: {result['title']}")
    results.append(f"لینک: {result['link']}")
    results.append("-" * 50)

content = f"نتایج گوگل: {query}\n\n" + "\n".join(results)

with open("google_results.txt", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ google_results.txt ذخیره شد!")
