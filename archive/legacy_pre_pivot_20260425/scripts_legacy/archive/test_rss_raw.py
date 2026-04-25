import requests

url = "https://www.fiercepharma.com/rss/xml"
response = requests.get(url, timeout=10)

# Afficher les 2000 premiers caractères
print(response.text[:2000])
