import sys
from pathlib import Path

# Add project root so auth_gateway and scripts modules resolve correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth_gateway.database import engine
from auth_gateway.models import Base

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
