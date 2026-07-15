# ------------------------------------------------------------------------------------------------ #
# Copyright (c) 2026 Carmenda. All rights reserved.                                                #
# This program is distributed under the terms of the PolyForm Noncommercial License 1.0.0          #
# ------------------------------------------------------------------------------------------------ #

"""Handler module for de-identification of medical text."""

from __future__ import annotations

import logging
import re
from functools import reduce
from typing import TYPE_CHECKING

import polars as pl

from core.deidentify.instance import DeidentifyInstanceManager
from core.utils.logger import setup_logging
from core.utils.terminal import colorize_tags, log_block

if TYPE_CHECKING:
    from deidentify.base import Document
    from deidentify.taggers import FlairTagger

    from core.utils.progress_tracker import ProgressTracker

logger = setup_logging()

instance_manager = DeidentifyInstanceManager()

# Matches FlairTagger's default mini_batch_size, so each chunk maps to one Flair inference batch
# and progress can be reported after every chunk instead of only once per (much larger) df slice.
PROGRESS_CHUNK_SIZE = 256


class DeidentifyHandler:
    """Handler class for de-identification operations."""

    def __init__(self, tracker: ProgressTracker) -> None:
        """Initialize the handler. The deidentify tagger is loaded lazily on first use."""
        self.tracker = tracker

        # Lazily loaded/cached FlairTagger, see `_get_tagger`.
        self._tagger: FlairTagger | None = None

        # For debug logging of de-identification results
        self.processed_reports: list[dict[str, str]] = []
        self.total_processed = 0

        # Progress tracking (progress bar)
        self.processed_count = 0
        self.total_count = 0
        self.last_update = 0

    def replace_synonym(self, df: pl.DataFrame, datakey: pl.DataFrame, report_cols: list[str]) -> pl.DataFrame:
        """Replace all synonyms in the report text with their main names."""
        synonym_df = (
            datakey.with_columns(pl.col('synonyms').str.split(','))
            .explode('synonyms')
            .with_columns(pl.col('synonyms').str.strip_chars())
            .filter(pl.col('synonyms') != '')
            .select([pl.col('clientname'), pl.col('synonyms')])
        )

        synonym_pairs = list(zip(synonym_df['synonyms'], synonym_df['clientname']))

        replaced_synonyms = [
            reduce(
                lambda expr, pair: expr.str.replace_all(r'\b' + re.escape(pair[0]) + r'\b', pair[1], literal=False),
                synonym_pairs,
                pl.col(column),
            ).alias(column)
            for column in report_cols
        ]
        return df.with_columns(replaced_synonyms)

    def _get_tagger(self) -> FlairTagger:
        """Lazily fetch the shared FlairTagger, loaded once per worker process."""
        if self._tagger is None:
            self.tracker.set_progress('init_model')
            self._tagger = instance_manager.create_instance()

        return self._tagger

    def _is_patient_name(self, annotation_text: str, clientname: str | None) -> bool:
        """Check whether a `Name` annotation refers to the client rather than someone else mentioned in the report."""
        if not clientname:
            return False

        name_parts = {part.lower() for part in clientname.split()}
        return annotation_text.strip().lower() in name_parts or annotation_text.strip().lower() == clientname.lower()

    def _annotate_batch(self, report_texts: list[str]) -> list[Document]:
        """Annotate multiple reports in a single tagger call, so Flair can batch internally."""
        from deidentify.base import Document

        tagger = self._get_tagger()
        documents = [Document(name=str(index), text=text) for index, text in enumerate(report_texts)]
        return tagger.annotate(documents)

    def _mask_document(self, annotated_doc: Document, clientname: str | None) -> str:
        """Mask PHI in a single annotated document, using [PATIENT] for the client's own name."""
        from deidentify.util import mask_annotations

        def _replacement_formatter(annotation: object) -> str:
            if annotation.tag == 'Name' and self._is_patient_name(annotation.text, clientname):
                return '[PATIENT]'
            return f'[{annotation.tag.upper()}]'

        return mask_annotations(annotated_doc, replacement_formatter=_replacement_formatter).text

    def _deidentify_batch(self, batch: pl.Series) -> pl.Series:
        """Annotate and mask a batch of report texts in chunks, while tracking progress per chunk."""
        rows = batch.to_list()
        results = ['' for _ in rows]

        for chunk_start in range(0, len(rows), PROGRESS_CHUNK_SIZE):
            self.tracker.check_cancelled()

            chunk = list(enumerate(rows[chunk_start : chunk_start + PROGRESS_CHUNK_SIZE], start=chunk_start))
            report_texts = {index: (row.get('report') or '') for index, row in chunk}
            clientnames = {index: (row.get('clientname') or None) for index, row in chunk}

            # Skip empty/null rows that may appear in batches; only non-empty reports go to the tagger.
            non_empty_indices = [index for index, text in report_texts.items() if text]
            annotated_docs = self._annotate_batch([report_texts[index] for index in non_empty_indices])

            for row_index, annotated_doc in zip(non_empty_indices, annotated_docs):
                results[row_index] = self._mask_document(annotated_doc, clientnames[row_index])

                if logger.level == logging.DEBUG:
                    self.total_processed += 1
                    self.processed_reports.append(
                        {
                            'report': report_texts[row_index],
                            'deidentify': results[row_index],
                        }
                    )

            self.processed_count += len(chunk)
            step_progress = (self.processed_count / self.total_count) * 100
            self.tracker.set_row_progress(
                'pseudonymize',
                self.processed_count,
                self.total_count,
                int(step_progress),
                overall=(20, 85),
            )
            self.last_update = self.processed_count

        return pl.Series(results)

    def deidentify_text(self, df: pl.DataFrame, input_cols: dict) -> pl.DataFrame:
        """De-identify report text with or without clientname."""
        reports_cols = [value.strip() for key, value in input_cols.items() if key.startswith('report')]

        has_clientname = 'clientname' in input_cols and input_cols['clientname'] in df.columns
        total_rows = df.height

        clientname_message = 'with clientname' if has_clientname else ''
        logger.info('Processing %d rows %s\n', total_rows, clientname_message)

        # Initialize a clean progress bar
        self.last_update = 0
        self.processed_count = 0
        self.total_count = total_rows * len(reports_cols)

        slice_size = 50_000
        df_result = df

        for col_number, report_col in enumerate(reports_cols, start=1):
            struct_fields = [pl.col(report_col).str.strip_chars().alias('report')]
            if has_clientname:
                struct_fields.append(pl.col(input_cols['clientname']).alias('clientname'))

            result_parts = [
                df.slice(offset, slice_size)
                .select(pl.struct(struct_fields).map_batches(self._deidentify_batch, return_dtype=pl.Utf8))
                .to_series()
                for offset in range(0, total_rows, slice_size)
            ]
            df_result = df_result.with_columns(pl.concat(result_parts).alias(f'processed_report_{col_number}'))

        self.tracker.clean_progress_bar()

        return df_result

    def add_clientcodes(self, df: pl.DataFrame, datakey: pl.DataFrame, input_cols: dict[str, str]) -> pl.DataFrame:
        """Add patient codes to DataFrame and replace [PATIENT] tags in processed reports."""
        clientname_col = input_cols['clientname']

        df = (
            df.join(
                datakey.select(['clientname', 'code']),
                left_on=clientname_col,
                right_on='clientname',
                how='left',
                coalesce=True,
            )
            .rename({'code': 'clientcode'})
            .select('clientcode', pl.all().exclude('clientcode'))
        )

        processed_cols = [col for col in df.columns if col.startswith('processed_report_')]
        return df.with_columns(
            [
                pl.col(col).str.replace_all(r'\[PATIENT\]', pl.format('[{}]', pl.col('clientcode')))
                for col in processed_cols
            ],
        )

    def deidentify_text_debug(self) -> None:
        """Only show de-identification results if logger is in debug mode."""
        max_reports = 10

        for rule in self.processed_reports[:max_reports]:
            title = 'De-identification Report'
            sections = {
                'ORIGINAL': colorize_tags(rule['report']),
                'DEIDENTIFY': colorize_tags(rule['deidentify']),
            }
            log_block(title, sections)
