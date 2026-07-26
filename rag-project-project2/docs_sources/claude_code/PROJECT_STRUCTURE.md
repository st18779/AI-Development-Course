# Project Structure

Here's the complete folder and file structure of the Order Management API Phase 1 project:

```
ProjectAi/
│
├── OrderManagementAPI/                     # Main API project
│   ├── bin/                               # Compiled output (auto-generated)
│   ├── obj/                               # Build artifacts (auto-generated)
│   │
│   ├── Controllers/                       # API Controllers
│   │   ├── ProductsController.cs          # Product endpoints
│   │   ├── OrdersController.cs            # Order endpoints
│   │   └── InventoryController.cs         # Inventory endpoints
│   │
│   ├── Models/                            # Domain Models
│   │   ├── Product.cs                     # Product entity
│   │   ├── Inventory.cs                   # Inventory entity
│   │   ├── Order.cs                       # Order entity & OrderStatus enum
│   │   └── OrderItem.cs                   # Order item entity
│   │
│   ├── Data/                              # Database Layer
│   │   └── OrderManagementDbContext.cs    # EF Core DbContext
│   │
│   ├── Services/                          # Business Logic Layer
│   │   ├── ProductService.cs              # Product business logic
│   │   ├── InventoryService.cs            # Inventory management
│   │   ├── OrderService.cs                # Order processing
│   │   └── NotificationService.cs         # Order notifications
│   │
│   ├── Migrations/                        # EF Core Migrations (auto-generated)
│   │   └── .gitkeep                       # Placeholder for migrations
│   │
│   ├── Properties/
│   │   └── launchSettings.json            # Local run settings
│   │
│   ├── Dockerfile                         # Multi-stage Docker image
│   ├── .dockerignore                      # Docker build ignore file
│   │
│   ├── appsettings.json                   # Default configuration
│   ├── appsettings.Development.json       # Development settings
│   ├── appsettings.Docker.json            # Docker container settings
│   │
│   ├── Program.cs                         # Application entry point & setup
│   ├── OrderManagementAPI.csproj          # Project file (NuGet packages)
│   │
│   └── [Auto-generated files]
│       ├── Properties/
│       ├── bin/
│       └── obj/
│
├── docker-compose.yml                     # Docker Compose orchestration
│
├── README.md                              # Main project documentation
├── SETUP_GUIDE.md                         # CLI setup instructions
├── PROJECT_STRUCTURE.md                   # This file
├── API_TESTING_GUIDE.md                   # API testing examples
│
└── .gitignore                             # Git ignore rules

```

## File Descriptions

### Controllers (`/Controllers`)

| File | Purpose |
|------|---------|
| `ProductsController.cs` | Handles product CRUD operations |
| `OrdersController.cs` | Handles order creation, approval, rejection |
| `InventoryController.cs` | Handles inventory management |

**Key Methods:**
- **ProductsController**: `GetAllProducts()`, `GetProductById()`, `CreateProduct()`, `DeleteProduct()`
- **OrdersController**: `GetAllOrders()`, `GetOrderById()`, `CreateOrder()`, `ApproveOrder()`, `RejectOrder()`
- **InventoryController**: `GetInventory()`, `InitializeInventory()`, `ReserveInventory()`, `ReleaseInventory()`

### Models (`/Models`)

| File | Purpose |
|------|---------|
| `Product.cs` | Product entity with name, description, price |
| `Inventory.cs` | Inventory tracking (available & reserved quantities) |
| `Order.cs` | Order entity with order items and status |
| `OrderItem.cs` | Individual item in an order |

**Relationships:**
```
Product (1) ─── (Many) Inventory
Product (1) ─── (Many) OrderItem
Order (1) ─── (Many) OrderItem
```

### Data (`/Data`)

| File | Purpose |
|------|---------|
| `OrderManagementDbContext.cs` | EF Core DbContext with all entity configurations, relationships, and constraints |

**Configured Tables:**
- Products (with seed indices)
- Inventories (with unique constraint on ProductId)
- Orders (with unique constraint on OrderNumber)
- OrderItems (with cascade delete)

### Services (`/Services`)

| File | Purpose |
|------|---------|
| `ProductService.cs` | Product business logic (CRUD) |
| `InventoryService.cs` | Inventory reservation and release logic |
| `OrderService.cs` | Order creation, approval, rejection logic |
| `NotificationService.cs` | Console logging for order events |

**Design:**
- Interface-based for future abstraction
- Dependency injection ready
- Structured logging throughout

### Configuration Files

| File | Purpose |
|------|---------|
| `Program.cs` | Application startup, service registration, middleware setup |
| `appsettings.json` | Default SQL Server connection string |
| `appsettings.Development.json` | Local SQL Server settings (Windows Auth) |
| `appsettings.Docker.json` | Container SQL Server settings (sa user) |
| `OrderManagementAPI.csproj` | NuGet package references |

### Docker Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build (SDK → Publish → Runtime) |
| `docker-compose.yml` | Orchestrates API + SQL Server services |
| `.dockerignore` | Excludes unnecessary files from Docker context |

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Complete project overview, features, setup instructions |
| `SETUP_GUIDE.md` | Step-by-step CLI commands to recreate project |
| `PROJECT_STRUCTURE.md` | This file - folder organization |
| `API_TESTING_GUIDE.md` | Curl/PowerShell examples to test all endpoints |

### Git Files

| File | Purpose |
|------|---------|
| `.gitignore` | Excludes build artifacts, packages, logs from version control |

## Database Schema

### Products Table
```sql
CREATE TABLE Products (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(200) NOT NULL,
    Description NVARCHAR(1000) NOT NULL,
    Price DECIMAL(18,2),
    CreatedAt DATETIME2,
    UpdatedAt DATETIME2
)
```

### Inventories Table
```sql
CREATE TABLE Inventories (
    Id INT PRIMARY KEY IDENTITY(1,1),
    ProductId INT NOT NULL UNIQUE,
    QuantityAvailable INT NOT NULL,
    QuantityReserved INT NOT NULL,
    UpdatedAt DATETIME2,
    FOREIGN KEY (ProductId) REFERENCES Products(Id) ON DELETE CASCADE
)
```

### Orders Table
```sql
CREATE TABLE Orders (
    Id INT PRIMARY KEY IDENTITY(1,1),
    OrderNumber NVARCHAR(50) NOT NULL UNIQUE,
    CreatedAt DATETIME2,
    Status INT NOT NULL,
    TotalAmount DECIMAL(18,2),
    Notes NVARCHAR(MAX),
    UpdatedAt DATETIME2
)
```

### OrderItems Table
```sql
CREATE TABLE OrderItems (
    Id INT PRIMARY KEY IDENTITY(1,1),
    OrderId INT NOT NULL,
    ProductId INT NOT NULL,
    Quantity INT NOT NULL,
    UnitPrice DECIMAL(18,2),
    TotalPrice DECIMAL(18,2),
    FOREIGN KEY (OrderId) REFERENCES Orders(Id) ON DELETE CASCADE,
    FOREIGN KEY (ProductId) REFERENCES Products(Id) ON DELETE RESTRICT
)
```

## NuGet Packages

| Package | Version | Purpose |
|---------|---------|---------|
| `Microsoft.AspNetCore.OpenApi` | 8.0.28 | OpenAPI support |
| `Swashbuckle.AspNetCore` | 6.6.2 | Swagger UI documentation |
| `Microsoft.EntityFrameworkCore` | 8.0.11 | ORM framework |
| `Microsoft.EntityFrameworkCore.SqlServer` | 8.0.11 | SQL Server provider |
| `Microsoft.EntityFrameworkCore.Tools` | 8.0.11 | CLI tools for migrations |

## Key Features in Code

### 1. **Dependency Injection**
```csharp
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IInventoryService, InventoryService>();
builder.Services.AddScoped<IOrderService, OrderService>();
builder.Services.AddScoped<INotificationService, NotificationService>();
```

### 2. **Automatic Migrations**
```csharp
using (var scope = app.Services.CreateScope())
{
    var dbContext = scope.ServiceProvider.GetRequiredService<OrderManagementDbContext>();
    dbContext.Database.Migrate();
}
```

### 3. **Inventory Reservation on Order Creation**
- Automatic reserve on order creation
- Automatic release on order rejection
- Transaction-like behavior

### 4. **Structured Logging**
- ILogger injected into all services
- Console output with structured format
- Order approval/rejection notifications

### 5. **CORS Support**
```csharp
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", builder =>
    {
        builder.AllowAnyOrigin()
               .AllowAnyMethod()
               .AllowAnyHeader();
    });
});
```

## Deployment Readiness

✅ **Production Ready for Phase 1:**
- Multi-stage Dockerfile for optimized images
- Docker Compose for local testing
- Environment-specific configurations
- Structured logging
- Error handling and validation
- Database migrations

✅ **Ready for Microservices Migration:**
- Clean separation of concerns
- Service interfaces for easy replacement
- Independent service layer
- Dependency injection throughout
- No hard dependencies between services

## Next Steps (Phase 2)

The structure is designed to facilitate:
- **Unit Testing** - Services can be tested independently
- **Integration Testing** - Full API flow testing
- **Microservices Split** - Each service can become independent
- **API Versioning** - Controllers support route versioning
- **Authentication** - Easy to add auth middleware
- **Caching** - Services can be wrapped with caching layer
