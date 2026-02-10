"""Tests for advanced ingestion parsing and preprocessing."""

import builtins
import sys
import types

import pytest

from ragkit.config.schema_v2 import DocumentParsingConfig, TextPreprocessingConfig
from ragkit.ingestion.parsers.advanced_pdf_parser import AdvancedPDFParser
from ragkit.ingestion.parsers.image_processor import ImageProcessor
from ragkit.ingestion.parsers.table_extractor import TableExtractor
from ragkit.ingestion.preprocessing import TextPreprocessor

ORIGINAL_IMPORT = builtins.__import__


class TestAdvancedPDFParser:
    """Tests for the advanced PDF parser helpers."""

    @pytest.fixture
    def parser_config(self):
        return DocumentParsingConfig(
            ocr_enabled=True,
            ocr_language=["eng"],
            ocr_engine="tesseract",
            table_extraction_strategy="markdown",
            header_detection=True,
            footer_removal=True,
        )

    @pytest.fixture
    def parser(self, parser_config):
        return AdvancedPDFParser(parser_config)

    def test_table_to_markdown_conversion(self, parser):
        table = [
            ["Name", "Age", "City"],
            ["Alice", "30", "Paris"],
            ["Bob", "25", "London"],
        ]

        markdown = parser._table_to_markdown(table)

        assert "| Name | Age | City |" in markdown
        assert "| --- | --- | --- |" in markdown
        assert "| Alice | 30 | Paris |" in markdown
        assert "| Bob | 25 | London |" in markdown

    def test_table_to_text_conversion(self, parser):
        table = [
            ["A", "B"],
            ["1", "2"],
        ]
        text = parser._table_to_text(table)
        assert "A | B" in text
        assert "1 | 2" in text

    @pytest.mark.asyncio
    async def test_parse_page_with_tables_and_images(self, parser):
        class DummyTable:
            def __init__(self, rows):
                self._rows = rows
                self.bbox = (0, 0, 1, 1)

            def extract(self):
                return self._rows

        class DummyPage:
            width = 100
            height = 200

            def __init__(self):
                self.images = [{"bbox": (0, 0, 10, 10), "width": 10, "height": 10, "object_id": 1}]

            def extract_text(self):
                return "Header\nBody text"

            def find_tables(self):
                return [DummyTable([["A", "B"], ["1", "2"]])]

        parser.config.image_extraction_enabled = True
        parser.config.table_extraction_strategy = "markdown"
        page_data = await parser._parse_page(DummyPage(), 1)

        assert page_data["tables"]
        assert page_data["images"]

    def test_footer_removal(self, parser):
        text_with_footer = "This is the main content.\n\nPage 1"
        cleaned = parser._remove_footer(text_with_footer)

        assert "Page 1" not in cleaned
        assert "main content" in cleaned

    def test_footer_removal_keeps_long_footer(self, parser):
        text_with_footer = (
            "Content line\nThis footer line is definitely longer than fifty characters."
        )
        cleaned = parser._remove_footer(text_with_footer)
        assert cleaned == text_with_footer

    def test_header_detection(self, parser):
        text = "CHAPTER 1\n\nThis is content\n\nSECTION A\n\nMore content"
        headers = parser._detect_headers(text)

        assert len(headers) >= 2
        assert any(h["text"] == "CHAPTER 1" for h in headers)
        assert any(h["text"] == "SECTION A" for h in headers)

    def test_header_detection_numeric_and_long(self, parser):
        long_line = "L" * 130
        text = f"{long_line}\n1 Introduction\n"
        headers = parser._detect_headers(text)
        assert any(h["text"] == "1 Introduction" for h in headers)
        assert all(h["text"] != long_line for h in headers)

    def test_remove_page_number(self, parser):
        text = "Header\nPage 3\nBody"
        cleaned = parser._remove_page_number(text, 3)
        assert "Page 3" not in cleaned

    @pytest.mark.asyncio
    async def test_parse_page_triggers_ocr_and_captioning(self, parser, monkeypatch):
        class DummyPage:
            width = 100
            height = 200

            def extract_text(self):
                return ""

            def find_tables(self):
                return []

        async def dummy_ocr(page):
            return "ocr result"

        async def dummy_extract_images(page, page_num):
            return [{"data": b"img"}]

        async def dummy_caption(data):
            return "caption"

        parser.config.ocr_enabled = True
        parser.config.image_extraction_enabled = True
        parser.config.image_captioning_enabled = True
        parser.config.footer_removal = False
        parser.config.page_number_removal = False

        monkeypatch.setattr(parser, "_ocr_page", dummy_ocr)
        monkeypatch.setattr(parser._image_processor, "extract_images", dummy_extract_images)
        monkeypatch.setattr(parser._image_processor, "generate_caption", dummy_caption)

        page_data = await parser._parse_page(DummyPage(), 1)
        assert page_data["text"] == "ocr result"
        assert page_data["images"][0]["caption"] == "caption"

    def test_merge_pages_with_separate_tables(self, parser):
        parser.config.preserve_formatting = True
        parser.config.table_extraction_strategy = "separate"
        pages = [
            {
                "page_number": 1,
                "text": "Body",
                "tables": [{"type": "separate_chunk", "content": "A | B"}],
            }
        ]
        merged = parser._merge_pages(pages)
        assert "--- Page 1 ---" in merged
        assert "[TABLE]" in merged

    @pytest.mark.asyncio
    async def test_parse_errors_and_pdfplumber_missing(self, parser_config, tmp_path, monkeypatch):
        parser = AdvancedPDFParser(parser_config)
        missing_file = tmp_path / "missing.pdf"
        with pytest.raises(ValueError):
            await parser.parse(missing_file)

        not_pdf = tmp_path / "file.txt"
        not_pdf.write_text("content")
        with pytest.raises(ValueError):
            await parser.parse(not_pdf)

        def fake_import(name, *args, **kwargs):
            if name == "pdfplumber":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        dummy_pdf = tmp_path / "sample.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4")
        with pytest.raises(RuntimeError):
            await parser.parse(dummy_pdf)

    @pytest.mark.asyncio
    async def test_ocr_page_low_confidence(self, parser, monkeypatch):
        class DummyImage:
            pass

        class DummyPage:
            def to_image(self, resolution: int):
                return types.SimpleNamespace(original=DummyImage())

        class DummyEngine:
            async def extract_text(self, image):
                return "ocr text", 0.5

        parser._ocr_engine = DummyEngine()
        parser.config.ocr_confidence_threshold = 0.6
        text = await parser._ocr_page(DummyPage())
        assert text == "ocr text"

    @pytest.mark.asyncio
    async def test_ocr_page_initializes_engine(self, parser, monkeypatch):
        class DummyImage:
            pass

        class DummyPage:
            def to_image(self, resolution: int):
                return types.SimpleNamespace(original=DummyImage())

        class DummyEngine:
            def __init__(self, engine, languages, dpi, preprocessing):
                self.engine = engine
                self.languages = languages
                self.dpi = dpi
                self.preprocessing = preprocessing

            async def extract_text(self, image):
                return "ok", 0.9

        monkeypatch.setattr(
            "ragkit.ingestion.parsers.advanced_pdf_parser.OCREngine",
            DummyEngine,
        )

        parser._ocr_engine = None
        text = await parser._ocr_page(DummyPage())
        assert text == "ok"
        assert isinstance(parser._ocr_engine, DummyEngine)

    @pytest.mark.asyncio
    async def test_parse_with_stub_pdfplumber(self, parser_config, tmp_path, monkeypatch):
        dummy_file = tmp_path / "sample.pdf"
        dummy_file.write_bytes(b"%PDF-1.4")

        class DummyPage:
            width = 100
            height = 200

            def extract_text(self):
                return "Hello world"

            def find_tables(self):
                return []

        class DummyPDF:
            def __init__(self):
                self.pages = [DummyPage()]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        dummy_module = types.SimpleNamespace(open=lambda path: DummyPDF())
        monkeypatch.setitem(sys.modules, "pdfplumber", dummy_module)

        parser = AdvancedPDFParser(parser_config)
        parser.config.ocr_enabled = False
        parser.config.skip_empty_pages = False
        parser.config.footer_removal = False
        parser.config.page_number_removal = False
        parsed = await parser.parse(dummy_file)

        assert "Hello world" in parsed.content
        assert parsed.metadata["total_pages"] == 1


class TestTextPreprocessing:
    """Tests for text preprocessing."""

    def test_url_removal(self):
        config = TextPreprocessingConfig(remove_urls=True)
        preprocessor = TextPreprocessor(config)

        text = "Check out https://example.com for more info"
        result = preprocessor.process(text)

        assert "https://example.com" not in result
        assert "Check out" in result
        assert "for more info" in result

    def test_email_removal(self):
        config = TextPreprocessingConfig(remove_emails=True)
        preprocessor = TextPreprocessor(config)

        text = "Contact us at support@example.com"
        result = preprocessor.process(text)

        assert "support@example.com" not in result
        assert "Contact us at" in result

    def test_phone_removal(self):
        config = TextPreprocessingConfig(remove_phone_numbers=True)
        preprocessor = TextPreprocessor(config)

        text = "Call 555-123-4567 for assistance"
        result = preprocessor.process(text)

        assert "555-123-4567" not in result
        assert "Call" in result

    def test_unicode_normalization(self):
        config = TextPreprocessingConfig(normalize_unicode="NFC")
        preprocessor = TextPreprocessor(config)

        text = "café"
        result = preprocessor.process(text)

        assert result == "café"

    def test_non_string_input(self):
        config = TextPreprocessingConfig()
        preprocessor = TextPreprocessor(config)
        result = preprocessor.process(1234)
        assert result == "1234"

    def test_remove_punctuation_and_lowercase(self):
        config = TextPreprocessingConfig(remove_punctuation=True, lowercase=True)
        preprocessor = TextPreprocessor(config)
        text = "Hello, WORLD!"
        result = preprocessor.process(text)
        assert result == "hello world"

    def test_whitespace_normalization(self):
        config = TextPreprocessingConfig(
            normalize_whitespace=True,
            remove_extra_newlines=True,
        )
        preprocessor = TextPreprocessor(config)

        text = "This  has   multiple    spaces\n\n\n\nAnd newlines"
        result = preprocessor.process(text)

        assert "  " not in result
        assert "\n\n\n" not in result

    def test_special_and_control_characters(self):
        config = TextPreprocessingConfig(
            remove_special_characters=True,
            remove_control_characters=True,
        )
        preprocessor = TextPreprocessor(config)

        text = "Hello\x00 world!#$"
        result = preprocessor.process(text)

        assert "\x00" not in result
        assert "!" not in result

    def test_deduplication_exact(self):
        config = TextPreprocessingConfig(deduplication_strategy="exact")
        preprocessor = TextPreprocessor(config)

        existing = ["This is a test document"]

        assert preprocessor.check_duplicate("This is a test document", existing) is True
        assert preprocessor.check_duplicate("This is different", existing) is False

    def test_deduplication_none(self):
        config = TextPreprocessingConfig(deduplication_strategy="none")
        preprocessor = TextPreprocessor(config)
        assert preprocessor.check_duplicate("x", ["x"]) is False

    def test_deduplication_unknown_strategy(self):
        config = TextPreprocessingConfig.model_construct(deduplication_strategy="weird")
        preprocessor = TextPreprocessor(config)
        assert preprocessor.check_duplicate("x", ["x"]) is False

    def test_deduplication_fuzzy(self):
        config = TextPreprocessingConfig(
            deduplication_strategy="fuzzy",
            deduplication_threshold=0.9,
        )
        preprocessor = TextPreprocessor(config)

        existing = ["This is a test document for deduplication"]

        assert (
            preprocessor.check_duplicate("This is a test document for deduplicaton", existing)
            is True
        )

        assert preprocessor.check_duplicate("Completely different text here", existing) is False

    def test_deduplication_semantic(self):
        import numpy as np

        config = TextPreprocessingConfig(
            deduplication_strategy="semantic",
            deduplication_threshold=0.9,
        )

        def embedder(texts):
            return [
                np.array([1.0, 0.0]) if i == 0 else np.array([1.0, 0.0]) for i in range(len(texts))
            ]

        preprocessor = TextPreprocessor(config, embedder=embedder)
        assert preprocessor.check_duplicate("test", ["test"]) is True

    def test_deduplication_semantic_without_embedder(self):
        config = TextPreprocessingConfig(deduplication_strategy="semantic")
        preprocessor = TextPreprocessor(config)
        assert preprocessor.check_duplicate("test", ["test"]) is False

    def test_deduplication_semantic_invalid_embeddings(self):
        config = TextPreprocessingConfig(deduplication_strategy="semantic")

        def embedder(_texts):
            return None

        preprocessor = TextPreprocessor(config, embedder=embedder)
        assert preprocessor.check_duplicate("test", ["a"]) is False

    def test_deduplication_semantic_length_mismatch(self):
        config = TextPreprocessingConfig(deduplication_strategy="semantic")

        def embedder(_texts):
            return [[1.0, 0.0]]

        preprocessor = TextPreprocessor(config, embedder=embedder)
        assert preprocessor.check_duplicate("test", ["a"]) is False

    def test_deduplication_semantic_numpy_missing(self, monkeypatch):
        config = TextPreprocessingConfig(deduplication_strategy="semantic")

        def embedder(_texts):
            return [[1.0, 0.0], [1.0, 0.0]]

        preprocessor = TextPreprocessor(config, embedder=embedder)

        def fake_import(name, *args, **kwargs):
            if name == "numpy":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        assert preprocessor.check_duplicate("test", ["a"]) is False

    def test_deduplication_semantic_scalar_embedding(self):
        config = TextPreprocessingConfig(deduplication_strategy="semantic")

        def embedder(_texts):
            return [1.0, 2.0]

        preprocessor = TextPreprocessor(config, embedder=embedder)
        assert preprocessor.check_duplicate("test", ["a"]) is False

    def test_deduplication_semantic_invalid_rank(self):
        config = TextPreprocessingConfig(deduplication_strategy="semantic")

        def embedder(_texts):
            return [[[1.0, 2.0]], [[1.0, 2.0]]]

        preprocessor = TextPreprocessor(config, embedder=embedder)
        assert preprocessor.check_duplicate("test", ["a"]) is False

    @pytest.mark.asyncio
    async def test_language_detection(self):
        config = TextPreprocessingConfig(
            language_detection=True,
            language_detector="langdetect",
        )
        preprocessor = TextPreprocessor(config)

        text_en = "This is a sample text in English"
        lang = await preprocessor.detect_language(text_en)
        assert lang == "en"

        text_fr = (
            "Ceci est un texte en français avec plusieurs phrases pour "
            "améliorer la détection automatique de la langue."
        )
        lang = await preprocessor.detect_language(text_fr)
        assert lang == "fr"

    @pytest.mark.asyncio
    async def test_language_detection_disabled_and_short_text(self):
        config = TextPreprocessingConfig(language_detection=False)
        preprocessor = TextPreprocessor(config)
        lang = await preprocessor.detect_language("short")
        assert lang == "en"

        config = TextPreprocessingConfig(
            language_detection=True,
            min_text_length_for_detection=100,
        )
        preprocessor = TextPreprocessor(config)
        lang = await preprocessor.detect_language("too short")
        assert lang == "en"

    @pytest.mark.asyncio
    async def test_language_detection_langdetect_missing(self, monkeypatch):
        config = TextPreprocessingConfig(
            language_detection=True,
            language_detector="langdetect",
        )
        preprocessor = TextPreprocessor(config)

        def fake_import(name, *args, **kwargs):
            if name == "langdetect":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        long_text = (
            "This is a sample text in English that is long enough to trigger "
            "language detection in the preprocessing pipeline."
        )
        lang = await preprocessor.detect_language(long_text)
        assert lang == "en"

    @pytest.mark.asyncio
    async def test_language_detection_langid(self, monkeypatch):
        config = TextPreprocessingConfig(
            language_detection=True,
            language_detector="langid",
        )
        preprocessor = TextPreprocessor(config)

        dummy_langid = types.SimpleNamespace(classify=lambda text: ("fr", 1.0))
        monkeypatch.setitem(sys.modules, "langid", dummy_langid)

        long_text = (
            "Texte en français suffisamment long pour dépasser la limite "
            "de détection et valider le chemin langid correctement."
        )
        lang = await preprocessor.detect_language(long_text)
        assert lang == "fr"

    @pytest.mark.asyncio
    async def test_language_detection_langid_missing(self, monkeypatch):
        config = TextPreprocessingConfig(
            language_detection=True,
            language_detector="langid",
        )
        preprocessor = TextPreprocessor(config)

        def fake_import(name, *args, **kwargs):
            if name == "langid":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        long_text = (
            "Texte en français suffisamment long pour dépasser la limite "
            "de détection et forcer l'échec de l'import langid."
        )
        lang = await preprocessor.detect_language(long_text)
        assert lang == "en"

    @pytest.mark.asyncio
    async def test_language_detection_fasttext(self, monkeypatch):
        config = TextPreprocessingConfig(
            language_detection=True,
            language_detector="fasttext",
        )
        preprocessor = TextPreprocessor(config)

        class DummyModel:
            def predict(self, text, k=1):
                return (["__label__en"], [0.99])

        dummy_fasttext = types.SimpleNamespace(load_model=lambda path: DummyModel())
        monkeypatch.setitem(sys.modules, "fasttext", dummy_fasttext)

        long_text = (
            "This is a sufficiently long text for detection that should "
            "trigger the fasttext branch in language detection."
        )
        lang = await preprocessor.detect_language(long_text)
        assert lang == "en"

    @pytest.mark.asyncio
    async def test_language_detection_fasttext_missing(self, monkeypatch):
        config = TextPreprocessingConfig(
            language_detection=True,
            language_detector="fasttext",
        )
        preprocessor = TextPreprocessor(config)

        def fake_import(name, *args, **kwargs):
            if name == "fasttext":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        long_text = (
            "This is a sufficiently long text for detection that should "
            "trigger the fasttext branch and then fail on import."
        )
        lang = await preprocessor.detect_language(long_text)
        assert lang == "en"

    def test_custom_regex_filters(self):
        config = TextPreprocessingConfig(custom_regex_filters=[r"\d{3}-\d{3}-\d{4}"])
        preprocessor = TextPreprocessor(config)

        text = "Call me at 555-123-4567 please"
        result = preprocessor.process(text)

        assert "555-123-4567" not in result
        assert "Call me at" in result

    def test_custom_replacement_rules(self):
        config = TextPreprocessingConfig(
            custom_replacement_rules={
                "REDACTED": "[REMOVED]",
                "confidential": "public",
            }
        )
        preprocessor = TextPreprocessor(config)

        text = "This is REDACTED and confidential"
        result = preprocessor.process(text)

        assert "[REMOVED]" in result
        assert "public" in result
        assert "REDACTED" not in result
        assert "confidential" not in result

    def test_stopwords_missing_nltk(self, monkeypatch):
        def fake_import(name, *args, **kwargs):
            if name == "nltk":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        config = TextPreprocessingConfig(remove_stopwords=True)
        preprocessor = TextPreprocessor(config)
        assert preprocessor.process("keep words") == "keep words"

    def test_stopwords_removal_with_stub(self, monkeypatch):
        class DummyStopwords:
            @staticmethod
            def words(lang):
                return ["this", "is"]

        dummy_corpus = types.SimpleNamespace(stopwords=DummyStopwords)

        class DummyData:
            @staticmethod
            def find(name):
                raise LookupError()

        dummy_nltk = types.SimpleNamespace(
            data=DummyData(),
            download=lambda *args, **kwargs: None,
        )

        monkeypatch.setitem(sys.modules, "nltk", dummy_nltk)
        monkeypatch.setitem(sys.modules, "nltk.corpus", dummy_corpus)

        config = TextPreprocessingConfig(remove_stopwords=True)
        preprocessor = TextPreprocessor(config)

        text = "this is a test"
        result = preprocessor.process(text)

        assert "this" not in result
        assert "is" not in result

    def test_stopwords_words_failure(self, monkeypatch):
        class DummyStopwords:
            @staticmethod
            def words(lang):
                raise RuntimeError("broken")

        dummy_corpus = types.SimpleNamespace(stopwords=DummyStopwords)

        class DummyData:
            @staticmethod
            def find(name):
                return True

        dummy_nltk = types.SimpleNamespace(
            data=DummyData(),
            download=lambda *args, **kwargs: None,
        )

        monkeypatch.setitem(sys.modules, "nltk", dummy_nltk)
        monkeypatch.setitem(sys.modules, "nltk.corpus", dummy_corpus)

        config = TextPreprocessingConfig(remove_stopwords=True)
        preprocessor = TextPreprocessor(config)
        result = preprocessor.process("keep words")
        assert result == "keep words"

    def test_fix_encoding_errors_exception(self):
        config = TextPreprocessingConfig()
        preprocessor = TextPreprocessor(config)

        class BrokenText:
            def encode(self, *args, **kwargs):
                raise UnicodeError("boom")

            def __str__(self):
                return "broken"

        broken = BrokenText()
        result = preprocessor._fix_encoding_errors(broken)
        assert result is broken


class TestOCREngine:
    """Tests for the OCR engine wrapper."""

    def test_image_preprocessing(self):
        pil = pytest.importorskip("PIL")
        from ragkit.utils.ocr import OCREngine

        engine = OCREngine(
            engine="tesseract",
            languages=["eng"],
            preprocessing=True,
        )

        img = pil.Image.new("RGB", (100, 100), color="gray")
        processed = engine._preprocess_image(img)

        assert processed.mode == "L"

    @pytest.mark.asyncio
    async def test_extract_text_with_preprocessing_tesseract(self, monkeypatch):
        pil = pytest.importorskip("PIL")
        from ragkit.utils.ocr import OCREngine

        dummy = types.SimpleNamespace(
            image_to_string=lambda image, lang=None: "text",
            image_to_data=lambda image, lang=None, output_type=None: {"conf": ["100"]},
            Output=types.SimpleNamespace(DICT="dict"),
        )
        monkeypatch.setitem(sys.modules, "pytesseract", dummy)

        engine = OCREngine(engine="tesseract", languages=["eng"], preprocessing=True)
        img = pil.Image.new("RGB", (10, 10), color="white")
        text, confidence = await engine.extract_text(img)
        assert text == "text"
        assert confidence == 1.0

    @pytest.mark.asyncio
    async def test_tesseract_backend(self, monkeypatch):
        from ragkit.utils.ocr import OCREngine

        dummy = types.SimpleNamespace(
            image_to_string=lambda image, lang=None: "text",
            image_to_data=lambda image, lang=None, output_type=None: {"conf": ["50", "100"]},
            Output=types.SimpleNamespace(DICT="dict"),
        )
        monkeypatch.setitem(sys.modules, "pytesseract", dummy)

        engine = OCREngine(engine="tesseract", languages=["eng"], preprocessing=False)
        text, confidence = await engine._ocr_tesseract(object())
        assert text == "text"
        assert confidence == 0.75

    @pytest.mark.asyncio
    async def test_tesseract_missing_dependency(self, monkeypatch):
        from ragkit.utils.ocr import OCREngine

        def fake_import(name, *args, **kwargs):
            if name == "pytesseract":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        engine = OCREngine(engine="tesseract", languages=["eng"], preprocessing=False)
        with pytest.raises(RuntimeError):
            await engine._ocr_tesseract(object())

    @pytest.mark.asyncio
    async def test_easyocr_backend(self, monkeypatch):
        import numpy as np

        from ragkit.utils.ocr import OCREngine

        class DummyReader:
            def readtext(self, image_np):
                return [(None, "hello", 0.9)]

        dummy_easyocr = types.SimpleNamespace(Reader=lambda langs: DummyReader())
        monkeypatch.setitem(sys.modules, "easyocr", dummy_easyocr)

        engine = OCREngine(engine="easyocr", languages=["en"], preprocessing=False)
        text, confidence = await engine.extract_text(np.zeros((1, 1)))
        assert text == "hello"
        assert confidence == 0.9

    @pytest.mark.asyncio
    async def test_easyocr_missing_numpy(self, monkeypatch):
        from ragkit.utils.ocr import OCREngine

        def fake_import(name, *args, **kwargs):
            if name == "numpy":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        engine = OCREngine(engine="easyocr", languages=["en"], preprocessing=False)
        engine._ocr_instance = types.SimpleNamespace(readtext=lambda x: [])
        with pytest.raises(RuntimeError):
            await engine._ocr_easyocr(object())

    @pytest.mark.asyncio
    async def test_easyocr_uninitialized_instance(self):
        import numpy as np

        from ragkit.utils.ocr import OCREngine

        engine = OCREngine(engine="easyocr", languages=["en"], preprocessing=False)
        engine._ocr_instance = None
        with pytest.raises(RuntimeError):
            await engine._ocr_easyocr(np.zeros((1, 1)))

    @pytest.mark.asyncio
    async def test_doctr_backend(self, monkeypatch):
        import numpy as np

        from ragkit.utils.ocr import OCREngine

        class DummyResult:
            def render(self):
                return "doctr text"

        class DummyPredictor:
            def __call__(self, images):
                return DummyResult()

        dummy_models = types.SimpleNamespace(ocr_predictor=lambda pretrained=True: DummyPredictor())
        dummy_doctr = types.SimpleNamespace(models=dummy_models)

        monkeypatch.setitem(sys.modules, "doctr", dummy_doctr)
        monkeypatch.setitem(sys.modules, "doctr.models", dummy_models)

        engine = OCREngine(engine="doctr", languages=["en"], preprocessing=False)
        text, confidence = await engine.extract_text(np.zeros((1, 1)))
        assert text == "doctr text"
        assert confidence == 0.9

    @pytest.mark.asyncio
    async def test_doctr_missing_numpy(self, monkeypatch):
        from ragkit.utils.ocr import OCREngine

        def fake_import(name, *args, **kwargs):
            if name == "numpy":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        engine = OCREngine(engine="doctr", languages=["en"], preprocessing=False)
        engine._ocr_instance = types.SimpleNamespace(__call__=lambda self, images: None)
        with pytest.raises(RuntimeError):
            await engine._ocr_doctr(object())

    @pytest.mark.asyncio
    async def test_doctr_uninitialized_instance(self):
        import numpy as np

        from ragkit.utils.ocr import OCREngine

        engine = OCREngine(engine="doctr", languages=["en"], preprocessing=False)
        engine._ocr_instance = None
        with pytest.raises(RuntimeError):
            await engine._ocr_doctr(np.zeros((1, 1)))

    def test_init_ocr_missing_backends(self, monkeypatch):
        from ragkit.utils.ocr import OCREngine

        def fake_import(name, *args, **kwargs):
            if name in {"easyocr", "doctr"}:
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        engine = OCREngine(engine="easyocr", languages=["en"], preprocessing=False)
        with pytest.raises(RuntimeError):
            engine._init_ocr()

        engine = OCREngine(engine="doctr", languages=["en"], preprocessing=False)
        with pytest.raises(RuntimeError):
            engine._init_ocr()

    @pytest.mark.asyncio
    async def test_unsupported_engine(self):
        pil = pytest.importorskip("PIL")
        from ragkit.utils.ocr import OCREngine

        engine = OCREngine(engine="unknown", languages=["en"], preprocessing=False)
        img = pil.Image.new("RGB", (10, 10), color="white")
        with pytest.raises(RuntimeError):
            await engine.extract_text(img)

    def test_init_ocr_returns_none_for_tesseract(self):
        from ragkit.utils.ocr import OCREngine

        engine = OCREngine(engine="tesseract", languages=["en"], preprocessing=False)
        assert engine._init_ocr() is None


class TestTableExtractor:
    """Tests for table extraction strategies."""

    @pytest.mark.asyncio
    async def test_extract_tables_markdown(self):
        config = DocumentParsingConfig(table_extraction_strategy="markdown")
        extractor = TableExtractor(config)

        class DummyTable:
            def __init__(self, rows):
                self._rows = rows
                self.bbox = (0, 0, 1, 1)

            def extract(self):
                return self._rows

        class DummyPage:
            def find_tables(self):
                return [DummyTable([["X", "Y"], ["1", "2"]])]

        tables = await extractor.extract_tables(DummyPage())
        assert tables[0]["type"] == "markdown"
        assert "| X | Y |" in tables[0]["content"]

    @pytest.mark.asyncio
    async def test_extract_tables_none(self):
        config = DocumentParsingConfig(table_extraction_strategy="none")
        extractor = TableExtractor(config)

        class DummyPage:
            def find_tables(self):
                return []

        tables = await extractor.extract_tables(DummyPage())
        assert tables == []

    @pytest.mark.asyncio
    async def test_extract_tables_vision(self):
        config = DocumentParsingConfig(table_extraction_strategy="vision")
        extractor = TableExtractor(config)

        class DummyPage:
            def find_tables(self):
                return []

        tables = await extractor.extract_tables(DummyPage())
        assert tables == []

    @pytest.mark.asyncio
    async def test_extract_tables_find_tables_error(self):
        config = DocumentParsingConfig(table_extraction_strategy="markdown")
        extractor = TableExtractor(config)

        class DummyPage:
            def find_tables(self):
                raise RuntimeError("boom")

        tables = await extractor.extract_tables(DummyPage())
        assert tables == []

    @pytest.mark.asyncio
    async def test_extract_tables_preserve(self):
        config = DocumentParsingConfig(table_extraction_strategy="preserve")
        extractor = TableExtractor(config)

        class DummyTable:
            def __init__(self, rows):
                self._rows = rows
                self.bbox = (0, 0, 1, 1)

            def extract(self):
                return self._rows

        class DummyPage:
            def find_tables(self):
                return [DummyTable([["X", "Y"], ["1", "2"]])]

        tables = await extractor.extract_tables(DummyPage())
        assert tables[0]["type"] == "structured"
        assert tables[0]["rows"]

    @pytest.mark.asyncio
    async def test_extract_tables_separate(self):
        config = DocumentParsingConfig(table_extraction_strategy="separate")
        extractor = TableExtractor(config)

        class DummyTable:
            def __init__(self, rows):
                self._rows = rows
                self.bbox = (0, 0, 1, 1)

            def extract(self):
                return self._rows

        class DummyPage:
            def find_tables(self):
                return [DummyTable([["X", "Y"], ["1", "2"]])]

        tables = await extractor.extract_tables(DummyPage())
        assert tables[0]["type"] == "separate_chunk"
        assert "|" in tables[0]["content"]

    @pytest.mark.asyncio
    async def test_extract_tables_empty_and_truncation(self):
        config = DocumentParsingConfig(
            table_extraction_strategy="markdown",
            table_max_rows=1,
            table_max_columns=1,
        )
        extractor = TableExtractor(config)

        class DummyTable:
            def __init__(self, rows):
                self._rows = rows
                self.bbox = (0, 0, 1, 1)

            def extract(self):
                return self._rows

        class DummyPage:
            def find_tables(self):
                return [
                    DummyTable([]),
                    DummyTable([["A", "B"], ["1", "2"]]),
                ]

        tables = await extractor.extract_tables(DummyPage())
        assert len(tables) == 1
        assert "| A |" in tables[0]["content"]

    def test_table_to_markdown_empty(self):
        config = DocumentParsingConfig(table_extraction_strategy="markdown")
        extractor = TableExtractor(config)
        assert extractor._table_to_markdown([]) == ""


class TestImageProcessor:
    """Tests for image extraction metadata."""

    @pytest.mark.asyncio
    async def test_extract_images_from_page(self):
        config = DocumentParsingConfig(image_extraction_enabled=True)
        processor = ImageProcessor(config)

        class DummyPage:
            images = [{"bbox": (0, 0, 5, 5), "width": 5, "height": 5, "object_id": 42}]

        images = await processor.extract_images(DummyPage(), 1)
        assert len(images) == 1
        assert images[0]["object_id"] == 42

    @pytest.mark.asyncio
    async def test_extract_images_without_images_attr(self):
        config = DocumentParsingConfig(image_extraction_enabled=True)
        processor = ImageProcessor(config)

        class DummyPage:
            pass

        images = await processor.extract_images(DummyPage(), 1)
        assert images == []

    @pytest.mark.asyncio
    async def test_generate_caption_empty_bytes(self):
        config = DocumentParsingConfig(image_captioning_model="dummy")
        processor = ImageProcessor(config)
        caption = await processor.generate_caption(b"")
        assert caption == ""

    @pytest.mark.asyncio
    async def test_generate_caption_missing_transformers(self, monkeypatch):
        config = DocumentParsingConfig(image_captioning_model="dummy")
        processor = ImageProcessor(config)

        monkeypatch.setitem(sys.modules, "transformers", types.SimpleNamespace())
        caption = await processor.generate_caption(b"img")
        assert caption == ""

    @pytest.mark.asyncio
    async def test_generate_caption_missing_pillow(self, monkeypatch):
        class DummyProcessor:
            @classmethod
            def from_pretrained(cls, name):
                return cls()

            def __call__(self, image, return_tensors="pt"):
                return {"pixel_values": [1]}

            def decode(self, output, skip_special_tokens=True):
                return "caption"

        class DummyModel:
            @classmethod
            def from_pretrained(cls, name):
                return cls()

            def generate(self, **inputs):
                return [[1, 2, 3]]

        dummy_transformers = types.SimpleNamespace(
            BlipProcessor=DummyProcessor,
            BlipForConditionalGeneration=DummyModel,
        )
        monkeypatch.setitem(sys.modules, "transformers", dummy_transformers)

        def fake_import(name, *args, **kwargs):
            if name == "PIL":
                raise ImportError("missing")
            return ORIGINAL_IMPORT(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        config = DocumentParsingConfig(image_captioning_model="dummy")
        processor = ImageProcessor(config)
        caption = await processor.generate_caption(b"img")
        assert caption == ""

    @pytest.mark.asyncio
    async def test_generate_caption_invalid_image(self, monkeypatch):
        class DummyImageModule:
            @staticmethod
            def open(buffer):
                raise ValueError("bad image")

        dummy_pil = types.SimpleNamespace(Image=DummyImageModule)
        monkeypatch.setitem(sys.modules, "PIL", dummy_pil)
        monkeypatch.setitem(sys.modules, "PIL.Image", DummyImageModule)

        class DummyProcessor:
            @classmethod
            def from_pretrained(cls, name):
                return cls()

            def __call__(self, image, return_tensors="pt"):
                return {"pixel_values": [1]}

            def decode(self, output, skip_special_tokens=True):
                return "caption"

        class DummyModel:
            @classmethod
            def from_pretrained(cls, name):
                return cls()

            def generate(self, **inputs):
                return [[1, 2, 3]]

        dummy_transformers = types.SimpleNamespace(
            BlipProcessor=DummyProcessor,
            BlipForConditionalGeneration=DummyModel,
        )
        monkeypatch.setitem(sys.modules, "transformers", dummy_transformers)

        config = DocumentParsingConfig(image_captioning_model="dummy")
        processor = ImageProcessor(config)
        caption = await processor.generate_caption(b"img")
        assert caption == ""

    @pytest.mark.asyncio
    async def test_generate_caption_with_stub(self, monkeypatch):
        class DummyImage:
            def convert(self, mode):
                return self

        class DummyImageModule:
            @staticmethod
            def open(buffer):
                return DummyImage()

        dummy_pil = types.SimpleNamespace(Image=DummyImageModule)
        monkeypatch.setitem(sys.modules, "PIL", dummy_pil)
        monkeypatch.setitem(sys.modules, "PIL.Image", DummyImageModule)

        class DummyProcessor:
            @classmethod
            def from_pretrained(cls, name):
                return cls()

            def __call__(self, image, return_tensors="pt"):
                return {"pixel_values": [1]}

            def decode(self, output, skip_special_tokens=True):
                return "caption"

        class DummyModel:
            @classmethod
            def from_pretrained(cls, name):
                return cls()

            def generate(self, **inputs):
                return [[1, 2, 3]]

        dummy_transformers = types.SimpleNamespace(
            BlipProcessor=DummyProcessor,
            BlipForConditionalGeneration=DummyModel,
        )
        monkeypatch.setitem(sys.modules, "transformers", dummy_transformers)

        config = DocumentParsingConfig(image_captioning_model="dummy")
        processor = ImageProcessor(config)
        caption = await processor.generate_caption(b"image-bytes")
        assert caption == "caption"
