"""
Service layer for the news app.

These modules contain the *business logic* that is too heavy to live inside a
model or a view:

  * ``dedup``       – normalises Persian titles and hashes them so duplicate
                      articles can be detected even when their wording differs
                      slightly (zero-width chars, extra spaces, …).
  * ``categorizer`` – picks the best Category for a piece of text using a
                      hybrid strategy (keyword matching first, then a fallback
                      to the feed's default category).
  * ``rss_fetcher`` – downloads + parses an RSSFeed and creates Article rows
                      for every new item (using dedup + categorizer).

Keeping these concerns out of models/views makes them easy to unit-test and
to reuse from management commands, the scheduler, or future API views.
"""
