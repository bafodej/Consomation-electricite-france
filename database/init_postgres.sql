-- Script d'initialisation PostgreSQL pour RTE Consommation
-- Base de donnees : rte_consommation
-- PostgreSQL 16

-- Table principale : consommation electrique
CREATE TABLE IF NOT EXISTS consommation (
    datetime TIMESTAMP PRIMARY KEY,
    mw_conso DECIMAL(10, 2) NOT NULL CHECK (mw_conso > 0),
    region VARCHAR(50) NOT NULL DEFAULT 'France',
    source VARCHAR(20) NOT NULL CHECK (source IN ('RTE_API', 'SYNTHETIC')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index pour optimiser les requetes temporelles
CREATE INDEX IF NOT EXISTS idx_consommation_datetime ON consommation(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_consommation_created_at ON consommation(created_at);

-- Table previsions
CREATE TABLE IF NOT EXISTS prevision (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    mw_prevision DECIMAL(10, 2) NOT NULL CHECK (mw_prevision > 0),
    type_prevision VARCHAR(10) NOT NULL CHECK (type_prevision IN ('J', 'J-1')),
    datetime_creation TIMESTAMP DEFAULT NOW(),
    consommation_datetime TIMESTAMP,
    FOREIGN KEY (consommation_datetime)
        REFERENCES consommation(datetime)
        ON DELETE CASCADE
);

-- Index pour requetes frequentes
CREATE INDEX IF NOT EXISTS idx_prevision_datetime ON prevision(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_prevision_type ON prevision(type_prevision);
CREATE INDEX IF NOT EXISTS idx_prevision_consommation ON prevision(consommation_datetime);

-- Commentaires sur les tables
COMMENT ON TABLE consommation IS 'Donnees de consommation electrique France (RTE)';
COMMENT ON TABLE prevision IS 'Previsions de consommation J et J-1';

-- Commentaires sur les colonnes
COMMENT ON COLUMN consommation.datetime IS 'Date et heure UTC de la mesure';
COMMENT ON COLUMN consommation.mw_conso IS 'Consommation en megawatts';
COMMENT ON COLUMN consommation.source IS 'Origine: RTE_API (reel) ou SYNTHETIC (genere)';
COMMENT ON COLUMN prevision.mw_prevision IS 'Prevision de consommation en megawatts';
COMMENT ON COLUMN prevision.type_prevision IS 'Type: J (meme jour) ou J-1 (veille)';

-- Activation autovacuum pour maintenance automatique
ALTER TABLE consommation SET (autovacuum_enabled = true);
ALTER TABLE prevision SET (autovacuum_enabled = true);
