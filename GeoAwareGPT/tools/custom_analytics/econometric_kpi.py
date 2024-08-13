import os
from typing import Optional, Dict, Any, Sequence
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, session
from GeoAwareGPT.schema import BaseTool, BaseState
import re
import sys
import asyncio
import json
import pandas as pd

class EconometricKPI(BaseTool):
    def __init__(self):
        name = 'EconometricKPI'
        description = ""
        