# ------------------------------------------------------------------------------------------------ #
# Copyright (c) 2026 Carmenda. All rights reserved.                                                #
# This program is distributed under the terms of the GNU General Public License: GPL-3.0-or-later  #
# ------------------------------------------------------------------------------------------------ #

"""Test script to run deidentify."""

import warnings

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

from pprint import pprint  # noqa: E402

from deidentify.base import Document  # noqa: E402
from deidentify.taggers import FlairTagger  # noqa: E402
from deidentify.tokenizer import TokenizerFactory  # noqa: E402
from deidentify.util import mask_annotations  # noqa: E402

# Create some text
text = (
    'Dit is stukje tekst met daarin de naam Jan Jansen. De patient J. Jansen (e: '
    'j.jnsen@email.com, t: 06-12345678) is 64 jaar oud en woonachtig in Utrecht. Hij werd op 10 '
    'oktober door arts Peter de Visser ontslagen van de kliniek van het UMCU.'
)

# Wrap text in document
documents = [Document(name='doc_01', text=text)]

# Select downloaded model
model = 'model_bilstmcrf_ons_fast-v0.2.0'

# Instantiate tokenizer
tokenizer = TokenizerFactory().tokenizer(corpus='ons', disable=('tagger', 'ner'))

# Load tagger with a downloaded model file and tokenizer
tagger = FlairTagger(model=model, tokenizer=tokenizer, verbose=False)

print('')
print('*' * 80)
print(tagger.tags)
print('*' * 80)
print('')

# Annotate your documents
annotated_docs = tagger.annotate(documents)


def main() -> None:
    """Run deidentify test."""
    print(documents)

    first_doc = annotated_docs[0]
    pprint(first_doc.annotations)

    # Mask annotations in the first document
    masked_doc = mask_annotations(first_doc)
    print('\nMasked text:\n', masked_doc.text)


if __name__ == '__main__':
    main()
