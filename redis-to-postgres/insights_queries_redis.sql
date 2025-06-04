--alternativas mais votadas por questão
SELECT
    q.question_id,
    q.question_text,
    a.alternativa_escolhida,
    COUNT(*) as total_votos,
    ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER (PARTITION BY q.question_id) * 100, 2) as percentual_votos
FROM redis_questions q
JOIN redis_answers a ON q.question_id = a.question_id
GROUP BY q.question_id, q.question_text, a.alternativa_escolhida
ORDER BY q.question_id, total_votos DESC;

--questões com maior indice de asserto
SELECT
    q.question_id,
    q.question_text,
    q.dificuldade,
    q.assunto,
    COUNT(a.id) as total_respostas,
    COUNT(CASE WHEN a.alternativa_escolhida = q.alternativa_correta THEN 1 END) as acertos,
    ROUND(COUNT(CASE WHEN a.alternativa_escolhida = q.alternativa_correta THEN 1 END)::numeric / COUNT(a.id) * 100, 2) as taxa_acerto
FROM redis_questions q
LEFT JOIN redis_answers a ON q.question_id = a.question_id
GROUP BY q.question_id, q.question_text, q.dificuldade, q.assunto
HAVING COUNT(a.id) > 0
ORDER BY taxa_acerto DESC;

--questoes com mais menos votos validos
SELECT
    q.question_id,
    q.question_text,
    q.dificuldade,
    q.assunto,
    COUNT(a.id) as total_respostas,
    COUNT(DISTINCT a.usuario) as usuarios_responderam,
    ROUND(COUNT(DISTINCT a.usuario)::numeric / (
        SELECT COUNT(DISTINCT usuario) FROM redis_answers
    ) * 100, 2) as percentual_participacao
FROM redis_questions q
LEFT JOIN redis_answers a ON q.question_id = a.question_id
GROUP BY q.question_id, q.question_text, q.dificuldade, q.assunto
ORDER BY total_respostas ASC;

--tempo medio de resposta por questao
WITH tempo_resposta AS (
    SELECT
        a.question_id,
        a.usuario,
        a.nro_tentativa,
        a.datahora,
        LAG(a.datahora) OVER (PARTITION BY a.question_id, a.usuario ORDER BY a.nro_tentativa) as tempo_inicio,
        EXTRACT(EPOCH FROM (a.datahora - LAG(a.datahora) OVER (PARTITION BY a.question_id, a.usuario ORDER BY a.nro_tentativa))) as segundos_resposta
    FROM redis_answers a
)
SELECT
    q.question_id,
    q.question_text,
    q.dificuldade,
    ROUND(AVG(tr.segundos_resposta), 2) as tempo_medio_segundos,
    ROUND(AVG(tr.segundos_resposta)/60, 2) as tempo_medio_minutos
FROM redis_questions q
JOIN tempo_resposta tr ON q.question_id = tr.question_id
WHERE tr.segundos_resposta IS NOT NULL
GROUP BY q.question_id, q.question_text, q.dificuldade
ORDER BY tempo_medio_segundos;

--rank final dos alunos
WITH tempo_resposta AS (
    SELECT
        a.question_id,
        a.usuario,
        a.nro_tentativa,
        a.datahora,
        LAG(a.datahora) OVER (PARTITION BY a.question_id, a.usuario ORDER BY a.nro_tentativa) as tempo_inicio,
        EXTRACT(EPOCH FROM (a.datahora - LAG(a.datahora) OVER (PARTITION BY a.question_id, a.usuario ORDER BY a.nro_tentativa))) as segundos_resposta
    FROM redis_answers a
),
metricas_alunos AS (
    SELECT
        a.usuario,
        COUNT(a.id) as total_respostas,
        COUNT(CASE WHEN a.alternativa_escolhida = q.alternativa_correta THEN 1 END) as acertos,
        ROUND(COUNT(CASE WHEN a.alternativa_escolhida = q.alternativa_correta THEN 1 END)::numeric / COUNT(a.id) * 100, 2) as taxa_acerto,
        ROUND(AVG(tr.segundos_resposta), 2) as tempo_medio_resposta
    FROM redis_answers a
    JOIN redis_questions q ON a.question_id = q.question_id
    JOIN tempo_resposta tr ON a.question_id = tr.question_id AND a.usuario = tr.usuario AND a.nro_tentativa = tr.nro_tentativa
    WHERE tr.segundos_resposta IS NOT NULL
    GROUP BY a.usuario
)
SELECT
    usuario,
    total_respostas,
    acertos,
    taxa_acerto,
    ROUND(tempo_medio_resposta, 2) as tempo_medio_segundos,
    ROUND(tempo_medio_resposta/60, 2) as tempo_medio_minutos,
    ROW_NUMBER() OVER (ORDER BY taxa_acerto DESC, tempo_medio_resposta ASC) as rank_final
FROM metricas_alunos
ORDER BY rank_final;

--alunos com maior acerto
SELECT
    a.usuario,
    COUNT(a.id) as total_respostas,
    COUNT(CASE WHEN a.alternativa_escolhida = q.alternativa_correta THEN 1 END) as acertos,
    ROUND(COUNT(CASE WHEN a.alternativa_escolhida = q.alternativa_correta THEN 1 END)::numeric / COUNT(a.id) * 100, 2) as taxa_acerto,
    ROW_NUMBER() OVER (ORDER BY COUNT(CASE WHEN a.alternativa_escolhida = q.alternativa_correta THEN 1 END)::numeric / COUNT(a.id) DESC) as rank_acertos
FROM redis_answers a
JOIN redis_questions q ON a.question_id = q.question_id
GROUP BY a.usuario
ORDER BY taxa_acerto DESC;

--alunos mais rapidos
WITH tempo_resposta AS (
    SELECT
        a.usuario,
        a.question_id,
        a.nro_tentativa,
        a.datahora,
        LAG(a.datahora) OVER (PARTITION BY a.question_id, a.usuario ORDER BY a.nro_tentativa) as tempo_inicio,
        EXTRACT(EPOCH FROM (a.datahora - LAG(a.datahora) OVER (PARTITION BY a.question_id, a.usuario ORDER BY a.nro_tentativa))) as segundos_resposta
    FROM redis_answers a
)
SELECT
    usuario,
    COUNT(DISTINCT question_id) as total_questoes,
    ROUND(AVG(segundos_resposta), 2) as tempo_medio_segundos,
    ROUND(AVG(segundos_resposta)/60, 2) as tempo_medio_minutos,
    ROW_NUMBER() OVER (ORDER BY AVG(segundos_resposta)) as rank_velocidade
FROM tempo_resposta
WHERE segundos_resposta IS NOT NULL
GROUP BY usuario
ORDER BY tempo_medio_segundos;