"""Run ingestion batch from CLI (Stage 10 scheduling helper)."""

from ingestion.control import start_ingestion_batch


def main() -> None:
    result = start_ingestion_batch(
        source_names=None,
        only_active=True,
        index_after_crawl=True,
        stop_on_error=False,
    )
    print(result)


if __name__ == "__main__":
    main()
