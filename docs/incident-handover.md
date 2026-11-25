# Incident handover | LTE attach authentication

**Status:** Open for investigation. Synthetic MME-side events, UTC.

## Observation and scope

Attempt `a06`, exchange `s6a-a06`, sent an Authentication Information Request at `09:01:00.020Z` and recorded a timeout at `09:01:01.200Z`, **1,180 ms later**. There is no matching Answer in the MME trace. In the two-attempt trace, `a01` received its matching Answer after 25 ms. In the separate ten-attempt batch, five attaches completed and two of the five failures were labelled authentication timeouts. These counts describe the fixtures.

[Event trace](../attach-events.csv) · [Generated report](../attach-events.json) · [Batch records](../attempts.csv)

## Next shift

| Peer-side evidence | Next check |
| --- | --- |
| HSS received the request and sent no answer | Ask the HSS owner to inspect request handling, result logs and processing delay around the matched UTC timestamp. |
| HSS sent an answer | Compare send and receive evidence along the Diameter path and check MME correlation and timeout logs. A response received after the timer expired changes the investigation. |
| An available, complete HSS capture shows no matching request | Compare MME egress and intermediate routing evidence to find the last observed hop. |
| Peer records are unavailable or incomplete | Keep fault location open. Request the peer evidence before assigning ownership of the fault. |

## Escalation and retest

Send the HSS/Diameter owner the attempt ID, exchange ID, UTC interval, observed timer, and linked report. If an answer was sent and the MME did not record it, bring in the signalling transport owner with the same evidence. After the change, rerun a known-good attach and the previously failing scenario. Compare request/answer timing and attach completion. In a controlled negative test, check that an explicit timeout and an incomplete capture still produce separate classifications.
