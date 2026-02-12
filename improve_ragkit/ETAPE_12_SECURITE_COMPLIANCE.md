# Etape 12 : SECURITE & COMPLIANCE

## Objectif
Ajouter les mecanismes de securite de base : PII detection/redaction, content moderation, rate limiting, et audit logging.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| SecurityConfigV2 | `ragkit/config/schema_v2.py` | Complet (PII, moderation, access control, audit, rate limiting, encryption) - NON branche |
| API CORS | `ragkit/config/schema.py` | APICorsConfig existant |
| UI | `Settings.tsx` | Aucun parametre securite |

### Ce qui manque
- Detection/redaction PII (emails, telephones, numeros de carte)
- Content moderation (filtrage de contenu toxique)
- Rate limiting
- Audit logging
- Branchement de `SecurityConfigV2`

---

## Phase 2 : PII Detection & Redaction

### 2.1 Creer `ragkit/security/pii.py`

```python
class PIIDetector:
    """Detecte et redacte les informations personnelles."""

    PATTERNS = {
        "EMAIL_ADDRESS": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "PHONE_NUMBER": r'\b(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}\b',
        "CREDIT_CARD": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        "IBAN": r'\b[A-Z]{2}\d{2}[\s]?[\dA-Z]{4}[\s]?(?:[\dA-Z]{4}[\s]?){2,7}[\dA-Z]{1,4}\b',
        "IP_ADDRESS": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
    }

    def __init__(self, config: SecurityConfigV2):
        self.config = config
        self.entities = config.pii_entities
        self.mode = config.pii_detection_mode  # detect / redact / block

    def process(self, text: str) -> tuple[str, list[dict]]:
        """Traite le texte selon le mode configure."""
        detections = []
        processed = text

        for entity_type in self.entities:
            pattern = self.PATTERNS.get(entity_type)
            if not pattern:
                continue
            matches = re.finditer(pattern, text)
            for match in matches:
                detections.append({
                    "type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                })
                if self.mode == "redact":
                    processed = processed.replace(match.group(), f"[{entity_type}]")

        if self.mode == "block" and detections:
            raise SecurityError(f"PII detected: {[d['type'] for d in detections]}")

        return processed, detections
```

---

## Phase 3 : Content Moderation

### 3.1 Creer `ragkit/security/moderation.py`

```python
class ContentModerator:
    """Filtre le contenu inapproprie dans les requetes et reponses."""

    def __init__(self, config: SecurityConfigV2):
        self.config = config

    def check_input(self, query: str) -> tuple[bool, str | None]:
        """Verifie que la requete est appropriee."""
        if self.config.block_prompt_injection:
            if self._detect_prompt_injection(query):
                return False, "Potential prompt injection detected"
        return True, None

    def check_output(self, response: str) -> tuple[bool, str | None]:
        """Verifie que la reponse est appropriee."""
        return True, None

    def _detect_prompt_injection(self, text: str) -> bool:
        """Detection basique de prompt injection."""
        suspicious_patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"disregard\s+(all\s+)?above",
            r"you\s+are\s+now\s+a",
            r"system\s*:\s*you",
            r"<\|im_start\|>",
        ]
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in suspicious_patterns)
```

---

## Phase 4 : Rate Limiting

### 4.1 Creer `ragkit/security/rate_limiter.py`

```python
class RateLimiter:
    """Limite le nombre de requetes par utilisateur/IP."""

    def __init__(self, config: SecurityConfigV2):
        self.max_per_minute = config.max_requests_per_minute
        self.max_per_day = config.max_requests_per_day
        self._minute_counters: dict[str, list[float]] = defaultdict(list)
        self._day_counters: dict[str, int] = defaultdict(int)

    def check(self, client_id: str = "default") -> tuple[bool, str | None]:
        """Verifie si la requete est autorisee."""
        now = time.time()

        # Nettoyer les compteurs de la derniere minute
        self._minute_counters[client_id] = [
            t for t in self._minute_counters[client_id] if now - t < 60
        ]

        if len(self._minute_counters[client_id]) >= self.max_per_minute:
            return False, "Rate limit exceeded (per minute)"

        self._minute_counters[client_id].append(now)
        return True, None
```

---

## Phase 5 : Audit Logging

### 5.1 Creer `ragkit/security/audit.py`

```python
class AuditLogger:
    """Enregistre les evenements de securite et d'acces."""

    def __init__(self, config: SecurityConfigV2):
        self.config = config
        self.logger = logging.getLogger("ragkit.audit")

    def log_query(self, query: str, user: str = "anonymous", **kwargs):
        """Enregistre une requete."""
        if self.config.log_all_queries:
            self.logger.info("QUERY", extra={
                "user": user,
                "query": query[:200],
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs,
            })

    def log_document_access(self, document_id: str, user: str = "anonymous"):
        """Enregistre un acces a un document."""
        if self.config.log_document_access:
            self.logger.info("DOC_ACCESS", extra={
                "user": user,
                "document_id": document_id,
                "timestamp": datetime.utcnow().isoformat(),
            })

    def log_security_event(self, event_type: str, details: str):
        """Enregistre un evenement de securite."""
        self.logger.warning("SECURITY", extra={
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        })
```

---

## Phase 6 : UI - Exposition des Parametres

### Settings.tsx - Section "Securite"

Ajouter dans l'onglet "advanced" :
- **PII Detection** : Checkbox enabled
- **PII Mode** : Select (detect / redact / block)
- **Content Moderation** : Checkbox enabled
- **Prompt Injection Protection** : Checkbox enabled
- **Rate Limiting** : Checkbox enabled, Input max/minute, max/day
- **Audit Logging** : Checkbox enabled

---

## Phase 7 : Tests & Validation

### Tests
```
tests/unit/test_security.py
  - test_pii_detection_email
  - test_pii_detection_phone
  - test_pii_redaction
  - test_pii_block_mode
  - test_prompt_injection_detection
  - test_rate_limiter
  - test_audit_logging
```

### Validation
1. Builder dans `.build/`
2. Envoyer un texte avec un email -> verifier la redaction
3. Tenter un prompt injection -> verifier le blocage
4. Depasser la limite de requetes -> verifier le rate limiting
5. Verifier les logs d'audit

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| CREER | `ragkit/security/__init__.py` |
| CREER | `ragkit/security/pii.py` |
| CREER | `ragkit/security/moderation.py` |
| CREER | `ragkit/security/rate_limiter.py` |
| CREER | `ragkit/security/audit.py` |
| MODIFIER | Pipeline RAG (integration securite) |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| CREER | `tests/unit/test_security.py` |

---

## Criteres de Validation

- [ ] PII detection fonctionnelle (email, phone, credit card)
- [ ] PII redaction fonctionnelle
- [ ] Prompt injection detection fonctionnelle
- [ ] Rate limiting fonctionnel
- [ ] Audit logging fonctionnel
- [ ] Parametres exposes dans l'UI
- [ ] Tests passent
- [ ] Build et test manuel OK
