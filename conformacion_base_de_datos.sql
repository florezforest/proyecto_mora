-- VISTAZO A LA TABLA
SELECT *
FROM crop_recommendation
LIMIT 40;

------------------------------------------------------------------------------------------------------------

-- CREACIÓN DE TABLA SECUNDARIA

DROP TABLE IF EXISTS crop_environmental_requirements;

CREATE TABLE crop_environmental_requirements (
	crop_code INT NOT NULL ,
	crop TEXT NOT NULL,
	temperature_min REAL,
	temperature_max REAL,
	rainfall_min REAL,
	rainfall_max REAL,
	PRIMARY KEY (crop_code) -- CLAVE PRIMARIA
);

INSERT INTO crop_environmental_requirements
(crop_code, crop, temperature_min, temperature_max, rainfall_min, rainfall_max)
VALUES
(1, 'rice', 20.0, 33.0, 1000.0, 2500.0),
(2, 'maize', 10.0, 40.0, 400.0, 2200.0),
(3, 'chickpea', 20.0, 30.0, 300.0, 700.0),
(4, 'kidneybeans', 18.0, 30.0, 500.0, 1500.0),
(5, 'pigeonpeas', 18.0, 32.0, 400.0, 1000.0),
(6, 'mothbeans', 20.0, 35.0, 200.0, 800.0),
(7, 'mungbean', 22.0, 35.0, 300.0, 900.0),
(8, 'blackgram', 20.0, 35.0, 400.0, 1200.0),
(9, 'lentil', 15.0, 27.0, 300.0, 800.0),
(10, 'pomegranate', 25.0, 35.0, 500.0, 1200.0),
(11, 'banana', 21.0, 35.0, 1200.0, 2500.0),
(12, 'mango', 24.0, 35.0, 750.0, 2500.0),
(13, 'grapes', 15.0, 35.0, 500.0, 1200.0),
(14, 'watermelon', 20.0, 30.0, 400.0, 600.0),
(15, 'muskmelon', 18.0, 30.0, 300.0, 500.0),
(16, 'apple', 6.0, 24.0, 1000.0, 1500.0),
(17, 'orange', 15.0, 30.0, 1000.0, 2000.0),
(18, 'papaya', 22.0, 32.0, 1000.0, 2000.0),
(19, 'coconut', 20.0, 32.0, 1000.0, 3000.0),
(20, 'cotton', 18.0, 35.0, 500.0, 1000.0),
(21, 'jute', 24.0, 38.0, 1500.0, 2500.0),
(22, 'coffee', 15.0, 28.0, 1500.0, 2500.0);


SELECT * FROM crop_environmental_requirements;

------------------------------------------------------------------------------------------------------------

-- Departamentos recomendados

DROP TABLE IF EXISTS departamentos_recomendados;

CREATE TABLE departamentos_recomendados (
  id_depto INTEGER PRIMARY KEY, -- CLAVE PRIMARIA
  departamento_colombia TEXT NOT NULL,
  zona_vida TEXT DEFAULT NULL
);

-- Volcado de datos para la tabla `departamentos_recomendados`

INSERT INTO departamentos_recomendados (id_depto, departamento_colombia, zona_vida)
VALUES
(1, 'Llanos orientales', 'X'),
(2, 'Cauca', 'X'),
(3, 'Huila', 'X'),
(4, 'Valle del Cauca', 'X'),
(5, 'Meta', 'X'),
(6, 'Boyacá', 'X'),
(7, 'Nariño', 'X'),
(8, 'Santander', 'X'),
(9, 'Atlántico', 'X'),
(10, 'Arauca', 'X'),
(11, 'Magdalena', 'X'),
(12, 'Caribe', 'X'),
(13, 'Cundinamarca', 'X');

------------------------------------------------------------------------------------------------------------

-- ADAPTACIÓN DE LA TABLA PRINCIPAL

DROP TABLE IF EXISTS crop_recommendation_n;

CREATE TABLE crop_recommendation_n ( -- n: nueva copia para dejar original intacta
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    N BIGINT,
    P BIGINT,
    K BIGINT,
    temperature FLOAT,
    humidity FLOAT,
    ph FLOAT,
    rainfall FLOAT,
    crop TEXT,
    crop_code INT,
    depto_code INT,
    FOREIGN KEY (crop_code) REFERENCES crop_environmental_requirements(crop_code),
    FOREIGN KEY (depto_code) REFERENCES departamentos_recomendados(id_depto)
);

SELECT * FROM crop_recommendation_n;

INSERT INTO crop_recommendation_n 
(N, P, K, temperature, humidity, ph, rainfall, crop)
SELECT N, P, K, temperature, humidity, ph, rainfall, label 
FROM crop_recommendation;

SELECT * FROM crop_environmental_requirements;


-- Condiciones ambientales (INSERTAR CÓDIGOS EN TABLA PRINCIPAL)

UPDATE crop_recommendation_n
SET crop_code = (
	SELECT cer.crop_code
	FROM crop_environmental_requirements AS cer
	WHERE crop_recommendation_n.crop = cer.crop
);

UPDATE crop_recommendation_n
SET depto_code = (
	CASE
		WHEN crop = 'rice' THEN 1
		WHEN crop = 'maize' THEN 1
		WHEN crop = 'chickpea' THEN 2
		WHEN crop = 'kidneybeans' THEN 3
		WHEN crop = 'watermelon' THEN 5
		WHEN crop = 'apple' THEN 6
		WHEN crop = 'orange' THEN 8
		WHEN crop = 'pigeonpeas' THEN 9
		WHEN crop = 'mothbeans' THEN 7
		WHEN crop = 'blackgram' THEN 7
		WHEN crop = 'banana' THEN 10
		WHEN crop = 'mango' THEN 13
		WHEN crop = 'grapes' THEN 4
		WHEN crop = 'papaya' THEN 2
		WHEN crop = 'coconut' THEN 11
		WHEN crop = 'cotton' THEN 12
		WHEN crop = 'coffee' THEN 3
	END
);

SELECT *
FROM crop_recommendation_n;

------------------------------------------------------------------------------------------------------------

-- VERIFICACIÓN DE LAS TABLAS

SELECT n.id, cer.crop, n.N, cer.rainfall_min
FROM crop_recommendation_n AS n
JOIN crop_environmental_requirements AS cer
  ON n.crop_code = cer.crop_code;

SELECT n.crop, n.N, n.P, n.K, dr.departamento_colombia
FROM crop_recommendation_n AS n
JOIN departamentos_recomendados AS dr
ON n.depto_code = dr.id_depto;


/* Esto fue lo que se exportó como csv, usando
 * la herramienta de exportación de mi editor (dbeaver)
*/
SELECT *
FROM crop_recommendation_n AS n
JOIN departamentos_recomendados AS dr
	ON n.depto_code = dr.id_depto
JOIN crop_environmental_requirements AS cer
  ON n.crop_code = cer.crop_code;






