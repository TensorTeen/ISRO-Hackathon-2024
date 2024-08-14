from ...schema import BaseTool
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from dotenv import load_dotenv

load_dotenv()


class GetRailwayLength(BaseTool):
    def __init__(self):
        name = "get_railway_length"
        description = "Get the length of railway in a city"
        args = {
            "city": "Name of the city(str)",
        }
        version = "0.1.0"
        super().__init__(name, description, version, args)
        self.tool_type = "AUA"
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")
        DB_NAME = os.getenv("DB_NAME")
        db_string = (
            f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
        engine = create_engine(db_string, pool_pre_ping=True)
        self.session = sessionmaker(bind=engine)

    def run(self, city):
        with self.session() as session:
            # Query the database for the landuse percentage
            query = text(
                f"SELECT cb.cityname,SUM(ST_Length(ST_Intersection(rw.geom, cb.geom)::geography)) AS total_railway_length FROM  city_boundary cb JOIN railways rw ON  ST_Intersects(cb.geom, rw.geom) WHERE  cb.cityname = '{city}' GROUP BY  cb.cityname;"
            )
            response = session.execute(query)
            return str(response.fetchall()[:20])
