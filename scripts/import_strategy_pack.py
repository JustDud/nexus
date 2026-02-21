"""Import local startup strategy pack into DB + vector index."""

from ingestion.manual_import import import_directory


def main() -> None:
    result = import_directory(
        directory="data/startup_strategy_pack",
        source_name="startup_strategy_pack",
        topic="startup_strategy",
        recursive=True,
        index_after_import=True,
    )
    print(result)


if __name__ == "__main__":
    main()
