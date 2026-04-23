# apper.py - جایگزین کن
import requests
from bs4 import BeautifulSoup

query = "python tutorial"
url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"

headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

results = []
for result in soup.select('.result__title a')[:5]:
    title = result.get_text()
    link = result.get('href')
    results.append(f"{title}\n{link}\n{'-'*50}")

content = f"نتایج سرچ: {query}\n\n" + "\n".join(results)

with open("search_results.txt", "w", encoding="utf-8") as f:
    f.write(content)

print("search_results.txt OK!")
