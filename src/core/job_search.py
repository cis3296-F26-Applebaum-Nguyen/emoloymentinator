"""
Searches job boards using JobSpy.
Returns matching job postings based on search parameters.
"""

from pydantic import basemodel
from typing import Optional, Literal
from google import genai
from jobspy import scrape_jobs
import pandas as pd