# ------------------------------------------------------------------------------------------------ #
# Copyright (c) 2026 Carmenda. All rights reserved.                                                #
# This program is distributed under the terms of the PolyForm Noncommercial License 1.0.0          #
# ------------------------------------------------------------------------------------------------ #

"""Deidentify complete pipeline names detection test.

For complete results, run with arguments.
`pytest -s -v`
"""

import polars as pl

from core.deidentify.handler import DeidentifyHandler
from core.utils.logger import setup_test_logging
from core.utils.progress_tracker import ProgressTracker
from core.utils.terminal import get_separator_line


def test_name_detection_pipeline() -> None:
    """Test the full extended pipeline on different sentences."""
    handler = DeidentifyHandler(tracker=ProgressTracker())
    logger = setup_test_logging()

    test_data = [
        {
            'clientname': 'Truus de Rooij',
            'client_initials': 'TR',
            'report': 'truus de rooij, henk de vries, en piet gingen fietsen naar het ziekenhuis',
        },
        {
            'clientname': 'Monique Naaldenberg',
            'client_initials': 'MN',
            'report': 'monique naaldenberg, anja van der haar en gers wonen mooi in amsterdam',
        },
        {
            'clientname': 'Joup Janssen',
            'client_initials': 'JJ',
            'report': 'joup, maarten van der poel, pim hadden een goede dag in de kliniek',
        },
    ]

    # Column mapping for the deduce handler
    input_cols = {
        'clientname': 'clientname',
        'report': 'report',
    }

    # Create DataFrame from test data
    df = pl.DataFrame(test_data)

    logger.info('(start test)')
    logger.info(get_separator_line())

    # Process the dataframe
    result_df = handler.deidentify_text(df, input_cols)

    # Iterate through results and log them
    for case_number, row in enumerate(result_df.iter_rows(named=True), 1):
        logger.info('\nTEST CASE %d:', case_number)
        logger.info('  Client:  Client name: %s (%s)', row['clientname'], row['client_initials'])
        logger.info("  Input:   '%s'", row['report'])
        logger.info("  Output:  '%s'\n", row['processed_report_1'])

    logger.info('\n%s', get_separator_line())


if __name__ == '__main__':
    test_name_detection_pipeline()
