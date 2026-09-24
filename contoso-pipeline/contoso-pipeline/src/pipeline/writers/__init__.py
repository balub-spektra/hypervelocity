"""Output writers.

Every writer extends `WriterBase` (see base.py). `LocalFileWriter` is the
only implementation today. The pipeline's backlog item is to add a writer
that targets Azure Blob Storage, following the same pattern.
"""
