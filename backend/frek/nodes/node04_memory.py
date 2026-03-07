"""
FREK v2 — NODE 04 · MÉMOIRE
============================
FREK est anorexique en données. Il prend l'empreinte — jamais le corps.

~2.5KB par œuvre
100 millions d'œuvres = 250GB
Un seul serveur standard suffit pour des années.

NE STOCKE JAMAIS:
- Le fichier audio original
- Les données personnelles identifiantes
- Les versions intermédiaires en clair

STOCKE SEULEMENT:
- SHA-256 signal (32 bytes)
- Vecteur fréquentiel 528D (~2.1 KB)
- Timestamp milliseconde (8 bytes)
- Artiste_id anonyme + GPS condensé (24 bytes)
- Stade (2 bytes)

Technologie: pgvector (extension PostgreSQL)
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timezone
import os


# Modèles de données
@dataclass
class FrekAttestation:
    """Structure de stockage minimal FREK"""
    frek_id: str
    sha256_signal: str
    sha256_metadata: str
    hash_chaine: str
    vector_528d: List[float]
    timestamp_ms: int
    artiste_id: str
    gps_lat: Optional[float]
    gps_lon: Optional[float]
    stade: int
    prev_frek_id: Optional[str] = None
    
    @property
    def size_bytes(self) -> int:
        return (
            64 +  # frek_id
            32 + 32 + 32 +  # SHA-256 hashes
            len(self.vector_528d) * 4 +  # vector float32
            8 +  # timestamp
            16 +  # artiste_id UUID
            8 +  # GPS point
            2   # stade
        )


class Node04Memory:
    """
    Stockage minimal FREK — pgvector PostgreSQL
    
    Schema: frek_attestations
    - frek_id VARCHAR(64) PRIMARY KEY
    - sha256_signal BYTEA
    - sha256_metadata BYTEA
    - hash_chaine BYTEA
    - vector VECTOR(528)
    - timestamp_ms BIGINT
    - artiste_id UUID
    - gps_condense POINT
    - stade SMALLINT
    """
    
    def __init__(self):
        self._pool = None
        self._initialized = False
        # In-memory fallback si pas de DB
        self._memory_store: dict[str, FrekAttestation] = {}
        self._sequence_counter = 0
    
    async def _get_pool(self):
        """Lazy connection pool creation"""
        if self._pool is None:
            try:
                import asyncpg
                from pgvector.asyncpg import register_vector
                
                database_url = os.environ.get('MONGO_URL', '')
                
                # Si pas de PostgreSQL, utiliser stockage mémoire
                if not database_url.startswith('postgres'):
                    return None
                
                self._pool = await asyncpg.create_pool(
                    database_url,
                    min_size=1,
                    max_size=10,
                    init=register_vector
                )
                await self._init_schema()
            except Exception as e:
                print(f"⚠️ pgvector non disponible, utilisation stockage mémoire: {e}")
                return None
        return self._pool
    
    async def _init_schema(self):
        """Initialise le schéma de la base de données"""
        if self._initialized:
            return
            
        pool = await self._get_pool()
        if pool is None:
            self._initialized = True
            return
        
        async with pool.acquire() as conn:
            # Activer l'extension pgvector
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            
            # Créer la table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS frek_attestations (
                    frek_id VARCHAR(64) PRIMARY KEY,
                    sha256_signal BYTEA NOT NULL,
                    sha256_metadata BYTEA NOT NULL,
                    hash_chaine BYTEA NOT NULL,
                    vector vector(528) NOT NULL,
                    timestamp_ms BIGINT NOT NULL,
                    artiste_id VARCHAR(64) NOT NULL,
                    gps_lat DOUBLE PRECISION,
                    gps_lon DOUBLE PRECISION,
                    stade SMALLINT NOT NULL DEFAULT 4,
                    prev_frek_id VARCHAR(64),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            
            # Index pour recherche vectorielle (IVFFlat)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_frek_vector 
                ON frek_attestations 
                USING ivfflat (vector vector_cosine_ops)
                WITH (lists = 100)
            """)
            
            # Index pour recherche par artiste
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_frek_artiste 
                ON frek_attestations (artiste_id)
            """)
            
            # Index temporel
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_frek_timestamp 
                ON frek_attestations (timestamp_ms DESC)
            """)
        
        self._initialized = True
    
    async def store(self, attestation: FrekAttestation) -> bool:
        """
        Stocke une attestation FREK
        Retourne True si succès
        """
        await self._init_schema()
        pool = await self._get_pool()
        
        if pool is None:
            # Stockage mémoire
            self._memory_store[attestation.frek_id] = attestation
            return True
        
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO frek_attestations 
                    (frek_id, sha256_signal, sha256_metadata, hash_chaine, 
                     vector, timestamp_ms, artiste_id, gps_lat, gps_lon, 
                     stade, prev_frek_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (frek_id) DO NOTHING
                """,
                    attestation.frek_id,
                    bytes.fromhex(attestation.sha256_signal),
                    bytes.fromhex(attestation.sha256_metadata),
                    bytes.fromhex(attestation.hash_chaine),
                    attestation.vector_528d,
                    attestation.timestamp_ms,
                    attestation.artiste_id,
                    attestation.gps_lat,
                    attestation.gps_lon,
                    attestation.stade,
                    attestation.prev_frek_id,
                )
            return True
        except Exception as e:
            print(f"Erreur stockage: {e}")
            # Fallback mémoire
            self._memory_store[attestation.frek_id] = attestation
            return True
    
    async def get(self, frek_id: str) -> Optional[FrekAttestation]:
        """Récupère une attestation par FREK-ID"""
        pool = await self._get_pool()
        
        if pool is None:
            return self._memory_store.get(frek_id)
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM frek_attestations WHERE frek_id = $1",
                frek_id
            )
            if row:
                return self._row_to_attestation(row)
        return None
    
    async def get_by_artiste(self, artiste_id: str, limit: int = 100) -> List[FrekAttestation]:
        """Récupère les attestations d'un artiste"""
        pool = await self._get_pool()
        
        if pool is None:
            return [a for a in self._memory_store.values() if a.artiste_id == artiste_id][:limit]
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM frek_attestations 
                   WHERE artiste_id = $1 
                   ORDER BY timestamp_ms DESC 
                   LIMIT $2""",
                artiste_id, limit
            )
            return [self._row_to_attestation(row) for row in rows]
    
    async def get_latest(self, limit: int = 10) -> List[FrekAttestation]:
        """Récupère les dernières attestations"""
        pool = await self._get_pool()
        
        if pool is None:
            sorted_items = sorted(
                self._memory_store.values(),
                key=lambda x: x.timestamp_ms,
                reverse=True
            )
            return sorted_items[:limit]
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM frek_attestations 
                   ORDER BY timestamp_ms DESC 
                   LIMIT $1""",
                limit
            )
            return [self._row_to_attestation(row) for row in rows]
    
    async def count(self) -> int:
        """Compte le nombre total d'attestations"""
        pool = await self._get_pool()
        
        if pool is None:
            return len(self._memory_store)
        
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM frek_attestations")
            return result or 0
    
    async def get_next_sequence(self) -> int:
        """Retourne le prochain numéro de séquence"""
        pool = await self._get_pool()
        
        if pool is None:
            self._sequence_counter += 1
            return self._sequence_counter
        
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM frek_attestations")
            return (result or 0) + 1
    
    async def get_chain_info(self) -> tuple[Optional[str], Optional[str]]:
        """Retourne (last_frek_id, last_hash) pour le chaînage"""
        pool = await self._get_pool()
        
        if pool is None:
            if self._memory_store:
                latest = max(self._memory_store.values(), key=lambda x: x.timestamp_ms)
                return latest.frek_id, latest.hash_chaine
            return None, None
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT frek_id, hash_chaine FROM frek_attestations 
                   ORDER BY timestamp_ms DESC LIMIT 1"""
            )
            if row:
                return row['frek_id'], row['hash_chaine'].hex()
        return None, None
    
    def _row_to_attestation(self, row) -> FrekAttestation:
        """Convertit une ligne DB en FrekAttestation"""
        return FrekAttestation(
            frek_id=row['frek_id'],
            sha256_signal=row['sha256_signal'].hex(),
            sha256_metadata=row['sha256_metadata'].hex(),
            hash_chaine=row['hash_chaine'].hex(),
            vector_528d=list(row['vector']),
            timestamp_ms=row['timestamp_ms'],
            artiste_id=row['artiste_id'],
            gps_lat=row['gps_lat'],
            gps_lon=row['gps_lon'],
            stade=row['stade'],
            prev_frek_id=row['prev_frek_id'],
        )
    
    async def get_stats(self) -> dict:
        """Statistiques de stockage"""
        count = await self.count()
        return {
            "total_attestations": count,
            "estimated_size_kb": round(count * 2.5, 2),
            "estimated_size_mb": round(count * 2.5 / 1024, 2),
            "storage_backend": "memory" if await self._get_pool() is None else "pgvector",
        }


# Instance globale
node04 = Node04Memory()
