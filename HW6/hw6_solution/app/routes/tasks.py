from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from ..db import get_tasks_collection
from ..schemas import TaskCreate, TaskOut, TaskUpdate
from ..utils import is_valid_object_id, now_utc, serialize_task, to_object_id

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    col = get_tasks_collection()
    doc = payload.model_dump()

    ts = now_utc()
    doc["createdAt"] = ts
    doc["updatedAt"] = ts

    try:
        result = col.insert_one(doc)
        created = col.find_one({"_id": result.inserted_id})
        return serialize_task(created)
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while creating task.")


@router.get("", response_model=list[TaskOut])
def get_all_tasks():
    col = get_tasks_collection()
    try:
        docs = list(col.find().sort("createdAt", -1))
        return [serialize_task(doc) for doc in docs]
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while fetching tasks.")


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str):
    if not is_valid_object_id(task_id):
        raise HTTPException(status_code=400, detail="Invalid id format.")

    col = get_tasks_collection()
    try:
        doc = col.find_one({"_id": to_object_id(task_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Task not found.")
        return serialize_task(doc)
    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while fetching task.")


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: str, payload: TaskUpdate):
    if not is_valid_object_id(task_id):
        raise HTTPException(status_code=400, detail="Invalid id format.")

    col = get_tasks_collection()
    try:
        existing = col.find_one({"_id": to_object_id(task_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found.")

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields provided to update.")

        updates["updatedAt"] = now_utc()

        col.update_one({"_id": to_object_id(task_id)}, {"$set": updates})
        updated = col.find_one({"_id": to_object_id(task_id)})
        return serialize_task(updated)
    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while updating task.")


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str):
    if not is_valid_object_id(task_id):
        raise HTTPException(status_code=400, detail="Invalid id format.")

    col = get_tasks_collection()
    try:
        result = col.delete_one({"_id": to_object_id(task_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Task not found.")
        return
    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while deleting task.")
