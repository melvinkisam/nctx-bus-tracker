from models import models 
from database import database
import csv

file_path = "nctx_1763993672/stops.txt"

def load_stops_data(file_path: str):
    db = database.session_local()
    with open(file_path, "r") as textfile:
        reader = csv.DictReader(textfile, delimiter=",")
        #print("Detected columns:", reader.fieldnames)

        for row in reader:
            stop = models.Stop(
                stop_id=row["stop_id"],
                stop_name=row["stop_name"],
                latitude=float(row["stop_lat"]),
                longitude=float(row["stop_lon"]),
            )
            db.add(stop)

    db.commit()
    db.close()
    print("Loaded stops data into the database")

if __name__ == "__main__":
    models.Base.metadata.create_all(bind=database.engine)
    load_stops_data(file_path)

