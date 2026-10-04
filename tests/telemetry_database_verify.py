from app.database.connection import get_connection


connection = get_connection()

try:
    print("=" * 60)
    print("LATEST VITALS")
    print("=" * 60)

    row = connection.execute(
        """
        SELECT
            user_id,
            device_id,
            heart_rate,
            spo2,
            temperature,
            systolic_bp,
            diastolic_bp,
            recorded_at,
            source
        FROM vitals
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    print(row)

    print()
    print("=" * 60)
    print("LATEST ACTIVITY")
    print("=" * 60)

    row = connection.execute(
        """
        SELECT
            user_id,
            device_id,
            movement,
            steps,
            distance,
            calories,
            active_time,
            recorded_at,
            source
        FROM activity_data
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    print(row)

    print()
    print("=" * 60)
    print("LATEST DEVICE TELEMETRY")
    print("=" * 60)

    row = connection.execute(
        """
        SELECT
            device_id,
            battery,
            recorded_at
        FROM device_telemetry
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    print(row)

    print()
    print("=" * 60)
    print("LATEST LOCATION")
    print("=" * 60)

    row = connection.execute(
        """
        SELECT
            user_id,
            device_id,
            readable_name,
            latitude,
            longitude,
            recorded_at,
            source
        FROM location_history
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    print(row)

finally:
    connection.close()