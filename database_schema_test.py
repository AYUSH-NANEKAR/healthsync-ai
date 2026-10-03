from app.database.connection import get_connection


connection = get_connection()

tables = [
    "devices",
    "vitals",
    "activity_data",
    "device_telemetry",
    "location_history",
]

try:
    for table in tables:
        print()
        print("=" * 60)
        print(f"TABLE: {table}")
        print("=" * 60)

        columns = connection.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()

        for column in columns:
            column_id, name, data_type, not_null, default_value, primary_key = column

            print(
                f"{name:20} "
                f"{data_type:12} "
                f"NOT NULL={not_null} "
                f"PK={primary_key} "
                f"DEFAULT={default_value}"
            )

        print()
        print("Foreign Keys:")

        foreign_keys = connection.execute(
            f"PRAGMA foreign_key_list({table})"
        ).fetchall()

        if not foreign_keys:
            print("  None")
        else:
            for foreign_key in foreign_keys:
                (
                    fk_id,
                    sequence,
                    referenced_table,
                    from_column,
                    to_column,
                    on_update,
                    on_delete,
                    match,
                ) = foreign_key

                print(
                    f"  {from_column} -> "
                    f"{referenced_table}.{to_column} "
                    f"(ON DELETE {on_delete})"
                )

finally:
    connection.close()