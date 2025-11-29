"""
Initialize database tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db, engine
from app.core.database import AgentAction, Forecast, Inventory, PatientAdvisory

def main():
    print("Initializing database...")
    init_db()
    print("✅ Database initialized successfully!")
    print("\nTables created:")
    print("  - agent_actions")
    print("  - forecasts")
    print("  - inventory")
    print("  - patient_advisories")

if __name__ == "__main__":
    main()

