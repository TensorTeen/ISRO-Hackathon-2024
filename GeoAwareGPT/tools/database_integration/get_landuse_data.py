from ...schema import BaseTool
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from dotenv import load_dotenv

load_dotenv()


class GetLanduseData(BaseTool):
    def __init__(self):
        name = "get_landuse_data"
        description = "Get landuse percentage from a database given a city name and a type of landuse"
        args = {
            "city": "Modern name of the city(str) like chennai, mumbai, hyderabad",
            "landuse_type": "Type of landuse(str)[enum[commercial, residential, industrial]]",
            "percentage": "Return the percentage of landuse in the city(bool,optional,default=False)",
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

    def run(self, city, landuse_type, percentage=False):
        # Query the database for the landuse percentage
        with self.session() as session:
            if percentage:
                query = text(
                    f"SELECT CAST(SUM(ST_Area(landuse.geom)) AS FLOAT) * 100 / SUM(ST_Area(city_boundary.geom)) FROM landuse INNER JOIN city_boundary ON ST_Intersects(landuse.geom, city_boundary.geom) WHERE landuse.type = '{landuse_type}' AND lower(city_boundary.cityname)=lower('{city}');"
                )
                response = session.execute(query)
            else:  # need to change this to return area
                query = text(
                    f"SELECT landuse.type, CAST(SUM(ST_Area(landuse.geom)) AS FLOAT) * 100 / SUM(ST_Area(city_boundary.geom)) FROM landuse INNER JOIN city_boundary ON ST_Intersects(landuse.geom, city_boundary.geom) WHERE lower(city_boundary.cityname)=lower('{city}') GROUP BY landuse.type;"
                )
                response = session.execute(query)
        return str(response.fetchall()[:20])
