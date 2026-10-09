"""Small synthetic GTFS fixtures; no network or raw-data access."""

from io import BytesIO
from zipfile import ZipFile

import pytest


@pytest.fixture
def gtfs_zip():
    def make(overrides=None, omit=()):
        files = {
            "agency.txt": "agency_id,agency_name\nA,Fixture Transit\n",
            "stops.txt": ("stop_id,stop_lat,stop_lon\nA,45.1,3.2\nB,46.2,4.3\n"),
            "routes.txt": "route_id\nR\n",
            "trips.txt": "route_id,service_id,trip_id\nR,S,T1\nR,S,T2\n",
            "stop_times.txt": "trip_id,stop_id,stop_sequence\nT1,A,1\n",
            "calendar.txt": (
                "service_id,monday,tuesday,wednesday,thursday,friday,"
                "saturday,sunday,start_date,end_date\n"
                "S,1,1,1,1,1,0,0,20261005,20261011\n"
            ),
            "calendar_dates.txt": (
                "service_id,date,exception_type\nS,20261005,2\nS,20261012,1\n"
            ),
        }
        files.update(overrides or {})
        buffer = BytesIO()
        with ZipFile(buffer, "w") as archive:
            for name, text in files.items():
                if name not in omit:
                    archive.writestr(name, text)
        return buffer.getvalue()

    return make
