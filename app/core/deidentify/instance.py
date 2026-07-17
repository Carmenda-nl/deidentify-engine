# ------------------------------------------------------------------------------------------------ #
# Copyright (c) 2026 Carmenda. All rights reserved.                                                #
# This program is distributed under the terms of the GNU General Public License: GPL-3.0-or-later  #
# ------------------------------------------------------------------------------------------------ #

"""Manager for the Deidentify FlairTagger instance. holds a single instance of Deidentify."""

from __future__ import annotations

import sys
import warnings

from core.utils.logger import setup_logging
from main.config import settings

with warnings.catch_warnings():
    warnings.simplefilter('ignore', category=FutureWarning)
    warnings.simplefilter('ignore', category=UserWarning)

    from deidentify.taggers import FlairTagger
    from deidentify.tokenizer import TokenizerFactory

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
