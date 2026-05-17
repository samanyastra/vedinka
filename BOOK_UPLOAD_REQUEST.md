# Book Upload Request Moderation Model

## Overview

The `BookUploadRequest` model handles the book upload approval workflow for admin moderation.

**Location**: `apps/content/models.py`

---

## Model Structure

### BookUploadRequest

Tracks admin approval requests for book uploads.

**Fields:**

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `book` | OneToOneField(Book) | Yes | Reference to the uploaded book |
| `author` | ForeignKey(UserProfile) | Yes | Author who uploaded the book |
| `status` | CharField | Yes | Current approval status |
| `submitted_at` | DateTimeField | Auto | When book was submitted |
| `reviewed_by` | ForeignKey(User) | No | Admin who reviewed it |
| `reviewed_at` | DateTimeField | No | When review was completed |
| `rejection_reason` | TextField | No | Why it was rejected |
| `admin_comments` | TextField | No | Additional admin notes |
| `created_at` | DateTimeField | Auto | Record creation (from BaseModel) |
| `updated_at` | DateTimeField | Auto | Last update (from BaseModel) |

**Status Choices:**
- `pending` - Awaiting admin review
- `approved` - Book approved and published
- `rejected` - Book rejected

---

## Workflow

```
Author Uploads Book
        ↓
Book model created (is_checks_passed=False)
        ↓
BookUploadRequest created (status='pending')
        ↓
Admin Views Request
        ↓
Admin approves/rejects
        ↓
BookUploadRequest updated (status=approved/rejected)
        ↓
If approved:
  Book.is_checks_passed = True
  Book published & visible
        ↓
If rejected:
  rejection_reason set
  Book remains unpublished
  Author notified of reason
```

---

## Database Indexes

Optimized queries:

```
(status, -submitted_at)       # Get pending reviews
(author, status)              # Author's request history
(reviewed_by, -reviewed_at)   # Admin's review history
```

---

## Usage Examples

### Get all pending reviews
```python
from apps.content.models import BookUploadRequest

pending_requests = BookUploadRequest.objects.filter(
    status='pending'
).order_by('-submitted_at')
```

### Get author's requests
```python
author_requests = BookUploadRequest.objects.filter(
    author_id=123
).order_by('-submitted_at')
```

### Get admin's reviews
```python
admin_reviews = BookUploadRequest.objects.filter(
    reviewed_by_id=456,
    status__in=['approved', 'rejected']
).order_by('-reviewed_at')
```

### Approve a request
```python
request = BookUploadRequest.objects.get(id=1)
request.status = 'approved'
request.reviewed_by = admin_user
request.reviewed_at = datetime.now()
request.admin_comments = "Book quality looks good"
request.save()

# Update book
request.book.is_checks_passed = True
request.book.save()
```

### Reject a request
```python
request = BookUploadRequest.objects.get(id=1)
request.status = 'rejected'
request.reviewed_by = admin_user
request.reviewed_at = datetime.now()
request.rejection_reason = "Plagiarism detected"
request.admin_comments = "Please verify original content"
request.save()
```

---

## API Endpoints (To Be Implemented)

### Admin Views

```
GET /api/admin/book-requests/
  - List all pending/approved/rejected requests
  - Filter by status
  - Pagination

GET /api/admin/book-requests/{id}/
  - View single request details

PATCH /api/admin/book-requests/{id}/approve/
  - Approve a request
  - Set reviewed_by, reviewed_at
  - Update book.is_checks_passed

PATCH /api/admin/book-requests/{id}/reject/
  - Reject a request
  - Set rejection_reason, admin_comments

GET /api/admin/authors/{id}/book-requests/
  - View author's submissions
```

### Author Views

```
GET /api/my-books/
  - List author's uploaded books
  - Show request status

GET /api/my-books/{id}/request-status/
  - View approval status of a book
  - Show rejection reason if rejected

POST /api/books/upload/
  - Upload new book
  - Auto-create BookUploadRequest
```

---

## Related Flow

### Book Upload Flow
```
1. Author calls POST /api/books/upload/
2. Book model created (is_checks_passed=False)
3. BookUploadRequest created (status='pending')
4. Admin receives notification
5. Admin reviews at /admin/book-requests/
6. Admin approves/rejects with comments
7. Author receives email with status
```

---

## Admin Dashboard Queries

### Pending Review Count
```python
pending_count = BookUploadRequest.objects.filter(
    status='pending'
).count()
```

### Approval Rate
```python
from django.db.models import Count, Q

stats = BookUploadRequest.objects.aggregate(
    total=Count('id'),
    approved=Count('id', filter=Q(status='approved')),
    rejected=Count('id', filter=Q(status='rejected')),
    pending=Count('id', filter=Q(status='pending')),
)

approval_rate = (stats['approved'] / stats['total']) * 100
```

### Average Review Time
```python
from django.db.models import F
from django.db.models.functions import Extract

avg_time = BookUploadRequest.objects.filter(
    reviewed_at__isnull=False
).annotate(
    review_time=F('reviewed_at') - F('submitted_at')
).aggregate(
    Avg('review_time')
)
```

---

## Admin Notifications

**To implement:**

1. **New Upload Alert** - Notify admins when new request arrives
   - Trigger: BookUploadRequest.status = 'pending'
   - Notification: Email to admin@vedinka.com

2. **Approval Email** - Notify author when approved
   - Trigger: BookUploadRequest.status = 'approved'
   - Email: Author email with publication link

3. **Rejection Email** - Notify author when rejected
   - Trigger: BookUploadRequest.status = 'rejected'
   - Email: Author with rejection_reason and admin_comments

---

## Admin Panel Integration

### Django Admin

Register in `apps/content/admin.py`:

```python
from django.contrib import admin
from .models import BookUploadRequest

@admin.register(BookUploadRequest)
class BookUploadRequestAdmin(admin.ModelAdmin):
    list_display = ('book', 'author', 'status', 'submitted_at', 'reviewed_by')
    list_filter = ('status', 'submitted_at', 'reviewed_by')
    search_fields = ('book__title', 'author__user__username')
    readonly_fields = ('submitted_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Book Info', {
            'fields': ('book', 'author'),
        }),
        ('Review Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at'),
        }),
        ('Review Details', {
            'fields': ('rejection_reason', 'admin_comments'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        count = queryset.update(status='approved', reviewed_by=request.user)
        self.message_user(request, f"{count} requests approved")
    
    def reject_requests(self, request, queryset):
        count = queryset.update(status='rejected', reviewed_by=request.user)
        self.message_user(request, f"{count} requests rejected")
```

---

## Constraints & Validation

1. **OneToOne Relationship** - Each book can have only one upload request
2. **Status Flow** - Only pending → approved/rejected (no reverse)
3. **Reviewer** - Must be admin/staff user
4. **Rejection Reason** - Required if status='rejected'
5. **Timestamps** - Auto-managed by Django

---

## Migration Command

```bash
# Create migration
python manage.py makemigrations content

# Apply migration
python manage.py migrate

# Verify
python manage.py dbshell
SELECT * FROM content_bookluploadrequest;
```

---

## Summary Table

| Feature | Value |
|---------|-------|
| **Model Name** | BookUploadRequest |
| **App** | content |
| **Primary Key** | id (UUID from BaseModel) |
| **Related Book** | One-to-One |
| **Status Options** | pending, approved, rejected |
| **Indexed Fields** | status, author, reviewed_by |
| **Audit Trail** | submitted_at, reviewed_at |
