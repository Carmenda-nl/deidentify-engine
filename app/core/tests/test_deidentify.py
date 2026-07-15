# ------------------------------------------------------------------------------------------------ #
# Copyright (c) 2026 Carmenda. All rights reserved.                                                #
# This program is distributed under the terms of the PolyForm Noncommercial License 1.0.0          #
# ------------------------------------------------------------------------------------------------ #

"""Deidentify tagger end-to-end test.

For complete results, run with arguments.
`pytest -s -v`
"""

from __future__ import annotations

import warnings
from pprint import pformat
from textwrap import indent
from typing import TYPE_CHECKING

import pytest
from core.utils.logger import setup_test_logging
from core.utils.terminal import get_separator_line

with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=FutureWarning)
    warnings.simplefilter('ignore', category=UserWarning)

    from deidentify.base import Document
    from deidentify.taggers import FlairTagger
    from deidentify.tokenizer import TokenizerFactory
    from deidentify.util import mask_annotations

if TYPE_CHECKING:
    from deidentify.base import Document as DocumentType

MODEL_NAME = 'model_bilstmcrf_ons_fast-v0.2.0'

TEXT = (
    'Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen (e: '
    'j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 '
    'oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU.'
)


@pytest.fixture(scope='module')
def tagger() -> FlairTagger:
    """Load the Flair tagger with the ONS tokenizer once for all tests in this module."""
    tokenizer = TokenizerFactory().tokenizer(corpus='ons', disable=('tagger', 'ner'))
    return FlairTagger(model=MODEL_NAME, tokenizer=tokenizer, verbose=False)


@pytest.fixture
def annotated_doc(tagger: FlairTagger) -> DocumentType:
    """Annotate a single test document with the loaded tagger."""
    document = Document(name='test', text=TEXT)
    return tagger.annotate([document])[0]


def test_tagger_exposes_expected_tags(tagger: FlairTagger) -> None:
    """The loaded model exposes at least one recognisable PII tag."""
    logger = setup_test_logging()
    logger.info('\n%s\n', get_separator_line())
    logger.info('Available tags:\n%s', tagger.tags)
    logger.info('\n%s\n', get_separator_line())

    assert tagger.tags


def test_annotate_finds_pii(annotated_doc: DocumentType) -> None:
    """Annotating the sample text yields at least one PII annotation."""
    logger = setup_test_logging()
    logger.info('\n\nINPUT:\n%s', indent(annotated_doc.text, '  '))
    logger.info('\nAnnotations:\n%s\n', indent(pformat(annotated_doc.annotations), '  '))

    assert annotated_doc.annotations


def test_mask_annotations_redacts_pii(annotated_doc: DocumentType) -> None:
    """Masking the annotated document replaces detected PII in the resulting text."""
    logger = setup_test_logging()

    masked_doc = mask_annotations(annotated_doc)
    logger.info('\n\nOUTPUT:\n%s', indent(masked_doc.text, '  '))
    logger.info('\n%s\n', get_separator_line())

    assert masked_doc.text != annotated_doc.text
    assert 'Jan Jansen' not in masked_doc.text
