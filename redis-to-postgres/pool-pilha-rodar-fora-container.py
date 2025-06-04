import time
import redis
import psycopg2
import json
from datetime import datetime
from psycopg2 import Error

# Configurações de conexão
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_ANSWER_PATTERN = 'answer:*'  # Padrão para buscar todas as respostas
REDIS_QUESTION_PATTERN = 'question:*'  # Padrão para buscar todas as questões

PG_HOST = 'localhost'
PG_PORT = 5432
PG_DB = 'dw'
PG_USER = 'user'
PG_PASSWORD = 'senhaForte2025'
PG_ANSWER_TABLE = 'redis_answers'  # Tabela para respostas
PG_QUESTION_TABLE = 'redis_questions'  # Tabela para questões

def create_tables_if_not_exist(conn):
    try:
        with conn.cursor() as cur:
            # Tabela de respostas
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {PG_ANSWER_TABLE} (
                    id SERIAL PRIMARY KEY,
                    question_id INTEGER,
                    alternativa_escolhida VARCHAR,
                    datahora TIMESTAMP,
                    usuario VARCHAR,
                    nro_tentativa INTEGER,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Tabela de questões
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {PG_QUESTION_TABLE} (
                    id SERIAL PRIMARY KEY,
                    question_id INTEGER UNIQUE,
                    question_text TEXT,
                    alternativa_a TEXT,
                    alternativa_b TEXT,
                    alternativa_c TEXT,
                    alternativa_d TEXT,
                    alternativa_correta TEXT,
                    dificuldade TEXT,
                    assunto TEXT,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.commit()
    except Error as e:
        print(f"Erro ao criar tabelas: {str(e)}")
        conn.rollback()
        raise

def convert_date_format(date_str):
    try:
        # Converte a data do formato DD/MM/YYYY HH:MM para YYYY-MM-DD HH:MM:SS
        dt = datetime.strptime(date_str, '%d/%m/%Y %H:%M')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        print(f"Erro ao converter data {date_str}: {str(e)}")
        return None

def insert_answer_into_postgres(conn, answer_data):
    try:
        # Converte a data para o formato correto
        formatted_date = convert_date_format(answer_data['datahora'])
        if not formatted_date:
            print(f"Data inválida: {answer_data['datahora']}")
            return False

        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {PG_ANSWER_TABLE} 
                (question_id, alternativa_escolhida, datahora, usuario, nro_tentativa)
                VALUES (%s, %s, %s, %s, %s);
            """, (
                answer_data['question_id'],
                answer_data['alternativa_escolhida'],
                formatted_date,
                answer_data['usuario'],
                answer_data['nro_tentativa']
            ))
        conn.commit()
        return True
    except Error as e:
        print(f"Erro ao inserir resposta: {str(e)}")
        conn.rollback()
        return False

def insert_question_into_postgres(conn, question_data):
    try:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {PG_QUESTION_TABLE} 
                (question_id, question_text, alternativa_a, alternativa_b, 
                alternativa_c, alternativa_d, alternativa_correta, 
                dificuldade, assunto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (question_id) DO UPDATE SET
                    question_text = EXCLUDED.question_text,
                    alternativa_a = EXCLUDED.alternativa_a,
                    alternativa_b = EXCLUDED.alternativa_b,
                    alternativa_c = EXCLUDED.alternativa_c,
                    alternativa_d = EXCLUDED.alternativa_d,
                    alternativa_correta = EXCLUDED.alternativa_correta,
                    dificuldade = EXCLUDED.dificuldade,
                    assunto = EXCLUDED.assunto;
            """, (
                question_data['question_id'],
                question_data['question_text'],
                question_data['alternativa_a'],
                question_data['alternativa_b'],
                question_data['alternativa_c'],
                question_data['alternativa_d'],
                question_data['alternativa_correta'],
                question_data['dificuldade'],
                question_data['assunto']
            ))
        conn.commit()
        return True
    except Error as e:
        print(f"Erro ao inserir questão: {str(e)}")
        conn.rollback()
        return False

def process_redis_data(r, pg_conn):
    # Processa respostas
    answer_keys = r.keys(REDIS_ANSWER_PATTERN)
    for key in answer_keys:
        try:
            answer_data = r.hgetall(key)
            if answer_data:
                answer_data['nro_tentativa'] = int(answer_data['nro_tentativa'])
                if insert_answer_into_postgres(pg_conn, answer_data):
                    r.delete(key)
                    print(f"Processada e removida a resposta: {key}")
                else:
                    print(f"Falha ao inserir resposta {key} no PostgreSQL")
        except Exception as e:
            print(f"Erro ao processar resposta {key}: {str(e)}")
            try:
                pg_conn.rollback()
            except:
                pass

    # Processa questões
    question_keys = r.keys(REDIS_QUESTION_PATTERN)
    for key in question_keys:
        try:
            question_data = r.hgetall(key)
            if question_data:
                question_id = key.split(':')[1]
                question_data['question_id'] = int(question_id)
                if insert_question_into_postgres(pg_conn, question_data):
                    r.delete(key)
                    print(f"Processada e removida a questão: {key}")
                else:
                    print(f"Falha ao inserir questão {key} no PostgreSQL")
        except Exception as e:
            print(f"Erro ao processar questão {key}: {str(e)}")
            try:
                pg_conn.rollback()
            except:
                pass

def ensure_postgres_connection(pg_conn):
    try:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except:
        return False

def main():
    while True:
        try:
            # Conexão com Redis
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            
            # Conexão com Postgres
            pg_conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                dbname=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD
            )

            create_tables_if_not_exist(pg_conn)

            print("Iniciando loop de transferência de dados para o Postgres...")
            while True:
                if not ensure_postgres_connection(pg_conn):
                    print("Conexão com PostgreSQL perdida. Reconectando...")
                    break
                    
                process_redis_data(r, pg_conn)
                time.sleep(5)  # Aguarda 5 segundos entre cada iteração do loop

        except Exception as e:
            print(f"Erro no loop principal: {str(e)}")
            time.sleep(5)  # Aguarda antes de tentar reconectar
        finally:
            try:
                pg_conn.close()
            except:
                pass

if __name__ == "__main__":
    main()