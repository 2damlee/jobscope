import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db import engine
from app.models import Base

Base.metadata.create_all(bind=engine)

print("Tables created successfully.")