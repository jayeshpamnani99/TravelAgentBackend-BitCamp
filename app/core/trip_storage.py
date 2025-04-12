import json
import uuid
import os
from typing import Dict, Optional
from datetime import datetime

class TripStorage:
    def __init__(self, storage_file: str = "trip_data.json"):
        self.storage_file = storage_file
        self.trip_data = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load trip data from the storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.trip_data = json.load(f)
            except json.JSONDecodeError:
                self.trip_data = {}
        else:
            self.trip_data = {}

    def _save_data(self) -> None:
        """Save trip data to the storage file"""
        with open(self.storage_file, 'w') as f:
            json.dump(self.trip_data, f, indent=2)

    def create_trip(self, data: Dict) -> str:
        """Create a new trip entry and return its UUID"""
        trip_id = str(uuid.uuid4())
        self.trip_data[trip_id] = {
            "data": data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self._save_data()
        return trip_id

    def update_trip(self, trip_id: str, data: Dict) -> bool:
        """Update an existing trip entry"""
        if trip_id not in self.trip_data:
            return False
        
        self.trip_data[trip_id]["data"].update(data)
        self.trip_data[trip_id]["updated_at"] = datetime.now().isoformat()
        self._save_data()
        return True

    def get_trip(self, trip_id: str) -> Optional[Dict]:
        """Get trip data by UUID"""
        return self.trip_data.get(trip_id)

    def delete_trip(self, trip_id: str) -> bool:
        """Delete a trip entry"""
        if trip_id not in self.trip_data:
            return False
        
        del self.trip_data[trip_id]
        self._save_data()
        return True

    def get_all_trips(self) -> Dict:
        """Get all trip data"""
        return self.trip_data

# Create a global instance
trip_storage = TripStorage() 