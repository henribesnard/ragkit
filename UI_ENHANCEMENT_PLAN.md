# RAGKIT UI Enhancement Plan — Configuration Fine-Grained

## Objectif

Enrichir l'interface de configuration pour que l'utilisateur ait un controle fin sur chaque parametre de son RAG. Chaque champ doit etre accompagne d'un tooltip d'aide (?), les saisies libres doivent etre remplacees par des selects/multi-selects quand c'est possible, et toutes les options du schema Pydantic doivent etre exposees.

## Audit des lacunes actuelles

### Ce qui est expose vs ce qui existe dans le backend

| Tab | Champs actuels | Champs manquants dans le backend schema |
|-----|---------------|----------------------------------------|
| **General** | name, description, environment | - (complet) |
| **Ingestion** | source path, patterns (texte libre) | parsing engine, OCR, chunking strategy/params, metadata, recursive flag, bouton upload, patterns multi-select |
| **Retrieval** | architecture, top_k semantique | similarity_threshold, poids semantic/lexical, BM25 params, fusion method, rerank config, dedup, context max_chunks/max_tokens |
| **LLM** | provider (3 options), model (texte libre) | API key (!), temperature, max_tokens, top_p, timeout, max_retries, secondary/fast LLM, providers DeepSeek/Groq/Mistral |
| **Agents** | mode (default/custom) | system prompts (query analyzer + response generator), output schema, behavior configs, global timeout/retries |
| **Embedding** | _(n'existe pas comme tab)_ | provider, model, API key, batch_size, dimensions, cache, query_model separe |
| **Vector Store** | _(n'existe pas)_ | provider, mode, collection_name, distance_metric, URL/path/API key |
| **Conversation** | _(n'existe pas)_ | memory type, window_size, persistence backend |
| **Chatbot** | _(n'existe pas)_ | enabled, title, theme, examples, features |
| **Observability** | _(n'existe pas)_ | log level, format, file config, metrics tracking |

---

## Phase 0 : Composants UI partagés

Status: DONE

### Tache 0.1 — Composant `HelpTooltip`

**Fichier a creer :** `ragkit-ui/src/components/ui/help-tooltip.tsx`

Un petit icone `?` qui affiche un texte explicatif au survol (hover) et au clic (mobile).

```tsx
interface HelpTooltipProps {
  text: string;
}

export function HelpTooltip({ text }: HelpTooltipProps)
```

**Implementation :**
- Icone : cercle avec `?` dedans, couleur muted (gris), taille 16px
- Au hover : afficher un popover/tooltip positionne a droite ou au-dessus
- Au clic : toggle le tooltip (pour mobile)
- Style : fond blanc, border subtle, ombre douce, `text-sm`, max-width 280px
- Utiliser un `<div>` positionne en `absolute` ou `fixed` avec z-index eleve
- Pas de dependance externe (pas besoin de Radix/Headless UI)

**Structure du composant :**
```tsx
<div className="relative inline-flex">
  <button
    onMouseEnter={() => setShow(true)}
    onMouseLeave={() => setShow(false)}
    onClick={() => setShow(!show)}
    className="ml-1.5 inline-flex h-4 w-4 items-center justify-center
               rounded-full bg-slate-200 text-[10px] font-bold text-slate-500
               hover:bg-accent/20 hover:text-accent"
  >
    ?
  </button>
  {show && (
    <div className="absolute left-6 top-0 z-50 w-64 rounded-xl
                    border bg-white p-3 text-xs text-slate-600 shadow-lg">
      {text}
    </div>
  )}
</div>
```

### Tache 0.2 — Composant `FieldLabel`

**Fichier a creer :** `ragkit-ui/src/components/ui/field-label.tsx`

Combine le label + le tooltip en un seul composant reutilisable :

```tsx
interface FieldLabelProps {
  label: string;
  help?: string;
}

export function FieldLabel({ label, help }: FieldLabelProps)
```

**Rendu :**
```
Chunk size [?]     ← label en semibold + tooltip a cote
```

**Usage dans les sections :**
```tsx
// Avant :
<p className="text-sm font-semibold">Chunk size</p>

// Apres :
<FieldLabel label="Chunk size" help="Nombre de caracteres par chunk. Plus petit = plus precis mais plus de chunks." />
```

### Tache 0.3 — Composant `MultiSelect`

**Fichier a creer :** `ragkit-ui/src/components/ui/multi-select.tsx`

Liste de choix avec cases a cocher. L'utilisateur coche les patterns qu'il veut.

```tsx
interface MultiSelectProps {
  options: { value: string; label: string }[];
  selected: string[];
  onChange: (selected: string[]) => void;
  allowCustom?: boolean; // permet d'ajouter une valeur custom
}

export function MultiSelect({ options, selected, onChange, allowCustom }: MultiSelectProps)
```

**Implementation :**
- Afficher les options comme des chips/tags cliquables
- Les chips selectionnees sont en couleur accent
- Si `allowCustom`, ajouter un petit champ input en bas pour taper un pattern custom + bouton "Add"
- Style coherent avec les inputs existants (rounded-2xl, border-slate-200)

### Tache 0.4 — Composant `NumberInput`

**Fichier a creer :** `ragkit-ui/src/components/ui/number-input.tsx`

Input numerique avec min/max/step et affichage du range autorise.

```tsx
interface NumberInputProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  unit?: string; // ex: "tokens", "ms"
}

export function NumberInput({ value, onChange, min, max, step, unit }: NumberInputProps)
```

### Tache 0.5 — Composant `SliderInput`

**Fichier a creer :** `ragkit-ui/src/components/ui/slider-input.tsx`

Slider avec affichage de la valeur pour les parametres continus (temperature, threshold, weight).

```tsx
interface SliderInputProps {
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  label?: string;
}

export function SliderInput({ value, onChange, min, max, step, label }: SliderInputProps)
```

**Implementation :** `<input type="range">` stylise + affichage de la valeur courante a droite.

### Tache 0.6 — Composant `ToggleSwitch`

**Fichier a creer :** `ragkit-ui/src/components/ui/toggle-switch.tsx`

Interrupteur on/off stylise pour les booleens (enabled/disabled).

```tsx
interface ToggleSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
}

export function ToggleSwitch({ checked, onChange, label }: ToggleSwitchProps)
```

### Tache 0.7 — Composant `CollapsibleSection`

**Fichier a creer :** `ragkit-ui/src/components/ui/collapsible-section.tsx`

Section depliable pour les parametres avances. Evite de surcharger la vue par defaut.

```tsx
interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

export function CollapsibleSection({ title, defaultOpen = false, children }: CollapsibleSectionProps)
```

**Rendu :** Header cliquable avec chevron, le contenu glisse en hauteur avec une transition CSS.

---

## Phase 1 : Tab General — Ajouter les tooltips

Status: DONE

**Fichier :** `ragkit-ui/src/components/config/sections/GeneralConfig.tsx`

### Etapes :
1. Importer `FieldLabel`
2. Remplacer chaque `<p className="text-sm font-semibold">` par `<FieldLabel>`

### Mapping label → tooltip :

| Champ | Tooltip |
|-------|---------|
| Project name | Nom unique de votre projet RAG. Utilise dans les logs et l'interface. |
| Description | Description libre du projet. Aide a documenter l'objectif du systeme RAG. |
| Environment | `development` : logs verbeux, rechargement rapide. `staging` : test pre-production. `production` : optimise pour la performance. |

---

## Phase 2 : Tab Ingestion — Enrichir massivement

Status: DONE (UI). Backend browse endpoint deferred.

**Fichier :** `ragkit-ui/src/components/config/sections/IngestionConfig.tsx`

Le tab actuel n'a que 2 champs (source path, patterns). Le schema backend expose : sources, parsing (engine, OCR), chunking (strategy, chunk_size, overlap, semantic params), metadata.

### Structure cible du tab :

```
[Source path]  [?] ............... [Browse / Upload folder button]
[Patterns]     [?] ............... [MultiSelect: *.pdf, *.md, *.txt, *.docx, *.html, + custom]
[Recursive]    [?] ............... [ToggleSwitch]

▼ Parsing (section depliable)
  [Parsing engine]  [?] .......... [Select: auto, unstructured, docling, pypdf]
  [OCR enabled]     [?] .......... [ToggleSwitch]
  [OCR engine]      [?] .......... [Select: tesseract, easyocr]  (visible si OCR enabled)
  [OCR languages]   [?] .......... [MultiSelect: eng, fra, deu, spa, ita, + custom]

▼ Chunking (section depliable)
  [Strategy]        [?] .......... [Select: fixed, semantic]
  --- Si fixed ---
  [Chunk size]      [?] .......... [NumberInput min=64 max=4096 step=64]
  [Chunk overlap]   [?] .......... [NumberInput min=0 max=512 step=10]
  --- Si semantic ---
  [Similarity threshold] [?] ..... [SliderInput 0.0-1.0 step=0.05]
  [Min chunk size]  [?] .......... [NumberInput min=50 max=2000]
  [Max chunk size]  [?] .......... [NumberInput min=200 max=4000]

▼ Metadata (section depliable)
  [Extract fields]  [?] .......... [MultiSelect: source_path, file_type, creation_date, + custom]
```

### Mapping label → tooltip :

| Champ | Tooltip |
|-------|---------|
| Source path | Repertoire contenant les documents qui constitueront votre base de connaissances. Chemin relatif depuis la racine du projet. |
| Patterns | Types de fichiers a indexer. Selectionnez les formats de vos documents. |
| Recursive | Si active, parcourt aussi les sous-dossiers du repertoire source. |
| Parsing engine | Moteur d'extraction de texte. `auto` detecte automatiquement le meilleur moteur selon le type de fichier. `unstructured` et `docling` supportent plus de formats. `pypdf` est leger et rapide pour les PDF simples. |
| OCR enabled | Active la reconnaissance optique de caracteres pour les PDF scannes et les images. Necessite un moteur OCR installe. |
| OCR engine | `tesseract` : moteur OCR open-source classique, rapide. `easyocr` : base sur le deep learning, meilleur sur les langues non-latines. |
| OCR languages | Langues des documents pour l'OCR. Ajouter les codes de langue pertinents. |
| Chunking strategy | `fixed` : decoupe en morceaux de taille fixe (simple et rapide). `semantic` : decoupe en suivant la coherence semantique du texte (meilleure qualite mais plus lent). |
| Chunk size | Nombre de caracteres par morceau. Plus petit (256-512) = plus precis pour la recherche. Plus grand (1024-2048) = plus de contexte par resultat. |
| Chunk overlap | Nombre de caracteres de chevauchement entre les morceaux consecutifs. Evite de couper une phrase ou une idee au milieu. 50-100 est un bon defaut. |
| Similarity threshold | Seuil de similarite pour determiner ou couper. Plus haut (0.9+) = morceaux plus granulaires. Plus bas (0.7) = morceaux plus larges. |
| Min chunk size | Taille minimale d'un chunk semantique. Les morceaux trop petits sont fusionnes. |
| Max chunk size | Taille maximale d'un chunk semantique. Au-dela, le texte est coupe. |
| Extract fields | Metadonnees extraites automatiquement de chaque document et stockees avec les chunks. Utiles pour le filtrage a la recherche. |

### Bouton Upload / Browse

Pour le champ `Source path`, ajouter un bouton a droite de l'input :
```tsx
<div className="flex gap-2">
  <Input value={source.path} onChange={...} className="flex-1" />
  <Button variant="outline" onClick={handleBrowse}>
    <FolderIcon className="mr-1 h-4 w-4" />
    Browse
  </Button>
</div>
```

**Limitation :** Le browse de dossier dans un navigateur est limite. Deux approches possibles :
1. **`<input type="file" webkitdirectory>`** : permet de selectionner un dossier (Chrome/Edge/Firefox). Le navigateur retourne la liste des fichiers. On peut en extraire le chemin relatif.
2. **Backend endpoint `POST /api/v1/admin/browse`** : le frontend envoie un chemin partiel, le backend liste les dossiers a cet emplacement et retourne la liste. Le frontend affiche un file picker custom.

**Recommandation :** Approche 2 (backend endpoint) car elle fonctionne avec des chemins serveur et pas des chemins client. Mais pour un MVP, l'approche 1 suffit pour indiquer quel dossier l'utilisateur veut utiliser.

**Endpoint backend a creer :** `POST /api/v1/admin/browse`
```python
@router.post("/browse")
async def browse_directory(request: Request):
    body = await request.json()
    base = Path(body.get("path", "."))
    if not base.is_dir():
        return {"entries": [], "error": "Not a directory"}
    entries = []
    for item in sorted(base.iterdir()):
        if item.is_dir():
            entries.append({"name": item.name, "type": "directory"})
        else:
            entries.append({"name": item.name, "type": "file", "size": item.stat().st_size})
    return {"entries": entries, "current": str(base.resolve())}
```

---

## Phase 3 : Nouveau tab Embedding

Status: DONE

**Fichier a creer :** `ragkit-ui/src/components/config/sections/EmbeddingConfig.tsx`

Actuellement l'embedding est configure UNIQUEMENT dans le wizard, pas dans la page Config. Il faut ajouter un tab "Embedding" dans la page Config.

### Structure cible :

```
=== Document Embedding Model ===
[Provider]    [?] .......... [Select: openai, ollama, cohere, litellm]
[Model]       [?] .......... [Select dynamique selon provider + option custom]
[API key]     [?] .......... [Input password]  (masque si ollama)

▼ Parametres (depliable)
  [Batch size]    [?] ........ [NumberInput min=1 max=2048]
  [Dimensions]    [?] ........ [NumberInput, nullable]
  [Cache enabled] [?] ........ [ToggleSwitch]
  [Cache backend] [?] ........ [Select: memory, disk]  (visible si cache enabled)

=== Query Embedding Model ===
[Same as document model]  [ToggleSwitch — on par defaut]
--- Si off, afficher les memes champs pour le query model ---
```

### Dropdown de modeles par provider

Plutot que laisser l'utilisateur saisir un nom de modele en texte libre (risque d'erreur), fournir une liste deroulante avec les modeles courants ET une option "Custom" pour saisir un modele non liste.

**Fichier de donnees a creer :** `ragkit-ui/src/data/models.ts`

```typescript
export const EMBEDDING_MODELS: Record<string, { value: string; label: string }[]> = {
  openai: [
    { value: "text-embedding-3-large", label: "text-embedding-3-large (3072d, best quality)" },
    { value: "text-embedding-3-small", label: "text-embedding-3-small (1536d, fast)" },
    { value: "text-embedding-ada-002", label: "text-embedding-ada-002 (1536d, legacy)" },
  ],
  ollama: [
    { value: "nomic-embed-text", label: "nomic-embed-text (768d)" },
    { value: "mxbai-embed-large", label: "mxbai-embed-large (1024d)" },
    { value: "all-minilm", label: "all-minilm (384d, fast)" },
    { value: "snowflake-arctic-embed", label: "snowflake-arctic-embed (1024d)" },
  ],
  cohere: [
    { value: "embed-multilingual-v3.0", label: "embed-multilingual-v3.0 (1024d, multilingual)" },
    { value: "embed-english-v3.0", label: "embed-english-v3.0 (1024d, English)" },
    { value: "embed-multilingual-light-v3.0", label: "embed-multilingual-light-v3.0 (384d, fast)" },
  ],
  litellm: [
    { value: "mistral/mistral-embed", label: "Mistral Embed (1024d)" },
  ],
};

export const LLM_MODELS: Record<string, { value: string; label: string }[]> = {
  openai: [
    { value: "gpt-4o", label: "GPT-4o (flagship, multimodal)" },
    { value: "gpt-4o-mini", label: "GPT-4o mini (fast, low cost)" },
    { value: "gpt-4-turbo", label: "GPT-4 Turbo (128k context)" },
    { value: "o1", label: "o1 (reasoning)" },
    { value: "o1-mini", label: "o1-mini (reasoning, fast)" },
  ],
  anthropic: [
    { value: "claude-sonnet-4-20250514", label: "Claude Sonnet 4 (balanced)" },
    { value: "claude-opus-4-20250514", label: "Claude Opus 4 (most capable)" },
    { value: "claude-haiku-3-5-20241022", label: "Claude 3.5 Haiku (fast, low cost)" },
  ],
  deepseek: [
    { value: "deepseek-chat", label: "DeepSeek Chat (V3, general)" },
    { value: "deepseek-reasoner", label: "DeepSeek Reasoner (R1, reasoning)" },
  ],
  groq: [
    { value: "llama-3.3-70b-versatile", label: "Llama 3.3 70B (versatile)" },
    { value: "llama-3.1-8b-instant", label: "Llama 3.1 8B (ultra-fast)" },
    { value: "mixtral-8x7b-32768", label: "Mixtral 8x7B (32k context)" },
    { value: "gemma2-9b-it", label: "Gemma 2 9B" },
  ],
  mistral: [
    { value: "mistral-large-latest", label: "Mistral Large (best quality)" },
    { value: "mistral-medium-latest", label: "Mistral Medium (balanced)" },
    { value: "mistral-small-latest", label: "Mistral Small (fast)" },
    { value: "codestral-latest", label: "Codestral (code)" },
  ],
  ollama: [
    { value: "llama3", label: "Llama 3 8B" },
    { value: "llama3:70b", label: "Llama 3 70B" },
    { value: "mistral", label: "Mistral 7B" },
    { value: "mixtral", label: "Mixtral 8x7B" },
    { value: "phi3", label: "Phi-3" },
    { value: "qwen2", label: "Qwen 2" },
    { value: "gemma2", label: "Gemma 2" },
    { value: "deepseek-r1", label: "DeepSeek R1" },
  ],
};
```

### Composant `ModelSelect`

**Fichier a creer :** `ragkit-ui/src/components/ui/model-select.tsx`

Select qui affiche les modeles du provider selectionne + une option "Custom" qui revele un input texte.

```tsx
interface ModelSelectProps {
  provider: string;
  models: Record<string, { value: string; label: string }[]>;
  value: string;
  onChange: (value: string) => void;
}
```

### Mapping label → tooltip (Embedding) :

| Champ | Tooltip |
|-------|---------|
| Provider | Service qui genere les vecteurs d'embedding. `OpenAI` et `Cohere` necessitent une cle API. `Ollama` tourne en local sans cle. `LiteLLM` est un passe-plat generique pour d'autres providers. |
| Model | Modele d'embedding a utiliser. Chaque modele produit des vecteurs de dimension differente. Un modele plus grand donne de meilleurs resultats mais est plus lent et couteux. |
| API key | Cle d'API pour le provider d'embedding. Non necessaire pour les providers locaux (Ollama). |
| Batch size | Nombre de textes envoyes en une seule requete au provider. Plus grand = plus rapide pour l'ingestion de gros volumes. Reduire si vous avez des erreurs de timeout. |
| Dimensions | Nombre de dimensions du vecteur. Certains modeles permettent de reduire les dimensions pour economiser l'espace. Laisser vide pour utiliser la dimension par defaut du modele. |
| Cache enabled | Active le cache des embeddings deja calcules. Evite de recalculer les embeddings des documents deja traites. Recommande pour les gros volumes. |
| Cache backend | `memory` : cache en RAM, perdu au redemarrage. `disk` : cache sur disque, persiste entre les redemarrages. |
| Same as document model | Si active, le meme modele est utilise pour encoder les requetes et les documents. Desactiver si vous voulez un modele different pour les requetes (usage avance). |

---

## Phase 4 : Tab LLM — Enrichir massivement

Status: DONE

**Fichier :** `ragkit-ui/src/components/config/sections/LLMConfig.tsx`

### Structure cible :

```
=== LLM Principal (Primary) ===
[Provider]    [?] .......... [Select: openai, anthropic, deepseek, groq, mistral, ollama]
[Model]       [?] .......... [ModelSelect dynamique selon provider]
[API key]     [?] .......... [Input password]  (masque si ollama)

▼ Parametres du modele (depliable)
  [Temperature]   [?] ........ [SliderInput 0.0-2.0 step=0.1]
  [Max tokens]    [?] ........ [NumberInput min=1 max=128000]
  [Top P]         [?] ........ [SliderInput 0.0-1.0 step=0.05]
  [Timeout]       [?] ........ [NumberInput min=1 max=300, unite: secondes]
  [Max retries]   [?] ........ [NumberInput min=0 max=10]

▼ LLM Secondaire (depliable, optionnel)
  [Enabled]       [?] ........ [ToggleSwitch]
  --- Si enabled : memes champs que Primary ---

▼ LLM Rapide (depliable, optionnel)
  [Enabled]       [?] ........ [ToggleSwitch]
  --- Si enabled : memes champs que Primary ---
```

### Mapping label → tooltip (LLM) :

| Champ | Tooltip |
|-------|---------|
| Provider | Fournisseur du modele de langage. `OpenAI`, `Anthropic`, `DeepSeek`, `Groq`, `Mistral` sont des services cloud necessitant une cle API. `Ollama` tourne en local sur votre machine. |
| Model | Modele de langage a utiliser. Un modele plus capable donnera de meilleures reponses mais sera plus lent et couteux. |
| API key | Cle d'API du fournisseur. Generee depuis le dashboard du provider. Non necessaire pour Ollama (local). |
| Temperature | Controle la creativite des reponses. `0.0` = deterministe et factuel. `0.7` = equilibre. `1.5+` = creatif et imprevisible. Pour un RAG, recommande entre 0.1 et 0.7. |
| Max tokens | Nombre maximum de tokens dans la reponse generee. 1 token ≈ 4 caracteres. `1000` ≈ 750 mots. Augmenter pour des reponses longues. |
| Top P | Echantillonnage par noyau : ne considere que les tokens dont la probabilite cumulee atteint ce seuil. `1.0` = tous les tokens. `0.9` = exclut les tokens les moins probables. Laisser a 1.0 sauf besoin specifique. |
| Timeout | Temps maximum d'attente pour une reponse du LLM en secondes. Augmenter pour les modeles lents ou les reponses longues. |
| Max retries | Nombre de tentatives en cas d'echec (erreur reseau, rate limit). `2-3` est recommande pour la production. |
| LLM Secondaire | Modele de secours utilise si le modele principal echoue ou est indisponible. Utile pour la resilience en production. |
| LLM Rapide | Modele leger utilise pour les taches simples (analyse de requete, classification d'intent). Plus rapide et moins couteux que le modele principal. |

---

## Phase 5 : Tab Retrieval — Enrichir massivement

Status: DONE

**Fichier :** `ragkit-ui/src/components/config/sections/RetrievalConfig.tsx`

### Structure cible :

```
[Architecture]      [?] ...... [Select: semantic, lexical, hybrid, hybrid_rerank]

=== Recherche Semantique === (visible si architecture contient "semantic")
  [Enabled]           [?] .... [ToggleSwitch]
  [Weight]            [?] .... [SliderInput 0.0-1.0]  (visible si hybrid)
  [Top K]             [?] .... [NumberInput min=1 max=100]
  [Similarity threshold] [?] . [SliderInput 0.0-1.0]

=== Recherche Lexicale === (visible si architecture contient "lexical" ou "hybrid")
  [Enabled]           [?] .... [ToggleSwitch]
  [Weight]            [?] .... [SliderInput 0.0-1.0]  (visible si hybrid)
  [Top K]             [?] .... [NumberInput min=1 max=100]
  [Algorithm]         [?] .... [Select: bm25, bm25+]
  ▼ BM25 Parameters (depliable)
    [k1]              [?] .... [SliderInput 0.0-3.0]
    [b]               [?] .... [SliderInput 0.0-1.0]
  ▼ Preprocessing (depliable)
    [Lowercase]       [?] .... [ToggleSwitch]
    [Remove stopwords] [?] ... [ToggleSwitch]
    [Stopwords lang]  [?] .... [Select: french, english, auto]
    [Stemming]        [?] .... [ToggleSwitch]

=== Reranking === (visible si architecture = hybrid_rerank)
  [Enabled]           [?] .... [ToggleSwitch]
  [Provider]          [?] .... [Select: cohere, none]
  [Model]             [?] .... [Input]
  [API key]           [?] .... [Input password]
  [Top N]             [?] .... [NumberInput min=1 max=50]
  [Candidates]        [?] .... [NumberInput min=1 max=200]
  [Relevance threshold] [?] .. [SliderInput 0.0-1.0]

▼ Fusion (depliable, visible si hybrid)
  [Method]            [?] .... [Select: weighted_sum, reciprocal_rank_fusion]
  [Normalize scores]  [?] .... [ToggleSwitch]
  [RRF K]             [?] .... [NumberInput min=1 max=200]  (visible si RRF)

▼ Context (depliable)
  [Max chunks]        [?] .... [NumberInput min=1 max=20]
  [Max tokens]        [?] .... [NumberInput min=100 max=16000]
  [Deduplication]     [?] .... [ToggleSwitch]
  [Dedup threshold]   [?] .... [SliderInput 0.0-1.0]  (visible si dedup)
```

### Mapping label → tooltip (Retrieval) :

| Champ | Tooltip |
|-------|---------|
| Architecture | Strategie de recherche. `semantic` : recherche par similarite vectorielle (recommande). `lexical` : recherche par mots-cles (BM25). `hybrid` : combine les deux. `hybrid_rerank` : hybrid + reranking pour la meilleure precision. |
| Weight (semantic) | Poids de la recherche semantique dans le score final hybrid. Doit sommer a 1.0 avec le poids lexical. |
| Weight (lexical) | Poids de la recherche lexicale dans le score final hybrid. |
| Top K | Nombre de resultats a retourner par la recherche. Plus grand = plus de contexte mais plus lent et plus de bruit. |
| Similarity threshold | Score minimum de similarite pour qu'un resultat soit retenu. `0.0` = tout garder. `0.5` = filtrer les resultats peu pertinents. Augmenter si vous avez trop de resultats non pertinents. |
| Algorithm | `bm25` : algorithme classique de recherche par mots-cles. `bm25+` : variante qui gere mieux les documents longs. |
| k1 (BM25) | Controle la saturation de la frequence des termes. `1.2-2.0` est standard. Plus haut = plus de poids aux termes frequents. |
| b (BM25) | Controle la normalisation par longueur de document. `0.75` est standard. `0.0` = pas de normalisation. `1.0` = normalisation complete. |
| Lowercase | Convertir les textes en minuscules avant la recherche lexicale. Recommande sauf si la casse est significative. |
| Remove stopwords | Retirer les mots vides (le, la, de, the, is...) qui n'apportent pas de sens. Recommande. |
| Stopwords lang | Langue des mots vides. `auto` detecte automatiquement. |
| Stemming | Reduire les mots a leur racine (mangeons → mang). Ameliore le rappel mais peut reduire la precision. |
| Reranking provider | Service de reranking qui re-evalue la pertinence des resultats. Cohere offre des modeles de reranking performants. |
| Top N (rerank) | Nombre de resultats a garder apres le reranking. Plus petit que Top K. |
| Candidates | Nombre de resultats envoyes au reranker. Plus grand = meilleure qualite mais plus lent. |
| Relevance threshold (rerank) | Score minimum du reranker pour garder un resultat. |
| Fusion method | `weighted_sum` : combine les scores avec des poids. `reciprocal_rank_fusion` : combine les rangs, plus robuste aux differences d'echelle entre les scores. |
| Normalize scores | Normaliser les scores avant la fusion pour qu'ils soient sur la meme echelle. Recommande. |
| RRF K | Parametre de la fusion RRF. Plus grand = moins de difference entre les rangs. `60` est le defaut standard. |
| Max chunks | Nombre maximum de morceaux de contexte envoyes au LLM. Plus = plus de contexte mais risque de depasser la fenetre du modele. |
| Max tokens | Limite de tokens du contexte injecte dans le prompt. Doit etre inferieur a la fenetre du modele LLM moins la taille de la reponse souhaitee. |
| Deduplication | Supprimer les morceaux trop similaires dans le contexte final. Evite la redondance. |
| Dedup threshold | Seuil de similarite au-dela duquel deux morceaux sont consideres comme doublons. `0.95` est un bon defaut. |

---

## Phase 6 : Tab Agents — Enrichir massivement

Status: DONE

**Fichier :** `ragkit-ui/src/components/config/sections/AgentsConfig.tsx`

### Structure cible :

```
[Mode]              [?] ...... [Select: default, custom]

=== Query Analyzer ===
  [LLM reference]   [?] ...... [Select: primary, secondary, fast]
  [System prompt]   [?] ...... [Textarea, 6 lignes]

  ▼ Behavior (depliable)
    [Always retrieve] [?] .... [ToggleSwitch]
    [Detect intents]  [?] .... [MultiSelect: question, greeting, chitchat, out_of_scope, clarification, + custom]
    [Query rewriting]  [?] ... [ToggleSwitch]
    [Num rewrites]    [?] .... [NumberInput min=1 max=3]  (visible si rewriting enabled)

=== Response Generator ===
  [LLM reference]       [?] .. [Select: primary, secondary, fast]
  [System prompt]       [?] .. [Textarea, 8 lignes, avec note: utiliser {context} comme placeholder]
  [No retrieval prompt] [?] .. [Textarea, 4 lignes]
  [Out of scope prompt] [?] .. [Textarea, 4 lignes]

  ▼ Behavior (depliable)
    [Cite sources]        [?]  [ToggleSwitch]
    [Citation format]     [?]  [Input]
    [Admit uncertainty]   [?]  [ToggleSwitch]
    [Uncertainty phrase]  [?]  [Input]
    [Max response length] [?]  [NumberInput, nullable]
    [Response language]   [?]  [Select: auto, fr, en, es, de, it, pt, + custom]

▼ Global settings (depliable)
  [Timeout]             [?] .. [NumberInput min=1 max=120, unite: secondes]
  [Max retries]         [?] .. [NumberInput min=0 max=5]
  [Retry delay]         [?] .. [NumberInput min=0 max=10, unite: secondes]
  [Verbose]             [?] .. [ToggleSwitch]
```

### Mapping label → tooltip (Agents) :

| Champ | Tooltip |
|-------|---------|
| Mode | `default` : utilise le pipeline standard query → retrieval → response. `custom` : permet d'ajouter des agents personnalises. |
| LLM reference (analyzer) | Quel modele LLM utiliser pour analyser les requetes. `fast` est recommande car l'analyse est une tache simple. |
| System prompt (analyzer) | Instructions donnees au LLM pour analyser les requetes. Le LLM doit retourner un JSON avec l'intent, si la recherche est necessaire, et une version reecrite de la requete. |
| Always retrieve | Si active, effectue toujours une recherche dans la base de connaissances, meme pour les salutations et le hors-sujet. Utile si vous voulez toujours fournir du contexte. |
| Detect intents | Types d'intentions que l'agent doit detecter. `question` : question necessitant une reponse. `greeting` : salutation. `chitchat` : discussion informelle. `out_of_scope` : hors du domaine du RAG. |
| Query rewriting | Reecrire la requete de l'utilisateur pour ameliorer la recherche. Utile quand les requetes sont vagues ou mal formulees. |
| Num rewrites | Nombre de reformulations de la requete. Plus de reformulations = meilleur rappel mais plus de requetes au LLM. |
| LLM reference (generator) | Quel modele LLM utiliser pour generer les reponses. `primary` est recommande pour les meilleures reponses. |
| System prompt (generator) | Instructions donnees au LLM pour generer les reponses. `{context}` sera remplace par les morceaux de documents trouves. |
| No retrieval prompt | Prompt utilise quand aucune recherche n'est necessaire (salutations, chitchat). Le LLM repond sans contexte de documents. |
| Out of scope prompt | Prompt utilise quand la question est hors du domaine du RAG. Le LLM explique poliment que la question est hors-sujet. |
| Cite sources | Inclure les references des sources dans la reponse. Recommande pour la transparence. |
| Citation format | Format des citations dans la reponse. `{source_name}` sera remplace par le nom du fichier source. |
| Admit uncertainty | Si le LLM ne trouve pas de reponse dans le contexte, il l'admet au lieu d'inventer. Recommande. |
| Uncertainty phrase | Phrase utilisee quand le LLM ne peut pas repondre. |
| Max response length | Limite la longueur de la reponse en caracteres. Laisser vide pour aucune limite. |
| Response language | Langue de la reponse. `auto` : repond dans la langue de la question. |
| Timeout (global) | Temps maximum pour le traitement complet d'une requete (analyse + recherche + generation). |
| Max retries (global) | Nombre de tentatives en cas d'echec d'un agent. |
| Verbose | Active les logs detailles des agents. Utile pour le debug. |

---

## Phase 7 : Nouveau tab Embedding dans la page Config

Status: DONE

**Fichier :** `ragkit-ui/src/pages/Config.tsx`

### Etapes :
1. Importer `EmbeddingConfigSection` (creee en Phase 3)
2. Ajouter un `<TabsTrigger value="embedding">Embedding</TabsTrigger>` entre Ingestion et Retrieval
3. Ajouter le `<TabsContent>` correspondant

### Nouvel ordre des tabs :
```
General | Ingestion | Embedding | Retrieval | LLM | Agents
```

---

## Phase 8 : Nouveaux tabs optionnels (avance)

Status: DONE

Ajouter des tabs supplementaires pour les sections restantes du schema. Ces tabs sont dans une zone "Advanced" separee ou en sous-tabs.

### 8.1 — Tab Vector Store

**Fichier a creer :** `ragkit-ui/src/components/config/sections/VectorStoreConfig.tsx`

```
[Provider]          [?] ...... [Select: qdrant, chroma]

--- Si qdrant ---
  [Mode]            [?] ...... [Select: memory, local, cloud]
  [Path]            [?] ...... [Input]  (visible si local)
  [URL]             [?] ...... [Input]  (visible si cloud)
  [API key]         [?] ...... [Input password]  (visible si cloud)
  [Collection name] [?] ...... [Input]
  [Distance metric] [?] ...... [Select: cosine, euclidean, dot]

--- Si chroma ---
  [Mode]            [?] ...... [Select: memory, persistent]
  [Path]            [?] ...... [Input]  (visible si persistent)
  [Collection name] [?] ...... [Input]
```

| Champ | Tooltip |
|-------|---------|
| Provider | Base de donnees vectorielle. `qdrant` : performant, supporte le cloud. `chroma` : simple, bon pour le developpement. |
| Mode (qdrant) | `memory` : rapide, perdu au redemarrage (dev). `local` : persiste sur disque. `cloud` : heberge sur Qdrant Cloud. |
| Distance metric | Methode de calcul de distance entre vecteurs. `cosine` : standard, invariant a la norme. `dot` : produit scalaire, plus rapide. `euclidean` : distance geometrique. |
| Collection name | Nom de la collection dans la base vectorielle. Permet d'avoir plusieurs projets dans la meme base. |

### 8.2 — Tab Conversation

**Fichier a creer :** `ragkit-ui/src/components/config/sections/ConversationConfig.tsx`

```
=== Memory ===
  [Enabled]         [?] ...... [ToggleSwitch]
  [Type]            [?] ...... [Select: buffer_window, summary, none]
  [Window size]     [?] ...... [NumberInput min=1 max=50]  (visible si buffer_window)
  [Include in prompt] [?] .... [ToggleSwitch]

=== Persistence ===
  [Enabled]         [?] ...... [ToggleSwitch]
  [Backend]         [?] ...... [Select: memory, redis, postgresql]
```

| Champ | Tooltip |
|-------|---------|
| Memory enabled | Active la memoire de conversation. Le RAG se souvient des echanges precedents dans la meme session. |
| Memory type | `buffer_window` : garde les N derniers messages. `summary` : resume les echanges precedents. `none` : pas de memoire. |
| Window size | Nombre de messages precedents gardes en memoire. Plus grand = plus de contexte conversationnel mais plus de tokens. |
| Include in prompt | Inclure l'historique de conversation dans le prompt envoye au LLM. |
| Persistence enabled | Sauvegarder les conversations entre les redemarrages du serveur. |
| Persistence backend | `memory` : perdu au redemarrage. `redis` : rapide, necessite Redis. `postgresql` : durable, necessite PostgreSQL. |

### 8.3 — Tab Observability

**Fichier a creer :** `ragkit-ui/src/components/config/sections/ObservabilityConfig.tsx`

```
=== Logging ===
  [Level]       [?] .......... [Select: DEBUG, INFO, WARNING, ERROR]
  [Format]      [?] .......... [Select: text, json]
  ▼ File output (depliable)
    [Enabled]   [?] .......... [ToggleSwitch]
    [Path]      [?] .......... [Input]
    [Rotation]  [?] .......... [Select: daily, weekly, size-based]
    [Retention] [?] .......... [NumberInput, unite: jours]

=== Metrics ===
  [Enabled]     [?] .......... [ToggleSwitch]
  [Track]       [?] .......... [MultiSelect: query_count, query_latency, ingestion_count, ...]
```

### Modification de Config.tsx pour les tabs avances

Ajouter les nouveaux tabs dans une section "Advanced" en dessous des tabs principaux, ou bien dans une deuxieme rangee :

```
General | Ingestion | Embedding | Retrieval | LLM | Agents
Vector Store | Conversation | Observability
```

Ou bien un bouton "Show advanced settings" qui revele les tabs supplementaires.

---

## Phase 9 : Mise a jour des types TypeScript

Status: DONE

**Fichier :** `ragkit-ui/src/types/config.ts`

### Modifications :

1. Ajouter `litellm` au type `EmbeddingModelConfig.provider`
2. Ajouter `deepseek | groq | mistral` au type `LLMModelConfig.provider`
3. Ajouter les champs manquants :
   - `IngestionConfig.parsing.ocr`
   - `IngestionConfig.metadata`
   - `RetrievalConfig.lexical.params` (k1, b)
   - `RetrievalConfig.lexical.preprocessing`
   - `RetrievalConfig.fusion`
   - `RetrievalConfig.context.deduplication`
   - `AgentsConfig` avec tous les sous-champs
   - `ConversationConfig`
   - `ChatbotConfig`
   - `ObservabilityConfig`

---

## Phase 10 : Mise a jour du Wizard (Setup)

Status: DONE

Les memes ameliorations doivent s'appliquer au wizard de premiere configuration.

### Wizard steps a mettre a jour :

1. **SourcesStep.tsx** — ajouter MultiSelect pour patterns, bouton Browse, toggle Recursive, section chunking
2. **EmbeddingStep.tsx** — ajouter ModelSelect, section parametres avances, toggle "same as document"
3. **LLMStep.tsx** — ajouter ModelSelect, section parametres (temperature, max_tokens), champ API key (deja fait dans schema mais manque dans le wizard actuel selon les screenshots)
4. **RetrievalStep.tsx** — ajouter les champs selon l'architecture selectionnee
5. **ReviewStep.tsx** — afficher un resume structure au lieu de JSON brut

### ReviewStep ameliore

Au lieu d'un dump JSON, afficher un resume lisible :
```
Project: Acme KB
Environment: development

Ingestion:
  Source: ./data/documents (*.pdf, *.md, *.txt)
  Chunking: fixed, 512 chars, 50 overlap

Embedding:
  Provider: OpenAI (text-embedding-3-small)

LLM:
  Primary: OpenAI GPT-4o-mini (temperature: 0.7)

Retrieval:
  Architecture: semantic (top_k: 10)
```

---

## Resume des fichiers

### Fichiers a creer

| Fichier | Phase | Description |
|---------|-------|-------------|
| `ragkit-ui/src/components/ui/help-tooltip.tsx` | 0 | Composant tooltip `?` |
| `ragkit-ui/src/components/ui/field-label.tsx` | 0 | Label + tooltip combine |
| `ragkit-ui/src/components/ui/multi-select.tsx` | 0 | Selection multiple de tags |
| `ragkit-ui/src/components/ui/number-input.tsx` | 0 | Input numerique avec min/max |
| `ragkit-ui/src/components/ui/slider-input.tsx` | 0 | Slider avec affichage valeur |
| `ragkit-ui/src/components/ui/toggle-switch.tsx` | 0 | Interrupteur on/off |
| `ragkit-ui/src/components/ui/collapsible-section.tsx` | 0 | Section depliable |
| `ragkit-ui/src/components/ui/model-select.tsx` | 3 | Select de modele avec option custom |
| `ragkit-ui/src/data/models.ts` | 3 | Catalogue de modeles par provider |
| `ragkit-ui/src/components/config/sections/EmbeddingConfig.tsx` | 3 | Section config embedding |
| `ragkit-ui/src/components/config/sections/VectorStoreConfig.tsx` | 8 | Section config vector store |
| `ragkit-ui/src/components/config/sections/ConversationConfig.tsx` | 8 | Section config conversation |
| `ragkit-ui/src/components/config/sections/ObservabilityConfig.tsx` | 8 | Section config observability |

### Fichiers a modifier

| Fichier | Phase | Modifications |
|---------|-------|---------------|
| `ragkit-ui/src/components/config/sections/GeneralConfig.tsx` | 1 | Ajouter FieldLabel + tooltips |
| `ragkit-ui/src/components/config/sections/IngestionConfig.tsx` | 2 | Reecrire : parsing, chunking, OCR, metadata, MultiSelect patterns, bouton Browse |
| `ragkit-ui/src/components/config/sections/LLMConfig.tsx` | 4 | Reecrire : ModelSelect, API key, params, secondary/fast LLM |
| `ragkit-ui/src/components/config/sections/RetrievalConfig.tsx` | 5 | Reecrire : toutes les sous-sections semantic/lexical/rerank/fusion/context |
| `ragkit-ui/src/components/config/sections/AgentsConfig.tsx` | 6 | Reecrire : prompts, behavior, global settings |
| `ragkit-ui/src/pages/Config.tsx` | 7 | Ajouter tab Embedding + tabs avances |
| `ragkit-ui/src/types/config.ts` | 9 | Ajouter tous les types manquants |
| `ragkit-ui/src/components/wizard/steps/SourcesStep.tsx` | 10 | MultiSelect, Browse, Recursive, Chunking |
| `ragkit-ui/src/components/wizard/steps/EmbeddingStep.tsx` | 10 | ModelSelect, params avances |
| `ragkit-ui/src/components/wizard/steps/LLMStep.tsx` | 10 | ModelSelect, params, API key |
| `ragkit-ui/src/components/wizard/steps/RetrievalStep.tsx` | 10 | Champs selon architecture |
| `ragkit-ui/src/components/wizard/steps/ReviewStep.tsx` | 10 | Resume structure au lieu de JSON |

### Backend (optionnel, pour le browse)

| Fichier | Phase | Description |
|---------|-------|-------------|
| `ragkit/api/routes/admin/browse.py` | 2 | Endpoint browse pour lister les dossiers |
| `ragkit/api/routes/admin/__init__.py` | 2 | Enregistrer le nouveau routeur |

---

## Ordre d'implementation recommande

```
Phase 0 (composants UI partagés)
  |
  +---> Phase 1 (General — tooltips)            [rapide, warmup]
  |
  +---> Phase 2 (Ingestion — enrichir)           [plus gros]
  |       |
  |       +---> Phase 10 (Wizard — appliquer les memes ameliorations)
  |
  +---> Phase 3 (Embedding — nouveau tab)
  |
  +---> Phase 4 (LLM — enrichir)
  |
  +---> Phase 5 (Retrieval — enrichir)
  |
  +---> Phase 6 (Agents — enrichir)
  |
  +---> Phase 7 (Config.tsx — ajouter tabs)
  |
  +---> Phase 8 (tabs avances — VectorStore, Conversation, Observability)
  |
  +---> Phase 9 (types TypeScript)               [peut se faire progressivement]
```

**Phase 0** est le prerequis de toutes les autres : les composants UI partages (FieldLabel, MultiSelect, SliderInput...) sont utilises partout.

**Phases 1 a 6** sont independantes entre elles et peuvent etre faites en parallele par plusieurs developpeurs.

**Phase 9** (types) devrait etre mise a jour au fur et a mesure des autres phases.

**Phase 10** (wizard) reutilise les composants et patterns des phases 2-6.
