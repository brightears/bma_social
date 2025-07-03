from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import List, Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
import csv
import io
import logging

from app.models import Customer, User
from app.api.v1.dependencies import get_db, get_current_user
from app.core.security import get_password_hash

router = APIRouter()
logger = logging.getLogger(__name__)


class ContactCreate(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    whatsapp_id: Optional[str] = None
    line_id: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None
    
    @validator('email', 'whatsapp_id', 'line_id', 'notes', pre=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    whatsapp_id: Optional[str] = None
    line_id: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    
    @validator('email', 'whatsapp_id', 'line_id', 'notes', 'name', 'phone', pre=True)
    def empty_str_to_none(cls, v):
        if v == '':
            return None
        return v


class ContactResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str]
    whatsapp_id: Optional[str]
    line_id: Optional[str]
    tags: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContactGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#1976d2"  # Default blue


class ContactGroupResponse(BaseModel):
    name: str
    description: Optional[str]
    color: str
    contact_count: int


@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all contacts with optional filtering"""
    
    query = select(Customer)
    
    # Add search filter
    if search:
        search_filter = or_(
            Customer.name.ilike(f"%{search}%"),
            Customer.phone.ilike(f"%{search}%"),
            Customer.email.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    # Add tag filter
    if tag:
        # Use PostgreSQL JSON operators
        query = query.where(Customer.extra_data["tags"].astext.contains(tag))
    
    query = query.order_by(Customer.name).offset(skip).limit(limit)
    result = await db.execute(query)
    contacts = result.scalars().all()
    
    # Convert to response format
    response = []
    for contact in contacts:
        contact_data = {
            "id": str(contact.id),
            "name": contact.name,
            "phone": contact.phone,
            "email": contact.email,
            "whatsapp_id": contact.whatsapp_id,
            "line_id": contact.line_id,
            "tags": contact.extra_data.get("tags", []) if contact.extra_data else [],
            "notes": contact.extra_data.get("notes") if contact.extra_data else None,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at
        }
        response.append(ContactResponse(**contact_data))
    
    return response


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new contact"""
    
    try:
        # Check if contact already exists
        existing = await db.execute(
            select(Customer).where(
                or_(
                    Customer.phone == contact.phone,
                    and_(Customer.email == contact.email, contact.email is not None)
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with this phone or email already exists"
            )
        
        # Validate and clean email
        email_value = None
        if contact.email:
            email_value = contact.email.strip() if contact.email.strip() else None
        
        # Create new customer
        db_contact = Customer(
            name=contact.name,
            phone=contact.phone,
            email=email_value,
            whatsapp_id=contact.whatsapp_id or contact.phone,  # Default to phone
            line_id=contact.line_id,
            extra_data={
                "tags": contact.tags,
                "notes": contact.notes,
                "created_by": str(current_user.id)
            }
        )
        
        db.add(db_contact)
        await db.commit()
        await db.refresh(db_contact)
        
        return ContactResponse(
            id=str(db_contact.id),
            name=db_contact.name,
            phone=db_contact.phone,
            email=db_contact.email,
            whatsapp_id=db_contact.whatsapp_id,
            line_id=db_contact.line_id,
            tags=db_contact.extra_data.get("tags", []),
            notes=db_contact.extra_data.get("notes"),
            created_at=db_contact.created_at,
            updated_at=db_contact.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contact: {str(e)}"
        )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific contact"""
    
    result = await db.execute(
        select(Customer).where(Customer.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return ContactResponse(
        id=str(contact.id),
        name=contact.name,
        phone=contact.phone,
        email=contact.email,
        whatsapp_id=contact.whatsapp_id,
        line_id=contact.line_id,
        tags=contact.extra_data.get("tags", []) if contact.extra_data else [],
        notes=contact.extra_data.get("notes") if contact.extra_data else None,
        created_at=contact.created_at,
        updated_at=contact.updated_at
    )


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    contact_update: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a contact"""
    
    result = await db.execute(
        select(Customer).where(Customer.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Update fields if provided
    if contact_update.name is not None:
        contact.name = contact_update.name
    if contact_update.phone is not None:
        contact.phone = contact_update.phone
    if contact_update.email is not None:
        contact.email = contact_update.email
    if contact_update.whatsapp_id is not None:
        contact.whatsapp_id = contact_update.whatsapp_id
    if contact_update.line_id is not None:
        contact.line_id = contact_update.line_id
    
    # Update extra data
    if not contact.extra_data:
        contact.extra_data = {}
    
    if contact_update.tags is not None:
        contact.extra_data["tags"] = contact_update.tags
    if contact_update.notes is not None:
        contact.extra_data["notes"] = contact_update.notes
    
    contact.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(contact)
    
    return ContactResponse(
        id=str(contact.id),
        name=contact.name,
        phone=contact.phone,
        email=contact.email,
        whatsapp_id=contact.whatsapp_id,
        line_id=contact.line_id,
        tags=contact.extra_data.get("tags", []),
        notes=contact.extra_data.get("notes"),
        created_at=contact.created_at,
        updated_at=contact.updated_at
    )


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a contact"""
    
    result = await db.execute(
        select(Customer).where(Customer.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    await db.delete(contact)
    await db.commit()
    
    return {"status": "deleted"}


@router.get("/groups/", response_model=List[ContactGroupResponse])
async def get_contact_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all unique tags used as groups"""
    
    # Get all customers and extract unique tags
    result = await db.execute(select(Customer))
    customers = result.scalars().all()
    
    tag_counts = {}
    for customer in customers:
        if customer.extra_data and "tags" in customer.extra_data:
            for tag in customer.extra_data["tags"]:
                if tag not in tag_counts:
                    tag_counts[tag] = 0
                tag_counts[tag] += 1
    
    # Convert to response format
    groups = []
    for tag, count in tag_counts.items():
        groups.append(ContactGroupResponse(
            name=tag,
            description=None,
            color="#1976d2",
            contact_count=count
        ))
    
    return sorted(groups, key=lambda x: x.name)


@router.post("/import/csv")
async def import_contacts_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import contacts from CSV file"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a CSV file."
        )
    
    # Read CSV file
    contents = await file.read()
    csv_file = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.DictReader(csv_file)
    
    imported = 0
    skipped = 0
    errors = []
    
    for row in csv_reader:
        try:
            # Required fields
            if not row.get('name') or not row.get('phone'):
                errors.append(f"Row missing required fields: {row}")
                skipped += 1
                continue
            
            # Check if already exists
            existing = await db.execute(
                select(Customer).where(Customer.phone == row['phone'])
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue
            
            # Parse tags
            tags = []
            if row.get('tags'):
                tags = [tag.strip() for tag in row['tags'].split(',')]
            
            # Create contact
            contact = Customer(
                name=row['name'],
                phone=row['phone'],
                email=row.get('email'),
                whatsapp_id=row.get('whatsapp_id') or row['phone'],
                line_id=row.get('line_id'),
                extra_data={
                    "tags": tags,
                    "notes": row.get('notes'),
                    "created_by": str(current_user.id)
                }
            )
            
            db.add(contact)
            imported += 1
            
        except Exception as e:
            errors.append(f"Error processing row {row}: {str(e)}")
            skipped += 1
    
    await db.commit()
    
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10]  # Limit error messages
    }


@router.get("/export/csv")
async def export_contacts_csv(
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export contacts to CSV file"""
    
    query = select(Customer)
    
    # Filter by tag if provided
    if tag:
        query = query.where(Customer.extra_data["tags"].astext.contains(tag))
    
    result = await db.execute(query.order_by(Customer.name))
    contacts = result.scalars().all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['name', 'phone', 'email', 'whatsapp_id', 'line_id', 'tags', 'notes'])
    
    # Write contacts
    for contact in contacts:
        tags = ','.join(contact.extra_data.get("tags", [])) if contact.extra_data else ""
        notes = contact.extra_data.get("notes", "") if contact.extra_data else ""
        
        writer.writerow([
            contact.name,
            contact.phone,
            contact.email or "",
            contact.whatsapp_id or "",
            contact.line_id or "",
            tags,
            notes
        ])
    
    output.seek(0)
    
    return {
        "content": output.getvalue(),
        "filename": f"contacts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    }