# Topolino per gatti: prototipo A (senza camera)

Obiettivo: un giocattolo autonomo, veloce, che scatta in direzione opposta quando viene colpito. Serve a rispondere a una sola domanda: la gatta ci gioca per giorni o solo per minuti?

Prezzi e parti sono indicativi e vanno verificati prima di acquistare. Nessun link è stato controllato.

## Parti (circa 50-80 €, da verificare)

| Parte | Perché |
|---|---|
| ESP32 (scheda di sviluppo) | Cervello leggero, con Bluetooth |
| IMU (es. MPU-6050) | Rileva l'urto e da dove arriva |
| 3 micromotori con riduttore a giri alti (tipo N20) | Muovono le tre ruote |
| 3 ruote omni da circa 4 cm | Spostamento in qualsiasi direzione |
| 2 driver motore doppi (es. DRV8833) | Servono tre canali |
| Batteria al litio 1S con protezione + modulo di ricarica USB-C con protezione | Energia in sicurezza |
| Micro servo | Muove la coda |
| Scocca stampata in 3D (o da servizio di stampa) | Protegge ruote e batteria |
| Coda morbida e leggera | Attrae la gatta; si stacca senza spezzarsi in pezzi piccoli |

## Comportamento (macchina a stati)

1. **Riposo** a basso consumo.
2. **Urto** rilevato dall'accelerometro. La direzione dell'accelerazione dà la direzione dell'urto.
3. **Scatto** nella direzione opposta, con zigzag casuali.
4. **Pausa** ("fa il morto"), coda che si muove.
5. Ritorno al riposo.

## Parametri di difficoltà (da regolare dopo ogni prova)

- velocità massima dello scatto;
- ritardo di reazione dopo l'urto;
- numero e ampiezza dei zigzag;
- durata della pausa;
- probabilità di un secondo scatto.

## Piano di 4 settimane (5-6 ore nel weekend)

- **Settimana 1:** assemblare ruote e motori, guidarlo da telefono.
- **Settimana 2:** cinematica delle tre ruote (matrice 3×3 da velocità desiderata a velocità dei motori), misura di velocità e accelerazione.
- **Settimana 3:** rilevare l'urto, calcolarne la direzione, scattare dalla parte opposta.
- **Settimana 4:** scocca, coda, sicurezza, prova con la gatta.

## Sicurezza (non negoziabile)

- Batteria in una scocca rigida e sigillata.
- Ruote incassate: nessun punto dove una zampa o un artiglio possano incastrarsi.
- Nessuna parte piccola che si stacca; niente magneti piccoli accessibili.
- Sessioni brevi, con te presente. Se la gatta mostra stress, si ferma.

## Prima di investire altro

- Ricerca su Google Patents di idee simili.
- Valuta con un consulente se serve depositare un brevetto prima di pubblicare video.
- Prova con più gatti, non solo con la tua.
