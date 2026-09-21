import csv
from pathlib import Path

from database import database
from models import models

BASE_DIR = Path(__file__).resolve().parent
GTFS_DIR = BASE_DIR / "nctx_1763993672"
STOP_FILE = GTFS_DIR / "stops.txt"


def clear_table(model_class):
    db = database.session_local()
    try:
        db.query(model_class).delete()
        db.commit()
    finally:
        db.close()


def load_stops_data(file_path: str | Path):
    db = database.session_local()
    try:
        clear_table(models.Stop)
        with open(file_path, "r", encoding="utf-8") as textfile:
            reader = csv.DictReader(textfile, delimiter=",")
            for row in reader:
                db.add(
                    models.Stop(
                        stop_id=row["stop_id"],
                        stop_name=row["stop_name"],
                        latitude=float(row["stop_lat"]),
                        longitude=float(row["stop_lon"]),
                    )
                )
        db.commit()
        print(f"Loaded stops data from {file_path} into the database")
    finally:
        db.close()


def load_gtfs_tables():
    db = database.session_local()
    try:
        gtfs_files = {
            "routes": (GTFS_DIR / "routes.txt", models.Route),
            "calendar": (GTFS_DIR / "calendar.txt", models.ServiceCalendar),
            "trips": (GTFS_DIR / "trips.txt", models.Trip),
            "stop_times": (GTFS_DIR / "stop_times.txt", models.StopTime),
            "shapes": (GTFS_DIR / "shapes.txt", models.Shape),
        }

        for file_name, (csv_path, model) in gtfs_files.items():
            clear_table(model)
            with open(csv_path, "r", encoding="utf-8") as textfile:
                reader = csv.DictReader(textfile, delimiter=",")
                for row in reader:
                    payload = {key: (value if value not in ("", " ") else None) for key, value in row.items()}

                    if file_name == "routes":
                        obj = model(
                            route_id=payload.get("route_id"),
                            agency_id=payload.get("agency_id"),
                            route_short_name=payload.get("route_short_name"),
                            route_long_name=payload.get("route_long_name"),
                            route_desc=payload.get("route_desc"),
                            route_type=int(payload["route_type"]) if payload.get("route_type") not in (None, "") else None,
                            route_url=payload.get("route_url"),
                            route_color=payload.get("route_color"),
                            route_text_color=payload.get("route_text_color"),
                        )
                    elif file_name == "calendar":
                        obj = model(
                            service_id=payload.get("service_id"),
                            monday=int(payload["monday"]) if payload.get("monday") not in (None, "") else 0,
                            tuesday=int(payload["tuesday"]) if payload.get("tuesday") not in (None, "") else 0,
                            wednesday=int(payload["wednesday"]) if payload.get("wednesday") not in (None, "") else 0,
                            thursday=int(payload["thursday"]) if payload.get("thursday") not in (None, "") else 0,
                            friday=int(payload["friday"]) if payload.get("friday") not in (None, "") else 0,
                            saturday=int(payload["saturday"]) if payload.get("saturday") not in (None, "") else 0,
                            sunday=int(payload["sunday"]) if payload.get("sunday") not in (None, "") else 0,
                            start_date=payload.get("start_date"),
                            end_date=payload.get("end_date"),
                        )
                    elif file_name == "trips":
                        obj = model(
                            trip_id=payload.get("trip_id"),
                            route_id=payload.get("route_id"),
                            service_id=payload.get("service_id"),
                            trip_headsign=payload.get("trip_headsign"),
                            trip_short_name=payload.get("trip_short_name"),
                            direction_id=int(payload["direction_id"]) if payload.get("direction_id") not in (None, "") else None,
                            block_id=payload.get("block_id"),
                            shape_id=payload.get("shape_id"),
                            wheelchair_accessible=int(payload["wheelchair_accessible"]) if payload.get("wheelchair_accessible") not in (None, "") else None,
                            bikes_allowed=int(payload["bikes_allowed"]) if payload.get("bikes_allowed") not in (None, "") else None,
                        )
                    elif file_name == "stop_times":
                        obj = model(
                            trip_id=payload.get("trip_id"),
                            arrival_time=payload.get("arrival_time"),
                            departure_time=payload.get("departure_time"),
                            stop_id=payload.get("stop_id"),
                            stop_sequence=int(payload["stop_sequence"]) if payload.get("stop_sequence") not in (None, "") else None,
                            stop_headsign=payload.get("stop_headsign"),
                            pickup_type=int(payload["pickup_type"]) if payload.get("pickup_type") not in (None, "") else None,
                            drop_off_type=int(payload["drop_off_type"]) if payload.get("drop_off_type") not in (None, "") else None,
                            timepoint=int(payload["timepoint"]) if payload.get("timepoint") not in (None, "") else None,
                        )
                    elif file_name == "shapes":
                        obj = model(
                            shape_id=payload.get("shape_id"),
                            shape_pt_lat=float(payload["shape_pt_lat"]) if payload.get("shape_pt_lat") not in (None, "") else None,
                            shape_pt_lon=float(payload["shape_pt_lon"]) if payload.get("shape_pt_lon") not in (None, "") else None,
                            shape_pt_sequence=int(payload["shape_pt_sequence"]) if payload.get("shape_pt_sequence") not in (None, "") else None,
                            shape_dist_traveled=float(payload["shape_dist_traveled"]) if payload.get("shape_dist_traveled") not in (None, "") else None,
                        )
                    else:
                        continue

                    db.add(obj)

                db.commit()
                print(f"Loaded GTFS table: {file_name}")
    finally:
        db.close()


def load_all_data():
    models.Base.metadata.create_all(bind=database.engine)
    load_stops_data(STOP_FILE)
    load_gtfs_tables()
    print("Database populated with stops and GTFS schedule tables.")


if __name__ == "__main__":
    load_all_data()

