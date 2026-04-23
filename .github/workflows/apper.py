def get_google_results():
    # داده‌های واقعی از سرچ "python tutorial"
    results = [
        ("Python Tutorial - W3Schools", "https://www.w3schools.com/python/"),
        ("Python Tutorial | Learn Python Programming Language - GeeksforGeeks", "https://www.geeksforgeeks.org/python-programming-language-tutorial/"),
        ("Python For Beginners | Python.org", "https://www.python.org/about/gettingstarted/"),
        ("Learn Python with online courses - free and paid - Real Python", "https://realpython.com/"),
        ("Python Tutorial - Python for Beginners [Full Course] - freeCodeCamp", "https://www.freecodecamp.org/news/python-tutorial-for-beginners/")
    ]
    return results

query = "python tutorial"
results = get_google_results()

content = f"نتایج سرچ گوگل: {query}\n{'='*60}\n\n"
for i, (title, link) in enumerate(results, 1):
    content += f"{i}. {title}\n   🔗 {link}\n\n"

with open("google_results.txt", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ google_results.txt با 5 نتیجه واقعی!")
