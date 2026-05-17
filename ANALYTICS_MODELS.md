# Analytics & Metrics Models

New database tables added for tracking sales, popularity, and recommendations.

---

## Models Overview

### 1. **BookSalesMetrics** (Finance App)
**Location**: `apps/finance/models.py`

Tracks monthly sales performance per book.

**Fields:**
| Field | Type | Purpose |
|-------|------|---------|
| `book` | ForeignKey(Book) | Reference to the book |
| `month` | DateField | First day of month (YYYY-MM-01) |
| `sales_count` | Integer | Number of units sold |
| `revenue` | Decimal | Total revenue from sales |
| `average_rating` | Decimal | Average rating for the month |
| `views_count` | Integer | Page views for the month |

**Key Features:**
- Unique per book+month combination
- Indexed on (book, -month) and (-month) for fast queries
- Tracks sales, revenue, ratings, and views

**Use Cases:**
- "How many copies of Book X sold in March 2025?"
- "What's the revenue trend for Book Y over time?"
- "Which books are trending this month by views?"

---

### 2. **AuthorSalesMetrics** (Finance App)
**Location**: `apps/finance/models.py`

Tracks monthly sales performance per author (aggregated).

**Fields:**
| Field | Type | Purpose |
|-------|------|---------|
| `author` | ForeignKey(UserProfile) | Reference to author |
| `month` | DateField | First day of month (YYYY-MM-01) |
| `total_sales_count` | Integer | Total units sold across all books |
| `total_revenue` | Decimal | Total revenue from all books |
| `book_count` | Integer | Number of unique books sold |
| `total_views` | Integer | Total page views |

**Key Features:**
- Unique per author+month combination
- Indexed on (author, -month) and (-month) for fast queries
- Aggregates data across all author's books

**Use Cases:**
- "How many books did Author X sell in June 2025?"
- "What's Author Y's total monthly revenue trend?"
- **API**: List top authors by sales for a month
- **Report**: Author performance dashboard

---

### 3. **BookRecommendation** (Content App)
**Location**: `apps/content/models.py`

Stores book-to-book recommendations.

**Fields:**
| Field | Type | Purpose |
|-------|------|---------|
| `book` | ForeignKey(Book) | Source book |
| `recommended_book` | ForeignKey(Book) | Recommended book |
| `recommendation_type` | CharField | Type of recommendation |
| `score` | Decimal | Recommendation score (0-1.0) |
| `display_order` | Integer | Display order |
| `reason` | TextField | Why this book is recommended |
| `is_active` | Boolean | Is this recommendation active? |

**Recommendation Types:**
- `similar` - Similar books
- `author` - Other books by author
- `genre` - Same genre
- `trending` - Trending now
- `curated` - Curated pick
- `seasonal` - Seasonal recommendation
- `custom` - Custom recommendation

**Key Features:**
- Unique per book+recommended_book pair
- Ordered by score (descending) and display_order
- Indexed on (book, -score), recommendation_type, and is_active

**Use Cases:**
- "Show recommendations for Book X"
- "Get similar books to Book Y"
- "Curated picks for genre 'Fantasy'"
- **API**: `/books/{id}/recommendations/` endpoint

---

### 4. **BookPopularity** (Content App)
**Location**: `apps/content/models.py`

Tracks monthly popularity metrics per book.

**Fields:**
| Field | Type | Purpose |
|-------|------|---------|
| `book` | ForeignKey(Book) | Reference to book |
| `month` | DateField | First day of month (YYYY-MM-01) |
| `sales_count` | Integer | Units sold this month |
| `view_count` | Integer | Page views this month |
| `rating_count` | Integer | Number of ratings |
| `average_rating` | Decimal | Average rating |
| `popularity_score` | Decimal | Calculated score (0-100) |
| `rank` | Integer | Rank among all books |
| `popularity_status` | CharField | Status (trending/popular/moderate/new) |

**Popularity Status:**
- `trending` - Currently trending
- `popular` - Consistently popular
- `moderate` - Moderate popularity
- `new` - New release

**Key Features:**
- Unique per book+month combination
- Ordered by (-month, rank)
- Indexed on (book, -month), (-month, rank), and popularity_status

**Use Cases:**
- "Get trending books for March 2025"
- "Top 10 most popular books"
- "Rank #5 book for May 2025"
- **API**: `/books/trending/`, `/books/popular/` endpoints

---

## Database Indexes

All metrics tables have optimized indexes:

**BookSalesMetrics:**
- `(book, -month)` - Get all metrics for a book
- `(-month)` - Get all books' metrics for a month

**AuthorSalesMetrics:**
- `(author, -month)` - Get all metrics for an author
- `(-month)` - Get all authors' metrics for a month

**BookRecommendation:**
- `(book, -score)` - Get recommendations for a book
- `(recommendation_type)` - Filter by type
- `(is_active)` - Filter active only

**BookPopularity:**
- `(book, -month)` - Get popularity history for a book
- `(-month, rank)` - Get ranked books for a month
- `(popularity_status)` - Get trending/popular books

---

## API Endpoints (To Be Implemented)

### Recommended Books API
```
GET /api/books/{id}/recommendations/
```
**Response:** List of BookRecommendation objects filtered by book

### Popular Books API
```
GET /api/books/popular/?month=2025-05-01
```
**Response:** List of BookPopularity objects ranked by popularity_score

### Author Sales Report
```
GET /api/authors/{id}/sales/metrics/
```
**Response:** AuthorSalesMetrics objects across months

### Book Sales Report
```
GET /api/books/{id}/sales/metrics/
```
**Response:** BookSalesMetrics objects across months

---

## Management Commands (To Be Created)

1. **Calculate Monthly Metrics**
   ```bash
   python manage.py calculate_book_metrics --month=2025-05
   ```
   - Processes orders from the month
   - Calculates BookSalesMetrics and AuthorSalesMetrics
   - Updates BookPopularity ranks

2. **Generate Recommendations**
   ```bash
   python manage.py generate_recommendations --algorithm=collaborative
   ```
   - Generates BookRecommendation records
   - Supports multiple algorithms (collaborative, content-based, trending)

3. **Update Popularity Scores**
   ```bash
   python manage.py update_popularity_scores --month=2025-05
   ```
   - Recalculates popularity scores
   - Updates ranking and status
   - Can be run retroactively

---

## Data Flow

### Sales Metrics Generation
```
Order Created
    ↓
Order Items Added (books with prices)
    ↓
Payment Completed
    ↓
Celery Task: calculate_metrics_for_month()
    ↓
BookSalesMetrics Updated
    ↓
AuthorSalesMetrics Aggregated
    ↓
BookPopularity Calculated & Ranked
```

### Recommendation Generation
```
Algorithm Trigger (manual/scheduled)
    ↓
Analyze Similar Books (tags, genre, language)
    ↓
Analyze Author Books
    ↓
Analyze Trending (from BookPopularity)
    ↓
Generate BookRecommendation Records
    ↓
Set Scores & Display Order
```

### API Request Flow
```
GET /books/123/recommendations/
    ↓
Query BookRecommendation (book_id=123, is_active=True)
    ↓
Order by score DESC, display_order ASC
    ↓
Return with recommended_book details
```

---

## Migration Strategy

To create migrations for these new models:

```bash
# Create migrations
python manage.py makemigrations finance content

# Apply migrations
python manage.py migrate

# Verify
python manage.py dbshell
SELECT * FROM content_bookrecommendation;
SELECT * FROM finance_booksalesmetrics;
```

---

## Performance Considerations

1. **Aggregate Tables**: Metrics tables are aggregates - don't query raw orders each time
2. **Batch Updates**: Update metrics monthly using batch operations
3. **Caching**: Cache popular books in Redis for fast API responses
4. **Archiving**: Archive old popularity data (>12 months) to separate storage
5. **Denormalization**: BookPopularity denormalizes BookSalesMetrics data for ranking efficiency

---

## Example Queries

### Get monthly revenue by author
```python
from apps.finance.models import AuthorSalesMetrics
from datetime import datetime

month = datetime(2025, 5, 1)
metrics = AuthorSalesMetrics.objects.filter(
    month=month
).order_by('-total_revenue')[:10]  # Top 10 authors
```

### Get trending books
```python
from apps.content.models import BookPopularity
from datetime import datetime

month = datetime(2025, 5, 1)
trending = BookPopularity.objects.filter(
    month=month,
    popularity_status='trending'
).order_by('rank')[:20]  # Top 20 trending
```

### Get recommendations for a book
```python
from apps.content.models import BookRecommendation

recommendations = BookRecommendation.objects.filter(
    book_id=123,
    is_active=True
).order_by('-score')[:5]
```

### Author performance over time
```python
from apps.finance.models import AuthorSalesMetrics

author_metrics = AuthorSalesMetrics.objects.filter(
    author_id=456
).order_by('-month')  # Get all months
```

---

## Summary Table

| Model | App | Purpose | Unique Key | Indexes |
|-------|-----|---------|-----------|---------|
| **BookSalesMetrics** | finance | Monthly book sales tracking | (book, month) | (book, -month), (-month) |
| **AuthorSalesMetrics** | finance | Monthly author sales aggregation | (author, month) | (author, -month), (-month) |
| **BookRecommendation** | content | Book-to-book recommendations | (book, recommended_book) | (book, -score), (type), (is_active) |
| **BookPopularity** | content | Monthly book popularity ranking | (book, month) | (book, -month), (-month, rank), (status) |

---

## Next Steps

1. ✅ Models created and syntax verified
2. ⏳ Create and run migrations
3. ⏳ Create management commands for metrics calculation
4. ⏳ Implement API endpoints (serializers + views)
5. ⏳ Add Celery tasks for automatic updates
6. ⏳ Create dashboards/reports
