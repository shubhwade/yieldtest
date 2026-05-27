"""
YieldLens Database Repository
Generic repository for MongoDB operations with support for string and ObjectId formats.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId
from database.mongo import get_db

logger = logging.getLogger("yieldlens.database.repository")

def to_object_id(id_val: Any) -> Union[ObjectId, Any]:
    """Convert value to ObjectId if it's a valid 24-char hex string."""
    if isinstance(id_val, str) and len(id_val) == 24:
        try:
            return ObjectId(id_val)
        except Exception:
            return id_val
    return id_val

class BaseRepository:
    """Base repository for common MongoDB operations."""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
    
    @property
    def collection(self):
        return get_db()[self.collection_name]
    
    def find_by_id(self, id_val: Any) -> Optional[Dict[str, Any]]:
        """Find a document by _id, trying both string and ObjectId formats."""
        oid = to_object_id(id_val)
        doc = self.collection.find_one({"_id": id_val})
        if not doc and oid != id_val:
            doc = self.collection.find_one({"_id": oid})
        return doc
    
    def find(self, query: Dict[str, Any] = None, limit: int = 0, skip: int = 0, sort: List = None) -> List[Dict[str, Any]]:
        """Find multiple documents with optional pagination and sorting."""
        query = query or {}
        cursor = self.collection.find(query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return list(cursor)
    
    def count(self, query: Dict[str, Any] = None) -> int:
        """Count documents matching the query."""
        query = query or {}
        return self.collection.count_documents(query)
    
    def insert_one(self, document: Dict[str, Any]) -> Any:
        """Insert a single document."""
        return self.collection.insert_one(document)
    
    def update_by_id(self, id_val: Any, update: Dict[str, Any]) -> bool:
        """Update a document by _id, trying both string and ObjectId formats."""
        oid = to_object_id(id_val)
        result = self.collection.update_one({"_id": id_val}, update)
        if result.matched_count == 0 and oid != id_val:
            result = self.collection.update_one({"_id": oid}, update)
        return result.matched_count > 0
    
    def delete_by_id(self, id_val: Any) -> bool:
        """Delete a document by _id, trying both string and ObjectId formats."""
        oid = to_object_id(id_val)
        result = self.collection.delete_one({"_id": id_val})
        if result.deleted_count == 0 and oid != id_val:
            result = self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0
