# .env file load inside python path for pytest
import sys
import os
from dotenv import load_dotenv

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, src_path)

# Cargamos el env también para los test
load_dotenv(os.path.join(src_path, "src", ".env"))
