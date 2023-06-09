import requests

url = f"http://www.omdbapi.com/?t=zootopia&apikey=e51dcd6"

#http://img.omdbapi.com/?apikey=[yourkey]&

response = requests.get(url)

print(response)