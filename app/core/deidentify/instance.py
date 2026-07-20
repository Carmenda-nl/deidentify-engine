# ------------------------------------------------------------------------------------------------ #
# Copyright (c) 2026 Carmenda. All rights reserved.                                                #
# This program is distributed under the terms of the PolyForm Noncommercial License 1.0.0          #
# ------------------------------------------------------------------------------------------------ #

"""Manager for the Deidentify FlairTagger instance. holds a single instance of Deidentify."""

from __future__ import annotations

import sys

from deidentify.taggers import FlairTagger
from deidentify.tokenizer import TokenizerFactory

from core.utils.logger import setup_logging
from main.config import settings

logger = setup_logging()


class DeidentifyInstanceManager:
    """Configuring Deidentify FlairTagger instance."""

    def __init__(self) -> None:
        """Initialize the Deidentify instance manager."""
        self.tagger_instance: FlairTagger | None = None

    def create_instance(self) -> FlairTagger:
        """Create the FlairTagger instance, or return the cached one."""
        if self.tagger_instance is not None:
            return self.tagger_instance

        tokenizer = TokenizerFactory().tokenizer(corpus='ons', disable=('tagger', 'ner'))
        self.tagger_instance = FlairTagger(model=settings.deidentify_model, tokenizer=tokenizer, verbose=False)
        sys.stdout.write('\n')  # <-- White space above progress tracker

        return self.tagger_instance
