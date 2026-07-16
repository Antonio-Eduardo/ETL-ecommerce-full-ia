# Objetivo

Analise completamente a pasta `assets/`, que contém todos os arquivos CSV do projeto. Com base nessa análise, implemente um pipeline de ETL (Extract, Transform, Load) coerente com os dados disponíveis e documente todas as decisões tomadas.

**Não comece implementando imediatamente. Primeiro entenda os dados.**

---

# Etapa 1 — Análise dos dados

1. Leia todos os arquivos presentes em `assets/`.
2. Identifique:

   * quantidade de arquivos;
   * nome de cada arquivo;
   * número aproximado de registros;
   * colunas existentes;
   * tipos de dados aparentes;
   * presença de valores nulos;
   * valores duplicados;
   * inconsistências de formatação;
   * possíveis chaves primárias;
   * possíveis relacionamentos entre os CSVs.

Ao final dessa etapa, apresente um resumo da estrutura dos dados antes de prosseguir.

---

# Etapa 2 — Entendimento do domínio

Com base apenas nos dados encontrados:

* explique o que cada CSV representa;
* identifique como eles se relacionam;
* monte um modelo conceitual do domínio;
* indique quais tabelas são dimensionais, quais são fatos (caso faça sentido) e quais são apenas auxiliares.

Se alguma hipótese for necessária, documente explicitamente.

---

# Etapa 3 — Planejamento do ETL

Antes de escrever código, descreva o pipeline.

Explique:

## Extract

* Como cada CSV será carregado.
* Quais arquivos fazem parte do pipeline.
* Em qual ordem serão processados.

## Transform

Liste todas as transformações necessárias, por exemplo:

* remoção de duplicados;
* tratamento de nulos;
* padronização de datas;
* padronização de texto;
* normalização de colunas;
* conversão de tipos;
* criação de colunas derivadas;
* validações;
* junções entre arquivos;
* regras de negócio.

Justifique cada transformação.

## Load

Explique:

* qual será o resultado final;
* quais datasets serão produzidos;
* estrutura final dos dados;
* formato de saída.

---

# Etapa 4 — Implementação

Somente após concluir o planejamento:

1. implemente o pipeline;
2. mantenha o código organizado;
3. separe responsabilidades em funções ou módulos;
4. utilize nomes claros;
5. evite código duplicado;
6. mantenha comentários apenas quando agregarem valor.

---

# Etapa 5 — Validação

Após implementar:

* valide se todos os CSVs foram processados;
* confira se nenhuma informação importante foi perdida;
* valide os relacionamentos;
* confirme os tipos das colunas;
* verifique a existência de registros inválidos.

Caso encontre problemas, corrija antes de finalizar.

---

# Etapa 6 — Documentação

Atualize o `README.md`.

Inclua obrigatoriamente:

## Visão geral

* objetivo do projeto;
* descrição dos dados.

## Estrutura dos arquivos

Explique o papel de cada CSV.

## Pipeline ETL

Descreva:

* Extract;
* Transform;
* Load.

## Decisões de modelagem

Explique cada decisão importante tomada durante o desenvolvimento, por exemplo:

* por que determinadas colunas foram removidas;
* por que certos nulos foram tratados de uma determinada maneira;
* por que determinados relacionamentos foram criados;
* por que determinados tipos de dados foram escolhidos;
* justificativa de novas colunas criadas.

Não apenas descreva **o que** foi feito. Explique **por que** foi feito.

## Estrutura final

Mostre como ficou o resultado do ETL.

## Como executar

Documente passo a passo como executar o pipeline.

---

# Etapa 7 — Revisão final

Antes de considerar a tarefa concluída:

* releia todo o código;
* releia o README;
* confirme que toda decisão importante está documentada;
* verifique se existe alguma transformação sem justificativa;
* confirme que o projeto pode ser entendido por alguém que nunca viu os dados anteriormente.

Somente finalize quando todas as etapas acima estiverem completas.
