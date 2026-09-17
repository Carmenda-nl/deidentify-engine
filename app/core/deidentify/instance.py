# ------------------------------------------------------------------------------------------------ #
# Copyright (c) 2026 Carmenda. All rights reserved.                                                #
# This program is distributed under the terms of the PolyForm Noncommercial License 1.0.0          #
# ------------------------------------------------------------------------------------------------ #

"""Manager for the Deidentify FlairTagger instance. holds a single instance of Deidentify."""

from __future__ import annotations

import sys
from pathlib import Path

from deidentify.taggers import FlairTagger
from deidentify.tokenizer import TokenizerFactory

from core.utils.logger import setup_logging
from main.config import settings

logger = setup_logging()


class DeidentifyInstanceManager:
    """Configuring Deidentify FlairTagger instance."""

    def __init__(self, model_path: str | None = None) -> None:
        """Initialize the Deidentify instance manager."""
        self.model_path = self._resolve_model_path(model_path)
        self.tagger_instance: FlairTagger | None = None

    def _resolve_model_path(self, provided_path: str | None) -> str:
        """Resolve the model path in order of priority."""
        if provided_path:
            return provided_path

        model_file = Path(settings.deidentify_model) / 'final-model.pt'
        custom_model = Path(__file__).parent / 'models' / model_file

        # If frozen, use the bundled model
        if hasattr(sys, '_MEIPASS'):
            bundle_model = Path(sys._MEIPASS) / 'models' / model_file
            custom_model = bundle_model

        # Check in current working directory (for manual deployment)
        if not custom_model.exists():
            cwd_model = Path.cwd() / 'models' / model_file
            if cwd_model.exists():
                custom_model = cwd_model

        if custom_model.exists():
            logger.debug('Using custom model from: %s', custom_model)
            return str(custom_model)

        logger.warning('No custom model found, using default model cache')
        return settings.deidentify_model

    def create_instance(self) -> FlairTagger:
        """Create the FlairTagger instance, or return the cached one."""
        if self.tagger_instance is not None:
            return self.tagger_instance

        tokenizer = TokenizerFactory().tokenizer(corpus='ons', disable=('tagger', 'ner'))
        self.tagger_instance = FlairTagger(model=self.model_path, tokenizer=tokenizer, verbose=False)
        sys.stdout.write('\n')  # <-- White space above progress tracker

        return self.tagger_instance
