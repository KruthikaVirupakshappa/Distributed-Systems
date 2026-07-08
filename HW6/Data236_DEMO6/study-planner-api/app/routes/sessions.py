from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError
from ..db import get_sessions_collection
from ..schemas import StudySessionCreate, StudySessionUpdate, StudySessionOut
from ..utils import now_utc, serialize_session, is_valid_object_id, to_object_id

router = APIRouter(prefix="/api/sessions", tags=["Study Sessions"])

@router.post("", response_model=StudySessionOut, status_code=status.HTTP_201_CREATED)
def create_session(payload: StudySessionCreate):
    col = get_sessions_collection()
    doc = payload.model_dump()

    ts = now_utc()
    doc["createdAt"] = ts
    doc["updatedAt"] = ts

    try:
        res = col.insert_one(doc)
        created = col.find_one({"_id": res.inserted_id})
        return serialize_session(created)
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while creating session.")

@router.get("", response_model=list[StudySessionOut])
def get_all_sessions():
    col = get_sessions_collection()
    try:
        docs = list(col.find().sort("createdAt", -1))
        return [serialize_session(d) for d in docs]
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while fetching sessions.")

@router.get("/{session_id}", response_model=StudySessionOut)
def get_one_session(session_id: str):
    if not is_valid_object_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid id format.")

    col = get_sessions_collection()
    try:
        doc = col.find_one({"_id": to_object_id(session_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Session not found.")
        return serialize_session(doc)
    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while fetching session.")

@router.put("/{session_id}", response_model=StudySessionOut)
def update_session(session_id: str, payload: StudySessionUpdate):
    if not is_valid_object_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid id format.")

    col = get_sessions_collection()
    try:
        existing = col.find_one({"_id": to_object_id(session_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Session not found.")

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields provided to update.")

        updates["updatedAt"] = now_utc()

        col.update_one({"_id": to_object_id(session_id)}, {"$set": updates})
        updated = col.find_one({"_id": to_object_id(session_id)})
        return serialize_session(updated)
    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while updating session.")

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str):
    if not is_valid_object_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid id format.")

    col = get_sessions_collection()
    try:
        res = col.delete_one({"_id": to_object_id(session_id)})
        if res.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Session not found.")
        return
    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while deleting session.")