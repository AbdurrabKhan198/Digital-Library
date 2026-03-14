import os

templates_dir = r"c:\Users\hp\Desktop\Library\templates"

for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if "Islamic Digital Library" in content:
                content = content.replace("Islamic Digital Library", "Bayt al-Hikmah Online")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

print("Mass replacement complete.")
