# setup LLM
Potrzebne jest pobranie modelu w naszym przypadku będzie to gemma:2b

najpierw trzeba pobrać obraz kontenera
```
docker compose up chat --build
```
następnie trzeba się do niego zalogować i pobrać wybrany model 
```
docker exec -it ollama ollama pull
```