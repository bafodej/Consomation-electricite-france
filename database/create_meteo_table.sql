-- Table météo pour enrichir les données de consommation
-- Source: API Open-Meteo (données publiques)

CREATE TABLE IF NOT EXISTS meteo (
    datetime TIMESTAMP PRIMARY KEY,
    temperature DECIMAL(5, 2) NOT NULL,
    vent DECIMAL(6, 2) NOT NULL,
    ensoleillement DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index pour jointures avec table consommation
CREATE INDEX IF NOT EXISTS idx_meteo_datetime ON meteo(datetime DESC);

-- Commentaires
COMMENT ON TABLE meteo IS 'Données météorologiques France (Open-Meteo API)';
COMMENT ON COLUMN meteo.temperature IS 'Température en degrés Celsius';
COMMENT ON COLUMN meteo.vent IS 'Vitesse du vent en km/h';
COMMENT ON COLUMN meteo.ensoleillement IS 'Taux ensoleillement 0-100%';
