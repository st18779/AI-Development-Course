# Setup Guide - CLI Commands

This guide provides all the CLI commands used to create the Order Management API Phase 1 project from scratch.

## Prerequisites

- Windows OS (for PowerShell examples)
- .NET 8.0 SDK or later
- Docker Desktop (for containerization)

## Step 1: Install .NET 8.0 SDK

```powershell
# Check if .NET is installed
dotnet --version

# If not installed, download from https://dotnet.microsoft.com/download
# Or use the installer: https://aka.ms/dotnet/download
```

## Step 2: Create the WebAPI Project

```powershell
# Navigate to desired directory
cd "c:\Users\avish\OneDrive\Desktop\ProjectAi"

# Create new WebAPI project
dotnet new webapi -n OrderManagementAPI -f net8.0

# Navigate into the project
cd OrderManagementAPI
```

## Step 3: Add NuGet Packages

```powershell
# Install Entity Framework Core
dotnet add package Microsoft.EntityFrameworkCore --version 8.0.11

# Install SQL Server provider
dotnet add package Microsoft.EntityFrameworkCore.SqlServer --version 8.0.11

# Install EF Core Tools
dotnet add package Microsoft.EntityFrameworkCore.Tools --version 8.0.11
```

## Step 4: Verify Build

```powershell
# Restore packages
dotnet restore

# Build project
dotnet build
```

## Step 5: Create Folder Structure

```powershell
# Create required folders
New-Item -Type Directory -Path "Models"
New-Item -Type Directory -Path "Data"
New-Item -Type Directory -Path "Services"
New-Item -Type Directory -Path "Migrations"
```

Or using `mkdir`:

```bash
mkdir Models
mkdir Data
mkdir Services
mkdir Migrations
```

## Step 6: Create Models

Create the following files in the Models folder:
- `Product.cs`
- `Inventory.cs`
- `Order.cs`
- `OrderItem.cs`

(See the Models directory in the project)

## Step 7: Create DbContext

Create `Data/OrderManagementDbContext.cs` with all entity configurations.

## Step 8: Create Services

Create the following files in the Services folder:
- `ProductService.cs`
- `InventoryService.cs`
- `OrderService.cs`
- `NotificationService.cs`

## Step 9: Create Controllers

Create the following files in the Controllers folder:
- `ProductsController.cs`
- `OrdersController.cs`
- `InventoryController.cs`

## Step 10: Update Program.cs

Update the Program.cs file to register services and configure DbContext.

## Step 11: Configure appsettings

Update the following files:
- `appsettings.json` - Default connection string
- `appsettings.Development.json` - Local SQL Server settings
- `appsettings.Docker.json` - Docker container settings

## Step 12: Create Docker Files

### Create Dockerfile

In the OrderManagementAPI directory, create a multi-stage Dockerfile.

### Create docker-compose.yml

In the root directory, create docker-compose.yml with SQL Server and API services.

## Step 13: Final Build

```powershell
# Clean build
dotnet clean
dotnet build

# Or publish
dotnet publish -c Release -o ./publish
```

## Step 14: Run the Application

### Option A: Docker Compose (Recommended)

```powershell
# From root directory
cd ..
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option B: Local Development

```powershell
# Ensure SQL Server is running locally

# Run the application
dotnet run

# Application will start at:
# http://localhost:5000 (HTTP)
# https://localhost:5001 (HTTPS)
# Swagger: http://localhost:5000/swagger
```

## Database Migrations

### Manual Migration Creation (Optional)

```powershell
# Install EF Core CLI globally
dotnet tool install --global dotnet-ef --version 8.0.11

# Create migration
dotnet-ef migrations add InitialCreate

# Update database
dotnet-ef database update

# Remove last migration
dotnet-ef migrations remove

# View migrations
dotnet-ef migrations list
```

**Note:** Automatic migrations are enabled in Program.cs, so the database is created automatically on startup.

## Quick Reference Commands

```powershell
# Build
dotnet build

# Run
dotnet run

# Run with watch (reload on changes)
dotnet watch run

# Test
dotnet test

# Restore packages
dotnet restore

# Clean
dotnet clean

# Publish
dotnet publish -c Release

# Install local tool
dotnet tool install --local dotnet-ef

# List installed tools
dotnet tool list

# List available packages
dotnet package search EntityFrameworkCore
```

## Docker Commands

```bash
# Build image
docker build -t ordermanagement-api .

# Run container
docker run -p 5000:5000 ordermanagement-api

# Docker Compose
docker-compose up -d         # Start in background
docker-compose down          # Stop and remove containers
docker-compose down -v       # Stop and remove volumes
docker-compose logs -f api   # View logs
docker-compose ps            # View running services
```

## Useful SQL Server Commands

```sql
-- Connect to database
sqlcmd -S . -E

-- Check databases
SELECT name FROM sys.databases;

-- Use database
USE OrderManagementDB;

-- View tables
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES;

-- View data
SELECT * FROM Products;
SELECT * FROM Orders;
SELECT * FROM Inventories;
SELECT * FROM OrderItems;

-- Count rows
SELECT COUNT(*) FROM Products;
SELECT COUNT(*) FROM Orders;
```

## Troubleshooting Commands

```powershell
# Check .NET installation
dotnet --list-sdks
dotnet --list-runtimes

# Check project structure
Get-ChildItem -Recurse -Include *.cs | Select-Object FullName

# Verify build
dotnet build --no-restore --verbosity=diagnostic

# Check ports
netstat -ano | findstr :5000
netstat -ano | findstr :1433
```

## Environment Setup Verification

```powershell
# 1. Check .NET
dotnet --version

# 2. Check Docker
docker --version
docker-compose --version

# 3. Build the project
cd OrderManagementAPI
dotnet build

# 4. Run tests on Docker
docker-compose up --build
docker-compose logs api
```

## Additional Resources

- [Microsoft .NET Documentation](https://learn.microsoft.com/en-us/dotnet)
- [ASP.NET Core Tutorial](https://learn.microsoft.com/en-us/aspnet/core/tutorials/first-web-api)
- [Entity Framework Core](https://learn.microsoft.com/en-us/ef/core)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices)
