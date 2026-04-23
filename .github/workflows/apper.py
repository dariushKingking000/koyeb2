# apper.py جدید
import requests
from bs4 import BeautifulSoup
import re

# سرچ گوگل (مثال: "python tutorial")
query = "python tutorial"
url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# استخراج نتایج
results = []
for g in soup.find_all('div', class_='g')[:5]:  # 5 نتیجه اول
    title = g.find('h3')
    link = g.find('a', href=True)
    if title and link:
        results.append(f"{title.text}\n{link['href']}\n{'-'*50}")

content = f"نتایج سرچ: {query}\n\n" + "\n".join(results)

# ذخیره
with open("google_results.txt", "w", encoding="utf-8") as f:
    f.write(content)

print("google_results.txt ساخته شد!")
print(content[:200] + "...")
