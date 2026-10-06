<!-- expect: fail 객체의 연속 줄(첫 줄만 표시)을 잡는가 — v3.10.1 첫 검산의 자리 -->
```jsonc
{
  "reproduce": {
    "parameters": { "window.months": 12,                              // [id]
                    "cpd.minimum_tokens": 100,
                    "profile": "jqradar-default" },                   // [id]
    "people": { "attribution": "off" }                                // [id]
  }
}
```
