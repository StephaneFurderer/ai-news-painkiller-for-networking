# PostgreSQL + pgvector Setup Guide

## Quick Start (macOS)

### 1. Install PostgreSQL
```bash
# Using Homebrew
brew install postgresql@15
brew services start postgresql@15

# Or using PostgreSQL.app (easier GUI option)
# Download from: https://postgresapp.com/
```

### 2. Install pgvector extension

**Option A: Using Homebrew (Easiest)**
```bash
brew install pgvector
```

**Option B: Build from source (if Homebrew doesn't work)**
```bash
# First ensure you have build tools
xcode-select --install

# Install PostgreSQL development headers if not already installed
brew install postgresql@15

# Clone and build pgvector
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector

# Make sure pg_config is in PATH
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"  # For M1 Macs
# OR
export PATH="/usr/local/opt/postgresql@15/bin:$PATH"     # For Intel Macs

# Build and install
make
sudo make install
```

**Option C: Use Docker (Skip compilation entirely)**
```bash
# This gives you PostgreSQL + pgvector ready to go
docker run -d \
  --name postgres-vector \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=vector_sandbox \
  -p 5432:5432 \
  pgvector/pgvector:pg15
```

### 3. Create database and user
```sql
-- Connect to PostgreSQL
psql postgres

-- Create database
CREATE DATABASE vector_sandbox;

-- Create user (optional, or use your existing user)
CREATE USER vector_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE vector_sandbox TO vector_user;

-- Connect to your new database
\c vector_sandbox

-- Enable pgvector extension
CREATE EXTENSION vector;

-- Test it works
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 4. Install Python dependencies
```bash
pip install psycopg2-binary openai numpy python-dotenv
```

### 5. Update sandbox configuration
Edit the `db_config` in `vector_db_sandbox.py`:
```python
db_config = {
    'host': 'localhost',
    'database': 'vector_sandbox',
    'user': 'your_username',        # Your PostgreSQL user
    'password': 'your_password',    # Your PostgreSQL password
    'port': 5432
}
```

### 6. Run the sandbox
```bash
python vector_db_sandbox.py
```

## Alternative: Docker Setup

If you prefer Docker:

```bash
# Run PostgreSQL with pgvector
docker run -d \
  --name postgres-vector \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=vector_sandbox \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# Connect and test
docker exec -it postgres-vector psql -U postgres -d vector_sandbox
```

Then use these connection settings:
```python
db_config = {
    'host': 'localhost',
    'database': 'vector_sandbox',
    'user': 'postgres',
    'password': 'mysecretpassword',
    'port': 5432
}
```

## Troubleshooting

### pgvector installation fails
- Make sure you have PostgreSQL development headers: `brew install postgresql@15`
- Try the Docker approach instead

### Connection refused
- Check PostgreSQL is running: `brew services list | grep postgresql`
- Start if needed: `brew services start postgresql@15`

### Permission denied
- Make sure your user has database creation privileges
- Or run as postgres superuser initially

## Next Steps

Once you have the sandbox working:
1. Run through all the demos to understand concepts
2. Experiment with your own text examples
3. Try different similarity thresholds
4. Ready to integrate with your pipeline!