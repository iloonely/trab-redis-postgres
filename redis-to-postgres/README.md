# IMDB Redis-to-Postgres 🚀

Este projeto demonstra como usar RedisGears para monitorar chaves no Redis e transferir dados para uma tabela no PostgreSQL usando um script Python externo.

## 🛠️ Pré-requisitos

- [Docker](https://www.docker.com/) 🐳
- [Docker Compose](https://docs.docker.com/compose/) ⚙️
- Python 3.8+ 🐍
- `pip` (gerenciador de pacotes Python) 📦

## ▶️ Como subir o ambiente

1. **Suba os containers RedisGears e Postgres:**

   ```sh
   docker-compose up -d
   ```

   Isso irá:
   - Subir o RedisGears na porta 6379 🟥
   - Subir o Postgres na porta 5432 🟦
   - Montar automaticamente o script `registra-gear-interno.py` no RedisGears 📄

2. **Registre manualmente o script RedisGears:**

   ```sh
   # entre no container
   docker exec -it redis-gears bash
   ```

   ```sh
   # registra o codigo python no gear
   redis-cli RG.PYEXECUTE "$(cat /tmp/registra-gear-interno.py)"
   ```

   ```sh
   # sai do container
   exit
   ```

3. **Instale as dependências Python:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Execute o script Python externo para transferir dados do Redis para o Postgres:**

   ```sh
   python pool-pilha-rodar-fora-container.py
   ```

   O script irá:
   - Criar a tabela `redis_history` no Postgres se ela não existir 🗄️
   - A cada 5 segundos, buscar dados na lista `minha_pilha` do Redis ⏳
   - Inserir os dados encontrados na tabela `redis_history` ➡️ 🗃️

5. **Crie os registros no Redis através do RedisInsight ou redis-cli:**

   ```sh
   set pessoa:01 daniel
   ```

6. **Acesse o Postgres via sua IDE de preferência (DBeaver, por exemplo) 🖥️**
   
   Rode a consulta para ver os registros entrando:
   ```sql
   select * from redis_history;
   ```

## 💡 Observações

- Para testar, insira chaves no Redis com o padrão `pessoa:*` e veja os dados sendo processados automaticamente.
- Os dados processados ficam salvos na tabela `redis_history` no banco `dw` do Postgres.
- O script Python pode ser interrompido e reiniciado a qualquer momento.

## 🧹 Como limpar o ambiente

Para remover todos os containers, volumes e dados criados pelo projeto, execute:

```sh
docker-compose down -v
```

Isso irá:
- Parar e remover os containers 🛑
- Remover os volumes persistentes (`redis_data` e `postgres_data`) 🗑️
- Apagar todos os dados do Redis e do Postgres criados durante os testes

Se quiser remover apenas os containers (mantendo os dados), use:

```sh
docker-compose down
```

### 🗑️ Como limpar a tabela do Postgres

Se quiser apenas apagar os dados da tabela `redis_history` no banco Postgres, execute:

```sh
DELETE FROM public.redis_history WHERE 1=1;
```

Isso irá remover todos os registros da tabela, mas manterá a estrutura da tabela no banco de dados.