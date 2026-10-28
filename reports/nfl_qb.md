# NFL – vrstva quarterback (náhradník)

Bežný štartér = najčastejší štartujúci quarterback tímu v posledných 8 odohraných zápasoch (pri rovnosti posledný). Náhradník = iný štartujúci quarterback → tím −penalizácia Elo. Penalizácia naučená len na tréningu 2010 – 2022, hodnotí sa test 2023 – 2025 (rovnaké zápasy ako G0-NFL).

## Výsledok: ✅ prejde (hranica zlepšenia 0,0005)

| Model (test) | Zápasy | Presnosť | Log loss | Brier |
|---|---|---|---|---|
| Elo (G0) | 854 | 63,9 % | 0,63412 | 0,22181 |
| Elo + náhradník (−65 Elo) | 854 | 64,4 % | 0,63050 | 0,22022 |

Zlepšenie na teste 0,00362, na tréningu 0,00403. Náhradník nastúpil v 19,1 % tímových zápasov tréningu a 23,5 % testu.

## Ladenie na tréningu (5 najlepších)

|   penalizácia (Elo) | log loss (tréning)   |
|--------------------:|:---------------------|
|                  65 | 0,62585              |
|                  60 | 0,62585              |
|                  70 | 0,62590              |
|                  55 | 0,62590              |
|                  75 | 0,62600              |

Zamietnutý kandidát (28. 10.): nováčik (< 8 štartov v kariére, −25 Elo) – na teste +0,00123, na tréningu len +0,00043 (pod hranicou), riziko náhody.
