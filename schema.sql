CREATE TABLE IF NOT EXISTS Users (
    user_id VARCHAR(10) PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(50) UNIQUE NOT NULL,
    phone VARCHAR(15),
    is_admin TINYINT(1) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Stations (
    station_id VARCHAR(10) PRIMARY KEY,
    station_name VARCHAR(50) UNIQUE NOT NULL,
    city VARCHAR(30),
    state VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS Trains (
    train_id VARCHAR(10) PRIMARY KEY,
    train_number INT UNIQUE NOT NULL,
    train_name VARCHAR(50) NOT NULL,
    source_station_id VARCHAR(10) NOT NULL,
    destination_station_id VARCHAR(10) NOT NULL,
    departure_time TIME,
    arrival_time TIME,
    FOREIGN KEY (source_station_id) REFERENCES Stations(station_id),
    FOREIGN KEY (destination_station_id) REFERENCES Stations(station_id)
);

CREATE TABLE IF NOT EXISTS TrainClasses (
    train_class_id VARCHAR(10) PRIMARY KEY,
    train_id VARCHAR(10) NOT NULL,
    class_name VARCHAR(20) NOT NULL,
    fare INT NOT NULL,
    total_seats INT NOT NULL,
    FOREIGN KEY (train_id) REFERENCES Trains(train_id),
    UNIQUE (train_id, class_name)
);

CREATE TABLE IF NOT EXISTS TrainStops (
    stop_id INT AUTO_INCREMENT PRIMARY KEY,
    train_id VARCHAR(10) NOT NULL,
    station_id VARCHAR(10) NOT NULL,
    stop_number INT NOT NULL,
    arrival_time TIME,
    departure_time TIME,
    halt_minutes INT DEFAULT 2,
    FOREIGN KEY (train_id) REFERENCES Trains(train_id),
    FOREIGN KEY (station_id) REFERENCES Stations(station_id),
    UNIQUE (train_id, stop_number)
);

CREATE TABLE IF NOT EXISTS Bookings (
    booking_id VARCHAR(10) PRIMARY KEY,
    user_id VARCHAR(10) NOT NULL,
    train_class_id VARCHAR(10) NOT NULL,
    journey_date DATE NOT NULL,
    seat_count INT NOT NULL,
    pnr_number VARCHAR(15) UNIQUE NOT NULL,
    booking_status VARCHAR(20) NOT NULL DEFAULT 'Confirmed',
    cancellation_reason VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (train_class_id) REFERENCES TrainClasses(train_class_id),
    INDEX idx_bookings_class_date (train_class_id, journey_date, booking_status)
);

INSERT INTO Stations (station_id, station_name, city, state) VALUES
('S01', 'Ahmedabad Junction', 'Ahmedabad', 'Gujarat'),
('S02', 'Rajkot Junction', 'Rajkot', 'Gujarat'),
('S03', 'Vadodara Junction', 'Vadodara', 'Gujarat'),
('S04', 'Surat', 'Surat', 'Gujarat'),
('S05', 'Jamnagar', 'Jamnagar', 'Gujarat'),
('S06', 'Mumbai Central', 'Mumbai', 'Maharashtra'),
('S07', 'New Delhi', 'Delhi', 'Delhi'),
('S08', 'Bhopal Junction', 'Bhopal', 'Madhya Pradesh'),
('S09', 'Jaipur Junction', 'Jaipur', 'Rajasthan'),
('S10', 'Howrah Junction', 'Kolkata', 'West Bengal'),
('S11', 'Anand Junction', 'Anand', 'Gujarat'),
('S12', 'Ratlam Junction', 'Ratlam', 'Madhya Pradesh'),
('S13', 'Kota Junction', 'Kota', 'Rajasthan'),
('S14', 'Sawai Madhopur Junction', 'Sawai Madhopur', 'Rajasthan'),
('S15', 'Mathura Junction', 'Mathura', 'Uttar Pradesh'),
('S16', 'Agra Cantt', 'Agra', 'Uttar Pradesh'),
('S17', 'Gwalior Junction', 'Gwalior', 'Madhya Pradesh'),
('S18', 'Jhansi Junction', 'Jhansi', 'Uttar Pradesh'),
('S19', 'Rewari Junction', 'Rewari', 'Haryana'),
('S20', 'Old Delhi Junction', 'Delhi', 'Delhi'),
('S21', 'Palanpur Junction', 'Palanpur', 'Gujarat'),
('S22', 'Abu Road', 'Abu Road', 'Rajasthan'),
('S23', 'Ajmer Junction', 'Ajmer', 'Rajasthan'),
('S24', 'Dewas Junction', 'Dewas', 'Madhya Pradesh'),
('S25', 'Godhra Junction', 'Godhra', 'Gujarat'),
('S26', 'Bandra Terminus', 'Mumbai', 'Maharashtra'),
('S27', 'Dadar', 'Mumbai', 'Maharashtra'),
('S28', 'Prayagraj Junction', 'Prayagraj', 'Uttar Pradesh'),
('S29', 'Varanasi Junction', 'Varanasi', 'Uttar Pradesh'),
('S30', 'Patna Junction', 'Patna', 'Bihar'),
('S31', 'Dr Ambedkar Nagar', 'Indore', 'Madhya Pradesh'),
('S32', 'Bhavnagar Terminus', 'Bhavnagar', 'Gujarat'),
('S33', 'Gandhidham Junction', 'Gandhidham', 'Gujarat'),
('S34', 'Hazrat Nizamuddin', 'Delhi', 'Delhi'),
('S35', 'Udaipur City', 'Udaipur', 'Rajasthan'),
('S36', 'Amritsar Junction', 'Amritsar', 'Punjab'),
('S37', 'Kalka', 'Kalka', 'Haryana');
INSERT INTO Trains
(train_id, train_number, train_name, source_station_id, destination_station_id, departure_time, arrival_time)
VALUES
('T01', 12951, 'Mumbai Rajdhani', 'S06', 'S07', '16:35:00', '08:35:00'),

('T02', 12952, 'Delhi Mumbai Rajdhani', 'S07', 'S06', '16:35:00', '08:15:00'),

('T03', 12926, 'Paschim Express', 'S07', 'S06', '16:10:00', '17:40:00'),

('T04', 12957, 'Swarna Jayanti Rajdhani', 'S01', 'S07', '19:40:00', '10:05:00'),

('T05', 12958, 'Delhi Ahmedabad Rajdhani', 'S07', 'S01', '19:55:00', '10:30:00'),

('T06', 12009, 'Mumbai Ahmedabad Shatabdi', 'S06', 'S01', '06:10:00', '12:40:00'),

('T07', 12010, 'Ahmedabad Mumbai Shatabdi', 'S01', 'S06', '14:40:00', '21:10:00'),

('T08', 12155, 'Bhopal Express', 'S08', 'S07', '22:00:00', '07:30:00'),

('T09', 12156, 'Delhi Bhopal Express', 'S07', 'S08', '21:15:00', '06:45:00'),

('T10', 12915, 'Ashram Express', 'S01', 'S20', '18:30:00', '06:00:00'),

('T11', 12953, 'August Kranti Rajdhani', 'S06', 'S34', '17:40:00', '10:55:00'),

('T12', 12963, 'Mewar Superfast Express', 'S34', 'S35', '19:00:00', '07:15:00'),

('T13', 12947, 'Azimabad Express', 'S01', 'S30', '21:40:00', '04:30:00'),

('T14', 12937, 'Gandhidham Howrah Garbha Express', 'S33', 'S10', '18:00:00', '06:00:00'),

('T15', 12971, 'Bhavnagar Bandra Terminus Express', 'S26', 'S32', '21:30:00', '10:30:00'),

('T16', 12973, 'Indore Jaipur Superfast Express', 'S31', 'S09', '16:00:00', '05:30:00'),

('T17', 12011, 'Kalka Shatabdi Express', 'S07', 'S37', '07:40:00', '12:45:00'),

('T18', 12015, 'Ajmer Shatabdi Express', 'S07', 'S23', '06:05:00', '12:45:00'),

('T19', 12903, 'Golden Temple Mail', 'S06', 'S36', '18:45:00', '07:30:00');
INSERT INTO TrainClasses
(train_class_id, train_id, class_name, fare, total_seats)
VALUES
('TC01', 'T01', 'sleeper', 900, 100),
('TC02', 'T01', '3ac', 1800, 60),
('TC03', 'T01', '2ac', 2500, 40),
('TC04', 'T01', '1ac', 4200, 20),

('TC05', 'T02', '3ac', 1800, 60),
('TC06', 'T02', '2ac', 2500, 40),

('TC07', 'T03', 'sleeper', 850, 120),
('TC08', 'T03', '3ac', 1750, 70),

('TC09', 'T04', '3ac', 1700, 50),
('TC10', 'T04', '2ac', 2400, 36),

('TC11', 'T05', '3ac', 1700, 50),
('TC12', 'T05', '2ac', 2400, 36),

('TC13', 'T06', 'chair-car', 700, 80),
('TC14', 'T07', 'chair-car', 700, 80),

('TC15', 'T08', 'sleeper', 600, 150),
('TC16', 'T08', '3ac', 1500, 60),

('TC17', 'T09', 'sleeper', 600, 150),
('TC18', 'T09', '3ac', 1500, 60),

('TC19', 'T10', 'sleeper', 550, 140),
('TC20', 'T10', '2ac', 1900, 40),

('TC21', 'T11', '2ac', 2800, 40),
('TC22', 'T11', '3ac', 1900, 60),

('TC23', 'T12', '2ac', 2400, 40),
('TC24', 'T12', '3ac', 1700, 60),

('TC25', 'T13', 'sleeper', 900, 120),
('TC26', 'T13', '3ac', 1800, 60),

('TC27', 'T14', 'sleeper', 1000, 120),
('TC28', 'T14', '3ac', 2000, 60),

('TC29', 'T15', 'sleeper', 700, 120),
('TC30', 'T15', '3ac', 1600, 60),

('TC31', 'T16', 'sleeper', 650, 120),
('TC32', 'T16', '3ac', 1500, 60),

('TC33', 'T17', 'chair-car', 850, 80),

('TC34', 'T18', 'chair-car', 800, 80),

('TC35', 'T19', 'sleeper', 1000, 120),
('TC36', 'T19', '3ac', 2100, 60);
INSERT INTO TrainStops
(train_id, station_id, stop_number, arrival_time, departure_time, halt_minutes)
VALUES

('T01', 'S06', 1, '16:35:00', '16:35:00', 0),
('T01', 'S04', 2, '19:30:00', '19:35:00', 5),
('T01', 'S03', 3, '21:10:00', '21:15:00', 5),
('T01', 'S12', 4, '00:15:00', '00:20:00', 5),
('T01', 'S13', 5, '03:00:00', '03:05:00', 5),
('T01', 'S15', 6, '05:45:00', '05:50:00', 5),
('T01', 'S07', 7, '08:35:00', '08:35:00', 0),

('T02', 'S07', 1, '16:35:00', '16:35:00', 0),
('T02', 'S19', 2, '18:45:00', '18:50:00', 5),
('T02', 'S09', 3, '22:30:00', '22:35:00', 5),
('T02', 'S23', 4, '01:00:00', '01:05:00', 5),
('T02', 'S22', 5, '02:45:00', '02:50:00', 5),
('T02', 'S21', 6, '04:00:00', '04:05:00', 5),
('T02', 'S01', 7, '08:15:00', '08:15:00', 0),

('T03', 'S07', 1, '16:10:00', '16:10:00', 0),
('T03', 'S15', 2, '20:00:00', '20:05:00', 5),
('T03', 'S13', 3, '22:00:00', '22:05:00', 5),
('T03', 'S12', 4, '00:30:00', '00:35:00', 5),
('T03', 'S03', 5, '05:30:00', '05:35:00', 5),
('T03', 'S04', 6, '07:15:00', '07:20:00', 5),
('T03', 'S06', 7, '17:40:00', '17:40:00', 0),

('T04', 'S01', 1, '19:40:00', '19:40:00', 0),
('T04', 'S11', 2, '20:20:00', '20:25:00', 5),
('T04', 'S03', 3, '21:30:00', '21:35:00', 5),
('T04', 'S12', 4, '02:30:00', '02:35:00', 5),
('T04', 'S13', 5, '04:20:00', '04:25:00', 5),
('T04', 'S15', 6, '06:15:00', '06:20:00', 5),
('T04', 'S07', 7, '10:05:00', '10:05:00', 0),

('T05', 'S07', 1, '19:55:00', '19:55:00', 0),
('T05', 'S15', 2, '23:30:00', '23:35:00', 5),
('T05', 'S13', 3, '01:30:00', '01:35:00', 5),
('T05', 'S12', 4, '04:00:00', '04:05:00', 5),
('T05', 'S03', 5, '09:00:00', '09:05:00', 5),
('T05', 'S01', 6, '10:30:00', '10:30:00', 0),

('T06', 'S06', 1, '06:10:00', '06:10:00', 0),
('T06', 'S04', 2, '08:30:00', '08:35:00', 5),
('T06', 'S03', 3, '10:20:00', '10:25:00', 5),
('T06', 'S11', 4, '11:00:00', '11:05:00', 5),
('T06', 'S01', 5, '12:40:00', '12:40:00', 0),

('T07', 'S01', 1, '14:40:00', '14:40:00', 0),
('T07', 'S11', 2, '15:15:00', '15:20:00', 5),
('T07', 'S03', 3, '16:00:00', '16:05:00', 5),
('T07', 'S04', 4, '18:00:00', '18:05:00', 5),
('T07', 'S06', 5, '21:10:00', '21:10:00', 0),

('T08', 'S08', 1, '22:00:00', '22:00:00', 0),
('T08', 'S18', 2, '01:30:00', '01:35:00', 5),
('T08', 'S17', 3, '03:00:00', '03:05:00', 5),
('T08', 'S16', 4, '05:00:00', '05:05:00', 5),
('T08', 'S07', 5, '07:30:00', '07:30:00', 0),

('T09', 'S07', 1, '21:15:00', '21:15:00', 0),
('T09', 'S16', 2, '23:30:00', '23:35:00', 5),
('T09', 'S17', 3, '01:30:00', '01:35:00', 5),
('T09', 'S18', 4, '03:00:00', '03:05:00', 5),
('T09', 'S08', 5, '06:45:00', '06:45:00', 0),

('T10', 'S01', 1, '18:30:00', '18:30:00', 0),
('T10', 'S20', 2, '06:00:00', '06:00:00', 0),

('T11', 'S06', 1, '17:40:00', '17:40:00', 0),
('T11', 'S34', 2, '10:55:00', '10:55:00', 0),

('T12', 'S34', 1, '19:00:00', '19:00:00', 0),
('T12', 'S13', 2, '23:00:00', '23:05:00', 5),
('T12', 'S14', 3, '01:00:00', '01:05:00', 5),
('T12', 'S23', 4, '04:30:00', '04:35:00', 5),
('T12', 'S35', 5, '07:15:00', '07:15:00', 0),

('T13', 'S01', 1, '21:40:00', '21:40:00', 0),
('T13', 'S28', 2, '02:00:00', '02:05:00', 5),
('T13', 'S29', 3, '05:30:00', '05:35:00', 5),
('T13', 'S30', 4, '09:00:00', '09:00:00', 0),

('T14', 'S33', 1, '18:00:00', '18:00:00', 0),
('T14', 'S03', 2, '22:00:00', '22:05:00', 5),
('T14', 'S10', 3, '06:00:00', '06:00:00', 0),

('T15', 'S26', 1, '21:30:00', '21:30:00', 0),
('T15', 'S02', 2, '05:00:00', '05:05:00', 5),
('T15', 'S32', 3, '10:30:00', '10:30:00', 0),

('T16', 'S31', 1, '16:00:00', '16:00:00', 0),
('T16', 'S24', 2, '17:00:00', '17:05:00', 5),
('T16', 'S09', 3, '05:30:00', '05:30:00', 0),

('T17', 'S07', 1, '07:40:00', '07:40:00', 0),
('T17', 'S15', 2, '09:30:00', '09:35:00', 5),
('T17', 'S16', 3, '10:15:00', '10:20:00', 5),
('T17', 'S37', 4, '12:45:00', '12:45:00', 0),

('T18', 'S07', 1, '06:05:00', '06:05:00', 0),
('T18', 'S15', 2, '08:00:00', '08:05:00', 5),
('T18', 'S13', 3, '09:45:00', '09:50:00', 5),
('T18', 'S23', 4, '12:45:00', '12:45:00', 0),

('T19', 'S06', 1, '18:45:00', '18:45:00', 0),
('T19', 'S04', 2, '21:30:00', '21:35:00', 5),
('T19', 'S03', 3, '23:30:00', '23:35:00', 5),
('T19', 'S28', 4, '04:30:00', '04:35:00', 5),
('T19', 'S36', 5, '07:30:00', '07:30:00', 0);
