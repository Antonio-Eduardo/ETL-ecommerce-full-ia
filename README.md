# ETL E-commerce

## Visão geral

**Objetivo:** transformar o conjunto de dados brutos de um marketplace brasileiro de e-commerce (estilo Olist) em datasets limpos e modelados, prontos para análise, seguindo um pipeline ETL (Extract, Transform, Load).

**Descrição dos dados:** 8 arquivos CSV em `assets/`, totalizando ~99 mil pedidos, ~112 mil itens de pedido, ~33 mil produtos, ~3 mil vendedores e ~1 milhão de registros de geolocalização. Os dados cobrem o ciclo completo de um pedido: cliente, produto, vendedor, pagamento, entrega e avaliação (review).

## Estrutura dos arquivos

| Arquivo | Papel |
|---|---|
| `olist_customers_dataset.csv` | Cliente e sua localização de entrega. `customer_id` é um ID por-pedido; `customer_unique_id` identifica a pessoa física/jurídica real através de múltiplos pedidos. |
| `olist_orders_dataset.csv` | O pedido: status e timestamps do ciclo de vida (compra, aprovação, postagem, entrega, prazo estimado). |
| `olist_order_items_dataset.csv` | Itens de um pedido (grão fino): produto, vendedor, preço e frete. Um pedido pode ter vários itens de vários vendedores. |
| `olist_order_payments_dataset.csv` | Forma(s) de pagamento de um pedido (pode haver mais de um método/parcela por pedido). |
| `olist_order_reviews_dataset.csv` | Avaliação do cliente sobre o pedido (nota + comentário opcional). |
| `olist_products_dataset.csv` | Catálogo de produtos: categoria, dimensões, peso. |
| `olist_sellers_dataset.csv` | Vendedores e sua localização. |
| `olist_geolocation_dataset.csv` | Tabela de apoio: CEP → lat/lng/cidade/estado (múltiplas coordenadas por prefixo de CEP). |

### Modelo conceitual

```
customers ──┐
            │
sellers ────┼──> order_items ──> orders (pedido) ──> order_payments
            │                         │
products ───┘                         └──> order_reviews

geolocation (dimensão auxiliar, relacionada por zip_code_prefix)
```

- **Dimensões:** `customers`, `products`, `sellers`, `geolocation`.
- **Fatos:** `order_items` (grão: item de pedido — métricas de preço/frete), `orders`/`order_payments` (grão: pedido/pagamento).
- **Satélite:** `order_reviews` (evento 1:N em relação a `orders`).

## Pipeline ETL

### Extract (`etl/extract.py`)
Leitura dos 8 CSVs com pandas. IDs e códigos (customer_id, order_id, product_id, seller_id, review_id, zip_code_prefix) são lidos como **string**, não numérico — preserva zeros à esquerda em CEPs e evita operações aritméticas indevidas em identificadores. Ordem de carga: dimensões (customers, sellers, products, geolocation) antes dos fatos (orders, order_items, order_payments, order_reviews), refletindo a dependência lógica do modelo.

### Transform (`etl/transform.py`)
| Transformação | Onde | Por quê |
|---|---|---|
| Remoção de duplicados | `geolocation` (261.831 linhas) | Coordenadas repetidas não agregam informação e distorceriam a agregação por CEP. |
| Padronização de texto | cidades (title case), estados (upper) | Variações de capitalização (`sao paulo` vs `São Paulo`) não são diferenças reais de dado. |
| Padronização de datas | todas as colunas `*_timestamp`/`*_date` | Necessário para calcular métricas de prazo (SLA de entrega, tempo de aprovação). |
| Nulos em `orders` (approved_at, delivered_carrier_date, delivered_customer_date) | mantidos como nulo real | Nulo aqui significa que a etapa do pedido não ocorreu (ex.: cancelado antes da aprovação); imputar mascararia o status real. |
| Nulos em `order_reviews` (comentário) | mantidos + flag `has_comment` | Ausência de comentário é comportamento normal do usuário, não erro de coleta. |
| Nulos em `products.product_category_name` (610) | preenchido com `"outros"` | Vira categoria explícita de negócio em vez de nulo silencioso. |
| Nulos em dimensões físicas de produto (2 registros) | mantidos nulos | Volume irrelevante (2 de 32.951); imputar distorceria estatísticas de peso/tamanho. |
| Conversão de tipos | zip codes com zero-padding de 5 dígitos | CEP não é grandeza numérica. |
| Colunas derivadas | `delivery_delay_days`, `approval_time_hours` (orders); `total_item_value` (order_items) | Métricas de negócio recorrentes (SLA, ticket) materializadas para evitar recomputação em toda análise. |
| Agregação | `geolocation` agregada por CEP (média lat/lng, moda cidade/estado) | A tabela bruta tem N coordenadas por CEP; o uso pretendido é localização aproximada, não endereço exato. |
| Agregação | `order_payments` somado por pedido (pode ter N parcelas/métodos) | `fact_orders` tem grão de 1 linha por pedido; a soma representa o valor total pago. |
| Deduplicação | `order_reviews` — mantido apenas o review mais recente por pedido (551 pedidos tinham mais de um) | Grão de `fact_orders` é 1 linha por pedido; o review mais recente reflete a avaliação final do cliente. |
| Junção | `fact_order_items` = order_items + orders + customers + products + sellers | Todas as FKs foram validadas com cobertura de 100% na etapa de análise — junção sem risco de perda de linhas (`inner`/`left` conforme o caso). |

### Load (`etl/load.py`)
Saída em **Parquet** (não CSV) em `output/`, por ser colunar, tipado (preserva datas e tipos numéricos sem re-parsing) e mais compacto. Datasets produzidos:

- `dim_customers.parquet`, `dim_sellers.parquet`, `dim_products.parquet`, `dim_geolocation.parquet`
- `fact_orders.parquet` — grão pedido, com prazo de entrega, tempo de aprovação, pagamento total, review mais recente.
- `fact_order_items.parquet` — grão item, para análises por produto/vendedor.

## Decisões de modelagem

- **`customer_id` vs `customer_unique_id`:** mantivemos `customer_id` como chave de junção padrão (é como o dataset foi desenhado — 1 ID por pedido), preservando `customer_unique_id` na dimensão para quem quiser analisar recorrência de clientes.
- **Pedidos sem item (775) e sem pagamento (1) não foram descartados** de `fact_orders`: são pedidos operacionalmente órfãos (provavelmente cancelados cedo no funil), e removê-los esconderia informação real sobre o funil de vendas. Eles simplesmente não aparecem em `fact_order_items` (junção inner, pois sem item não há métrica de item a analisar).
- **CEPs como string com zero-padding:** decisão para evitar a perda silenciosa de zeros à esquerda que ocorre quando pandas infere `int64` na leitura — um bug comum e difícil de notar neste tipo de dataset.
- **`order_status` não foi filtrado nem teve linhas removidas:** decidir o que é "pedido válido para receita" (ex.: excluir `canceled`) é responsabilidade de quem consome os dados analiticamente, não do ETL — o papel do ETL é entregar dados limpos e completos, não pré-aplicar regras de negócio de terceiros.
- **Parquet em vez de CSV na saída:** CSV perderia tipos (datas voltariam a ser string, decimais poderiam ganhar erro de precisão); Parquet resolve isso e é mais eficiente para leitura por ferramentas de análise (pandas, Spark, DuckDB).

## Estrutura final

```
output/
├── dim_customers.parquet      (99.441 linhas, 5 colunas)
├── dim_sellers.parquet        (3.095 linhas, 4 colunas)
├── dim_products.parquet       (32.951 linhas, 9 colunas)
├── dim_geolocation.parquet    (19.015 linhas, 5 colunas — 1 por CEP)
├── fact_orders.parquet        (99.441 linhas, 15 colunas)
└── fact_order_items.parquet   (112.650 linhas, 16 colunas)
```

Validado: nenhuma linha órfã (100% de integridade referencial), nenhuma chave duplicada, nenhum registro com preço/frete negativo, todos os tipos convertidos corretamente (datas como `datetime64`, IDs como `string`).

## Como executar

Pré-requisitos: Python 3.10+, `pandas`, `pyarrow`.

```bash
pip install pandas pyarrow
```

A partir da raiz do projeto:

```bash
python -m etl.pipeline
```

Isso lê os CSVs de `assets/`, aplica todas as transformações e grava os 6 arquivos Parquet em `output/`. O script imprime a contagem de linhas/colunas de cada dataset gerado ao final.
