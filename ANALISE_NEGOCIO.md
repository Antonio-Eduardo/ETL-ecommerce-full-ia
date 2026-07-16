# Análise de Negócio — Insights a partir dos dados processados

Análise feita sobre os datasets finais em `output/*.parquet` (pós-ETL). Os achados abaixo estão **rankeados por criticidade** para a tomada de decisão — do que exige ação imediata ao que é apenas complementar/exploratório. Cada item traz o número, a leitura de negócio e a fonte (dataset/coluna).

---

## 🔴 Críticos — impacto direto em receita ou risco, ação recomendada

### 1. Atraso na entrega derruba a nota do cliente de forma severa
Fonte: `fact_orders` (`delivery_delay_days`, `review_score`)

| Situação de entrega | Nota média |
|---|---|
| Adiantado (>7 dias antes do prazo) | 4,31 |
| No prazo | 4,17 |
| Atraso de até 7 dias | 2,71 |
| Atraso acima de 7 dias | 1,70 |

Um atraso de mais de 7 dias derruba a nota média de ~4,3 para 1,7 — quase o pior score possível. **6,77% dos pedidos entregues chegam após o prazo estimado.** Isso é o maior alavancador identificável de satisfação do cliente nos dados: qualquer investimento em previsão de prazo mais realista ou em logística que reduza esse atraso tem retorno direto e mensurável em reputação (reviews públicos, recompra).
**Decisão sugerida:** priorizar iniciativas de SLA de entrega (revisão da estimativa de prazo dada ao cliente e/ou performance de transportadora) acima de qualquer outra melhoria de UX.

### 2. Frete representa ~14,3% do valor total pago pelo cliente
Fonte: `fact_order_items` (`price`, `freight_value`, `total_item_value`)

- Frete total: R$ 2.198.275,64 sobre um total de itens de R$ 13.221.498,11 (pedidos entregues).
- **3,66% dos itens têm frete maior que o próprio preço do produto** — ou seja, para ~4.100 itens o cliente paga mais para transportar do que para comprar. Esse é um ponto crítico de abandono de carrinho e de percepção de preço injusto, especialmente para produtos de baixo valor.
**Decisão sugerida:** revisar política de frete para itens de baixo ticket (frete fixo mínimo, ponto de corte de frete grátis, ou revisão de tabela por categoria/peso).

### 3. Concentração extrema de receita em poucos vendedores
Fonte: `fact_order_items` (`seller_id`, `total_item_value`)

- **Os 10% dos vendedores mais fortes (309 de 3.095) concentram 66,7% de toda a receita da plataforma.**
- Isso é um risco de dependência operacional: perda ou insatisfação de um punhado de sellers-chave afeta desproporcionalmente o negócio.
**Decisão sugerida:** mapear os top ~50-100 vendedores e criar programa de retenção/SLA dedicado; ao mesmo tempo, investigar por que a cauda longa (90% dos sellers) gera tão pouca receita — pode indicar problema de descoberta/visibilidade na plataforma.

---

## 🟠 Importantes — informam estratégia, mas não exigem ação imediata isolada

### 4. Alta concentração geográfica em SP tanto do lado de clientes quanto de vendedores
Fonte: `dim_customers` / `dim_sellers` (`customer_state`, `seller_state`)

- Clientes: SP 42,0%, RJ 12,9%, MG 11,7% — top 3 estados = ~66,6% da base.
- Vendedores: SP concentra **59,7%** dos sellers (vs. 42% dos clientes) — desequilíbrio de oferta vs. demanda por estado, o que pode explicar parte do custo/tempo de frete para regiões Norte/Nordeste (não medido diretamente aqui, mas é hipótese testável).
**Decisão sugerida:** cruzar `delivery_delay_days` por estado do cliente para confirmar se atraso é maior fora do eixo SP-RJ-MG; se sim, justifica expansão de base de vendedores fora do Sudeste.

### 5. Receita concentrada em poucas categorias de produto
Fonte: `fact_order_items` (`product_category_name`, `total_item_value`)

- As 10 categorias mais fortes (de 74 no total) respondem por **62,3% da receita**. Líderes: beleza_saude, relogios_presentes, cama_mesa_banho, esporte_lazer, informatica_acessorios.
**Decisão sugerida:** usar como base para decisões de sortimento/curadoria e negociação de melhores condições com fornecedores dessas categorias-chave.

### 6. Cartão de crédito domina como forma de pagamento, com parcelamento relevante
Fonte: `fact_orders` (`payment_types`, `payment_installments_max`)

- 74,7% dos pedidos usam cartão de crédito (isolado); boleto ainda representa 19,9%.
- 51,5% dos pedidos são parcelados em mais de 1x (média de 2,93 parcelas entre quem parcela).
**Decisão sugerida:** garantir que a experiência de checkout com boleto (2ª maior forma de pagamento, mas sem parcelamento nativo) não seja um gargalo de conversão; considerar taxas de parcelamento na precificação.

### 7. Cancelamento/indisponibilidade é baixo, mas não desprezível
Fonte: `fact_orders` (`order_status`)

- 1,24% dos pedidos terminam como `canceled` ou `unavailable` (625 + 609 de 99.441). Não é um número alarmante, mas junto aos **775 pedidos sem nenhum item registrado** (identificados na etapa de validação do ETL) sugere uma fração de atrito no funil de checkout que vale investigar operacionalmente (estoque, falha de sistema, desistência).

---

## 🟡 Moderados — relevantes para operação/qualidade de dado, impacto de negócio indireto

### 8. Satisfação geral é alta, mas com cauda de insatisfação concentrada
Fonte: `fact_orders` (`review_score`)

- 57,8% dos reviews são nota 5; porém **11,5% são nota 1** — uma distribuição bimodal (cliente ama ou odeia, pouco meio-termo). Nota média 4,09.
**Uso sugerido:** tratar nota 1 como sinal de atenção — ver item 1 (atraso) como principal causa identificada; vale segmentar os 11,5% de notas 1 para entender se atraso explica a maioria ou se há outras causas (produto, atendimento).

### 9. Recorrência de clientes é baixa
Fonte: `dim_customers` (`customer_unique_id`)

- De 96.096 clientes únicos, apenas **3,12% (2.997) fizeram mais de um pedido** (máximo de 17 pedidos por cliente).
**Uso sugerido:** indicador de oportunidade de CRM/fidelização — a maior parte da receita hoje depende de aquisição de novos clientes, não de retenção. Vale como métrica de acompanhamento para iniciativas de recompra (cupom pós-compra, e-mail marketing).

### 10. Tempo de aprovação de pagamento é rápido, mas com pequena fração sem aprovação
Fonte: `fact_orders` (`approval_time_hours`, `order_approved_at`)

- Média de 10,4 horas até aprovação — razoável. 160 pedidos (0,16%) nunca tiveram aprovação registrada, coerente com pedidos cancelados/abandonados antes do pagamento.
**Uso sugerido:** não é ponto de ação prioritário; útil como baseline se a operadora de pagamento mudar no futuro.

---

## ⚪ Opcionais — qualidade de dado / contexto complementar, sem impacto direto de negócio

### 11. Pedidos com múltiplos vendedores são raros
Fonte: `fact_order_items` (`order_id`, `seller_id`)

- Apenas 1,3% dos pedidos combinam itens de mais de um vendedor. Não é um padrão relevante de comportamento de compra hoje; relevante apenas se a plataforma quiser otimizar consolidação de envio (reduzir frete duplicado).

### 12. Produtos sem categoria têm impacto de receita desprezível
Fonte: `dim_products` / `fact_order_items` (`product_category_name`)

- 1,85% dos produtos (610 de 32.951) não tinham categoria informada na origem (tratados como `"outros"` no ETL) e respondem por apenas 1,31% da receita. Confirma que a decisão de modelagem de preencher com `"outros"` (em vez de descartar) não distorce nenhuma análise agregada relevante.

---

## Resumo executivo (top 3 para decisão imediata)

1. **Atraso de entrega é o fator isolado com maior correlação a insatisfação** — nota cai de 4,3 para 1,7 quando o atraso passa de 7 dias. Prioridade #1.
2. **Frete desproporcional (>preço do produto em 3,66% dos itens) é risco de conversão/percepção de preço.** Prioridade #2.
3. **66,7% da receita depende de 10% dos vendedores** — risco de concentração que merece plano de retenção dedicado. Prioridade #3.

---

*Análise gerada a partir dos datasets `output/dim_customers.parquet`, `output/dim_sellers.parquet`, `output/dim_products.parquet`, `output/fact_orders.parquet` e `output/fact_order_items.parquet`, produzidos pelo pipeline em `etl/`. Todos os percentuais foram calculados sobre os dados já limpos e validados (ver `README.md`).*
