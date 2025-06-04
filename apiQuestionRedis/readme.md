# 🚀 Projeto API Quiz (Python + Redis)

API desenvolvida com **FastAPI** para gerenciar questões e respostas de quiz, utilizando o banco de dados em memória **Redis**.

---

## ⚙️ Configuração

1. **Suba um container Redis**  
   ```sh
   docker run -d --name meu-redis -p 6379:6379 redis
   ```

2. **Instale as dependências**  
   ```sh
   pip install fastapi uvicorn redis
   ```

3. **Execute a aplicação**  
   ```sh
   uvicorn main:app --reload --log-level info
   ```

---

## 🧪 Testando a API

Acesse no navegador: [http://127.0.0.1:8000](http://127.0.0.1:8000)

- Para acessar a documentação interativa (Swagger):  
  [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

![Swagger UI](https://github.com/commithouse/apiQuestionRedis/blob/main/images/image.png?raw=true)

---

## 🖱️ Como usar

Você pode utilizar a própria página do Swagger (`/docs`), clicar em **"Try it out"** e inserir os dados dos parâmetros e body diretamente na interface.

---

## 📝 Carga de Dados Fake

Para popular o banco com dados de exemplo, utilize os métodos abaixo e envie no body o conteúdo dos arquivos `.json` da pasta `carga-dados-fake` deste repositório:

- **POST `/questions`**: cria uma lista de questões
- **POST `/answers`**: cria uma lista de respostas

---

## 🧹 Limpeza do Ambiente

Para remover todos os dados do Redis, utilize as rotas via Swagger:

- **DELETE `/questions`**: remove todas as questões
- **DELETE `/answers`**: remove todas as respostas

Para remover o container Redis criado, execute:

```sh
docker rm -f meu-redis
```

---

## 📚 Referências

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Documentation](https://redis.io/documentation/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

---
