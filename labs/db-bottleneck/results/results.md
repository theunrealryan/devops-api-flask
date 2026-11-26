| Cenário | Requisições | Falhas | p95 (ms) | p99 (ms) | Descartadas | Consultas no banco | Acerto do cache |
|---|---|---|---|---|---|---|---|
| 1-baseline-50rps | 576 | 99.3% | 10000.6 | 10004.3 | 425 | 184 | - |
| 2-scaleup-50rps | 592 | 92.4% | 10006.7 | 10034.0 | 411 | 433 | - |
| 3-indice-50rps | 1001 | 0% | 15.8 | 30.4 | 0 | 1910 | - |
| 4-indice-200rps | 4000 | 0% | 6.8 | 46.0 | 0 | 7345 | - |
| 5-indice-valkey-200rps | 4000 | 0% | 21.9 | 43.6 | 0 | 4648 | 35.0% |
| 4-indice-500rps | 9207 | 0% | 776.2 | 879.8 | 793 | 16197 | - |
| 5-indice-valkey-500rps | 9975 | 0% | 90.8 | 147.1 | 25 | 8144 | 58.7% |
| 6-migracao-sem-timeout | 832 | 70.6% | 10000.4 | 10000.8 | 168 | - | - |
| 7-migracao-com-timeout | 991 | 0% | 7.0 | 1468.1 | 10 | - | - |
