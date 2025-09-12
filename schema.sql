CREATE TABLE glucose_readings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    value FLOAT NOT NULL,
    timestamp DATETIME NOT NULL UNIQUE,
    received_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO glucose_readings (value,reading_timestamp)
VALUES (5.7,'2025-09-12 06:15:00');