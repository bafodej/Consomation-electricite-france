-- Script d'initialisation PostgreSQL pour RTE Consommation
-- Base de donnees : rte_consommation
-- PostgreSQL 16

-- Table principale : consommation electrique
CREATE TABLE IF NOT EXISTS consumption (
    datetime TIMESTAMP PRIMARY KEY,
    mw_consumption DECIMAL(10, 2) NOT NULL CHECK (mw_consumption > 0),
    region VARCHAR(50) NOT NULL DEFAULT 'France',
    source VARCHAR(20) NOT NULL CHECK (source IN ('RTE_API', 'SYNTHETIC')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index pour optimiser les requetes temporelles
CREATE INDEX IF NOT EXISTS idx_consumption_datetime ON consumption(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_consumption_created_at ON consumption(created_at);

-- Table previsions
CREATE TABLE IF NOT EXISTS prevision (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP NOT NULL,
    mw_forecast DECIMAL(10, 2) NOT NULL CHECK (mw_forecast > 0),
    type_prevision VARCHAR(10) NOT NULL CHECK (type_prevision IN ('J', 'J-1')),
    datetime_creation TIMESTAMP DEFAULT NOW(),
    consumption_datetime TIMESTAMP,
    FOREIGN KEY (consumption_datetime)
        REFERENCES consumption(datetime)
        ON DELETE CASCADE
);

-- Index pour requetes frequentes
CREATE INDEX IF NOT EXISTS idx_prevision_datetime ON prevision(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_prevision_type ON prevision(type_prevision);
CREATE INDEX IF NOT EXISTS idx_prevision_consumption ON prevision(consumption_datetime);

-- Commentaires sur les tables
COMMENT ON TABLE consumption IS 'Donnees de consommation electrique France (RTE)';
COMMENT ON TABLE prevision IS 'Previsions de consommation J et J-1';

-- Commentaires sur les colonnes
COMMENT ON COLUMN consumption.datetime IS 'Date et heure UTC de la mesure';
COMMENT ON COLUMN consumption.mw_consumption IS 'Consommation en megawatts';
COMMENT ON COLUMN consumption.source IS 'Origine: RTE_API (reel) ou SYNTHETIC (genere)';
COMMENT ON COLUMN prevision.mw_forecast IS 'Prevision de consommation en megawatts';
COMMENT ON COLUMN prevision.type_prevision IS 'Type: J (meme jour) ou J-1 (veille)';

-- Activation autovacuum pour maintenance automatique
ALTER TABLE consumption SET (autovacuum_enabled = true);
ALTER TABLE prevision SET (autovacuum_enabled = true);
