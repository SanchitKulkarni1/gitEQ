# app/analysis/database_detector.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.analysis.symbols import SymbolRecord


@dataclass
class DatabaseDetection:
    """Result of database detection"""
    database_type: str  # PostgreSQL, MongoDB, MySQL, etc.
    orm: Optional[str] = None  # Prisma, TypeORM, SQLAlchemy, etc.
    confidence: float = 0.0
    evidence: List[str] = None
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []


class DatabaseDetector:
    """Detects database type and ORM from imports and file patterns"""
    
    # Database patterns
    DATABASES = {
        "PostgreSQL": {
            "imports": ["psycopg2", "pg", "asyncpg", "node-postgres"],
            "content": ["postgresql://", "postgres://", "SELECT * FROM", "CREATE TABLE"],
            "files": [],
        },
        "MongoDB": {
            "imports": ["pymongo", "mongoose", "mongodb"],
            "content": ["mongodb://", "MongoClient", "db.collection", ".insertOne", ".find"],
            "files": [],
        },
        "MySQL": {
            "imports": ["mysql-connector", "mysql2", "mysqlclient", "pymysql"],
            "content": ["mysql://", "CREATE TABLE", "SELECT * FROM"],
            "files": [],
        },
        "SQLite": {
            "imports": ["sqlite3"],
            "content": [".db", "sqlite://"],
            "files": [".db", ".sqlite", ".sqlite3"],
        },
        "Redis": {
            "imports": ["redis", "ioredis", "redis-py"],
            "content": ["redis://", ".set(", ".get(", "REDIS_"],
            "files": [],
        },
        "Elasticsearch": {
            "imports": ["elasticsearch", "@elastic/elasticsearch"],
            "content": ["http://localhost:9200", "es.search", ".index("],
            "files": [],
        },
        "DynamoDB": {
            "imports": ["boto3", "aws-sdk"],
            "content": ["dynamodb", "DynamoDB", "put_item", "query"],
            "files": [],
        },
        "Cassandra": {
            "imports": ["cassandra-driver"],
            "content": ["cassandra", "SELECT * FROM", "CREATE KEYSPACE"],
            "files": [],
        },
    }
    
    # ORM patterns
    ORMS = {
        "Prisma": {
            "imports": ["@prisma/client"],
            "files": ["prisma/schema.prisma", "schema.prisma"],
            "content": ["prisma.client", "prisma.", "model User {"],
        },
        "TypeORM": {
            "imports": ["typeorm"],
            "files": ["ormconfig.json"],
            "content": ["@Entity", "@Column", "createConnection"],
        },
        "Sequelize": {
            "imports": ["sequelize"],
            "files": [],
            "content": ["new Sequelize", "sequelize.define"],
        },
        "SQLAlchemy": {
            "imports": ["sqlalchemy", "sqlalchemy.orm"],
            "files": [],
            "content": ["declarative_base", "Column(", "relationship("],
        },
        "Django ORM": {
            "imports": ["django.db"],
            "files": ["models.py"],
            "content": ["models.Model", "models.CharField", "models.ForeignKey"],
        },
        "Mongoose": {
            "imports": ["mongoose"],
            "files": [],
            "content": ["mongoose.Schema", "mongoose.model", "new Schema"],
        },
        "Drizzle": {
            "imports": ["drizzle-orm"],
            "files": ["drizzle.config"],
            "content": ["pgTable", "mysqlTable"],
        },
    }
    
    def __init__(self, files: List[str], symbols: List[SymbolRecord], file_contents: Dict[str, str]):
        self.files = files
        self.symbols = symbols
        self.file_contents = file_contents
        self.import_names = [s.name.lower() for s in symbols if s.kind == "import"]
        self.all_content = " ".join(file_contents.values()).lower()
    
    def detect_database(self) -> Optional[DatabaseDetection]:
        """Detect primary database type"""
        best_match = None
        best_confidence = 0.0
        
        for db_name, patterns in self.DATABASES.items():
            confidence, evidence = self._calculate_confidence(patterns)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = DatabaseDetection(
                    database_type=db_name,
                    confidence=confidence,
                    evidence=evidence,
                )
        
        return best_match if best_confidence > 0.3 else None
    
    def detect_orm(self) -> Optional[str]:
        """Detect ORM/database library"""
        best_match = None
        best_confidence = 0.0
        
        for orm_name, patterns in self.ORMS.items():
            confidence, _ = self._calculate_confidence(patterns)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = orm_name
        
        return best_match if best_confidence > 0.4 else None
    
    def detect_all(self) -> DatabaseDetection:
        """Detect both database and ORM"""
        db = self.detect_database()
        orm = self.detect_orm()
        
        if db:
            db.orm = orm
            return db
        
        return None
    
    def _calculate_confidence(self, patterns: Dict) -> tuple[float, List[str]]:
        """Calculate confidence score based on pattern matches"""
        evidence = []
        confidence = 0.0
        
        # Check imports (50% weight)
        import_matches = sum(
            1 for pattern in patterns.get("imports", [])
            if any(pattern.lower() in imp for imp in self.import_names)
        )
        if patterns.get("imports"):
            import_confidence = (import_matches / len(patterns["imports"])) * 0.5
            confidence += import_confidence
            if import_matches > 0:
                evidence.append(f"Import match: {import_matches}/{len(patterns['imports'])}")
        
        # Check files (30% weight)
        file_matches = sum(
            1 for pattern in patterns.get("files", [])
            if any(pattern.lower() in f.lower() for f in self.files)
        )
        if patterns.get("files"):
            file_confidence = (file_matches / len(patterns["files"])) * 0.3
            confidence += file_confidence
            if file_matches > 0:
                evidence.append(f"File match: {file_matches}/{len(patterns['files'])}")
        
        # Check content (20% weight)
        content_matches = sum(
            1 for pattern in patterns.get("content", [])
            if pattern.lower() in self.all_content
        )
        if patterns.get("content"):
            content_confidence = (content_matches / len(patterns["content"])) * 0.2
            confidence += content_confidence
            if content_matches > 0:
                evidence.append(f"Content match: {content_matches}/{len(patterns['content'])}")
        
        return min(confidence, 1.0), evidence


def detect_database(files: List[str], symbols: List[SymbolRecord], file_contents: Dict[str, str]) -> Optional[DatabaseDetection]:
    """Convenience function to detect database"""
    detector = DatabaseDetector(files, symbols, file_contents)
    return detector.detect_all()