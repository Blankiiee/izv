IF DB_ID(N'CinemaHub_DB') IS NULL
BEGIN
    CREATE DATABASE CinemaHub_DB;
END;
GO
USE CinemaHub_DB;
GO
SET NOCOUNT ON;
GO
IF OBJECT_ID(N'dbo.Genres', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Genres (
        GenreID INT IDENTITY(1,1) PRIMARY KEY,
        GenreName NVARCHAR(50) NOT NULL UNIQUE,
        Description NVARCHAR(255) NOT NULL DEFAULT N''
    );
END;
GO
IF OBJECT_ID(N'dbo.Halls', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Halls (
        HallID INT IDENTITY(1,1) PRIMARY KEY,
        HallName NVARCHAR(50) NOT NULL UNIQUE,
        Capacity INT NOT NULL CHECK (Capacity > 0),
        IsVIP BIT NOT NULL DEFAULT 0
    );
END;
GO
IF OBJECT_ID(N'dbo.Movies', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Movies (
        MovieID INT IDENTITY(1,1) PRIMARY KEY,
        Title NVARCHAR(150) NOT NULL,
        GenreID INT NOT NULL,
        DurationMinutes INT NOT NULL CHECK (DurationMinutes > 0),
        AgeRating NVARCHAR(10) NOT NULL DEFAULT N'12+',
        BasePrice DECIMAL(10,2) NOT NULL CHECK (BasePrice >= 0),
        Synopsis NVARCHAR(500) NOT NULL DEFAULT N'',
        Accent CHAR(7) NOT NULL DEFAULT '#9a583b',
        CONSTRAINT FK_Movies_Genres FOREIGN KEY (GenreID) REFERENCES dbo.Genres(GenreID)
    );
END;
GO
IF OBJECT_ID(N'dbo.Sessions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sessions (
        SessionID INT IDENTITY(1,1) PRIMARY KEY,
        MovieID INT NOT NULL,
        HallID INT NOT NULL,
        StartTime DATETIME2(0) NOT NULL,
        TicketPrice DECIMAL(10,2) NOT NULL CHECK (TicketPrice >= 0),
        CONSTRAINT FK_Sessions_Movies FOREIGN KEY (MovieID) REFERENCES dbo.Movies(MovieID) ON DELETE CASCADE,
        CONSTRAINT FK_Sessions_Halls FOREIGN KEY (HallID) REFERENCES dbo.Halls(HallID),
        CONSTRAINT UQ_Sessions_Hall_StartTime UNIQUE (HallID, StartTime)
    );
END;
GO
IF OBJECT_ID(N'dbo.Tickets', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Tickets (
        TicketID INT IDENTITY(1,1) PRIMARY KEY,
        SessionID INT NOT NULL,
        CustomerName NVARCHAR(100) NOT NULL,
        CustomerPhone NVARCHAR(20) NOT NULL DEFAULT N'',
        SeatNumber INT NOT NULL CHECK (SeatNumber > 0),
        PurchaseDate DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
        IsPaid BIT NOT NULL DEFAULT 1,
        CONSTRAINT FK_Tickets_Sessions FOREIGN KEY (SessionID) REFERENCES dbo.Sessions(SessionID) ON DELETE CASCADE,
        CONSTRAINT UQ_Tickets_Session_Seat UNIQUE (SessionID, SeatNumber)
    );
END;
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Sessions_StartTime' AND object_id = OBJECT_ID(N'dbo.Sessions'))
    CREATE INDEX IX_Sessions_StartTime ON dbo.Sessions(StartTime);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_Tickets_Session_Paid' AND object_id = OBJECT_ID(N'dbo.Tickets'))
    CREATE INDEX IX_Tickets_Session_Paid ON dbo.Tickets(SessionID, IsPaid);
GO
IF NOT EXISTS (SELECT 1 FROM dbo.Genres WHERE GenreName = N'Наукова фантастика')
    INSERT INTO dbo.Genres (GenreName, Description) VALUES (N'Наукова фантастика', N'Космос, майбутнє й технології.');
IF NOT EXISTS (SELECT 1 FROM dbo.Genres WHERE GenreName = N'Екшн та пригоди')
    INSERT INTO dbo.Genres (GenreName, Description) VALUES (N'Екшн та пригоди', N'Динамічні історії та великі пригоди.');
IF NOT EXISTS (SELECT 1 FROM dbo.Genres WHERE GenreName = N'Драма')
    INSERT INTO dbo.Genres (GenreName, Description) VALUES (N'Драма', N'Сильні історії про людей і вибір.');
IF NOT EXISTS (SELECT 1 FROM dbo.Genres WHERE GenreName = N'Анімація')
    INSERT INTO dbo.Genres (GenreName, Description) VALUES (N'Анімація', N'Яскраві стрічки для всієї родини.');
IF NOT EXISTS (SELECT 1 FROM dbo.Halls WHERE HallName = N'Зал «Синій»')
    INSERT INTO dbo.Halls (HallName, Capacity, IsVIP) VALUES (N'Зал «Синій»', 150, 0);
IF NOT EXISTS (SELECT 1 FROM dbo.Halls WHERE HallName = N'Зал «Червоний»')
    INSERT INTO dbo.Halls (HallName, Capacity, IsVIP) VALUES (N'Зал «Червоний»', 100, 0);
IF NOT EXISTS (SELECT 1 FROM dbo.Halls WHERE HallName = N'VIP Lounge')
    INSERT INTO dbo.Halls (HallName, Capacity, IsVIP) VALUES (N'VIP Lounge', 30, 1);
IF NOT EXISTS (SELECT 1 FROM dbo.Halls WHERE HallName = N'Мала зала')
    INSERT INTO dbo.Halls (HallName, Capacity, IsVIP) VALUES (N'Мала зала', 48, 0);
GO
IF NOT EXISTS (SELECT 1 FROM dbo.Movies WHERE Title = N'Дюна: Частина друга')
    INSERT INTO dbo.Movies (Title, GenreID, DurationMinutes, AgeRating, BasePrice, Synopsis, Accent)
    SELECT N'Дюна: Частина друга', GenreID, 166, N'16+', 200, N'Пол Атрейдес обирає між коханням і долею цілого всесвіту.', '#bd774e' FROM dbo.Genres WHERE GenreName = N'Наукова фантастика';
IF NOT EXISTS (SELECT 1 FROM dbo.Movies WHERE Title = N'Інтерстеллар')
    INSERT INTO dbo.Movies (Title, GenreID, DurationMinutes, AgeRating, BasePrice, Synopsis, Accent)
    SELECT N'Інтерстеллар', GenreID, 169, N'12+', 180, N'Екіпаж вирушає крізь простір і час, щоб знайти людству новий дім.', '#607789' FROM dbo.Genres WHERE GenreName = N'Наукова фантастика';
IF NOT EXISTS (SELECT 1 FROM dbo.Movies WHERE Title = N'Оппенгеймер')
    INSERT INTO dbo.Movies (Title, GenreID, DurationMinutes, AgeRating, BasePrice, Synopsis, Accent)
    SELECT N'Оппенгеймер', GenreID, 180, N'18+', 220, N'Портрет ученого, чиє відкриття змінило перебіг історії.', '#ab5945' FROM dbo.Genres WHERE GenreName = N'Драма';
IF NOT EXISTS (SELECT 1 FROM dbo.Movies WHERE Title = N'Дедпул і Росомаха')
    INSERT INTO dbo.Movies (Title, GenreID, DurationMinutes, AgeRating, BasePrice, Synopsis, Accent)
    SELECT N'Дедпул і Росомаха', GenreID, 127, N'18+', 210, N'Двоє несхожих героїв вирушають у пригоду поза межами звичного світу.', '#a84b4b' FROM dbo.Genres WHERE GenreName = N'Екшн та пригоди';
IF NOT EXISTS (SELECT 1 FROM dbo.Movies WHERE Title = N'Думками навиворіт 2')
    INSERT INTO dbo.Movies (Title, GenreID, DurationMinutes, AgeRating, BasePrice, Synopsis, Accent)
    SELECT N'Думками навиворіт 2', GenreID, 96, N'0+', 160, N'Райлі дорослішає, а в її голові з''являються нові емоції.', '#9584ba' FROM dbo.Genres WHERE GenreName = N'Анімація';
IF NOT EXISTS (SELECT 1 FROM dbo.Movies WHERE Title = N'Кунг-фу Панда 4')
    INSERT INTO dbo.Movies (Title, GenreID, DurationMinutes, AgeRating, BasePrice, Synopsis, Accent)
    SELECT N'Кунг-фу Панда 4', GenreID, 94, N'0+', 150, N'По завжди є куди рости.', '#7e9b6d' FROM dbo.Genres WHERE GenreName = N'Анімація';
IF NOT EXISTS (SELECT 1 FROM dbo.Movies WHERE Title = N'Марсіанин')
    INSERT INTO dbo.Movies (Title, GenreID, DurationMinutes, AgeRating, BasePrice, Synopsis, Accent)
    SELECT N'Марсіанин', GenreID, 144, N'12+', 170, N'Сам на Червоній планеті астронавт планує повернення додому.', '#bf7656' FROM dbo.Genres WHERE GenreName = N'Наукова фантастика';
GO
DECLARE @Schedule TABLE (Title NVARCHAR(150), HallName NVARCHAR(50), StartTime DATETIME2(0), TicketPrice DECIMAL(10,2));
INSERT INTO @Schedule VALUES
    (N'Дюна: Частина друга', N'Зал «Синій»', '2026-10-09T11:40:00', 220),
    (N'Інтерстеллар', N'Зал «Червоний»', '2026-10-09T12:10:00', 190),
    (N'Думками навиворіт 2', N'Мала зала', '2026-10-09T13:20:00', 170),
    (N'Оппенгеймер', N'VIP Lounge', '2026-10-09T14:00:00', 360),
    (N'Дедпул і Росомаха', N'Зал «Червоний»', '2026-10-09T16:40:00', 240),
    (N'Дюна: Частина друга', N'VIP Lounge', '2026-10-09T18:30:00', 340),
    (N'Кунг-фу Панда 4', N'Зал «Червоний»', '2026-10-09T19:00:00', 170),
    (N'Інтерстеллар', N'Зал «Синій»', '2026-10-09T20:45:00', 200),
    (N'Марсіанин', N'Мала зала', '2026-10-10T10:30:00', 180),
    (N'Оппенгеймер', N'Зал «Червоний»', '2026-10-10T18:15:00', 240),
    (N'Думками навиворіт 2', N'Зал «Синій»', '2026-10-10T12:00:00', 170),
    (N'Дедпул і Росомаха', N'VIP Lounge', '2026-10-10T21:00:00', 350),
    (N'Дюна: Частина друга', N'Зал «Червоний»', '2026-10-11T16:40:00', 220),
    (N'Марсіанин', N'Зал «Синій»', '2026-10-11T19:20:00', 200);
INSERT INTO dbo.Sessions (MovieID, HallID, StartTime, TicketPrice)
SELECT m.MovieID, h.HallID, schedule.StartTime, schedule.TicketPrice
FROM @Schedule schedule
JOIN dbo.Movies m ON m.Title = schedule.Title
JOIN dbo.Halls h ON h.HallName = schedule.HallName
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.Sessions existing
    WHERE existing.HallID = h.HallID AND existing.StartTime = schedule.StartTime
);
GO
DECLARE @Sales TABLE (
    Title NVARCHAR(150), HallName NVARCHAR(50), StartTime DATETIME2(0),
    CustomerName NVARCHAR(100), CustomerPhone NVARCHAR(20), SeatNumber INT, IsPaid BIT
);
INSERT INTO @Sales VALUES
    (N'Дюна: Частина друга', N'Зал «Синій»', '2026-10-09T11:40:00', N'Олександр Іваненко', N'+380 97 111 22 33', 12, 1),
    (N'Дюна: Частина друга', N'Зал «Синій»', '2026-10-09T11:40:00', N'Марія Бондаренко', N'+380 50 222 33 44', 13, 1),
    (N'Дюна: Частина друга', N'Зал «Синій»', '2026-10-09T11:40:00', N'Дмитро Шевченко', N'+380 63 333 44 55', 14, 1),
    (N'Дюна: Частина друга', N'Зал «Синій»', '2026-10-09T11:40:00', N'Аліна Коваль', N'+380 95 400 20 10', 25, 1),
    (N'Інтерстеллар', N'Зал «Червоний»', '2026-10-09T12:10:00', N'Віктор Мороз', N'+380 98 444 55 66', 45, 1),
    (N'Інтерстеллар', N'Зал «Червоний»', '2026-10-09T12:10:00', N'Олена Кравець', N'+380 50 555 66 77', 46, 1),
    (N'Думками навиворіт 2', N'Мала зала', '2026-10-09T13:20:00', N'Андрій Ткачук', N'+380 67 666 77 88', 20, 1),
    (N'Оппенгеймер', N'VIP Lounge', '2026-10-09T14:00:00', N'Ігор Мельник', N'+380 93 777 88 99', 5, 1),
    (N'Оппенгеймер', N'VIP Lounge', '2026-10-09T14:00:00', N'Наталія Савченко', N'+380 50 888 99 00', 6, 1),
    (N'Дедпул і Росомаха', N'Зал «Червоний»', '2026-10-09T16:40:00', N'Сергій Поліщук', N'+380 97 999 00 11', 88, 1),
    (N'Дюна: Частина друга', N'VIP Lounge', '2026-10-09T18:30:00', N'Юлія Лисенко', N'+380 63 000 11 22', 15, 1),
    (N'Дюна: Частина друга', N'VIP Lounge', '2026-10-09T18:30:00', N'Аліна Коваль', N'+380 95 400 20 10', 18, 1),
    (N'Кунг-фу Панда 4', N'Зал «Червоний»', '2026-10-09T19:00:00', N'Тарас Мельник', N'+380 68 208 77 04', 5, 1),
    (N'Інтерстеллар', N'Зал «Синій»', '2026-10-09T20:45:00', N'Софія Петренко', N'+380 93 870 12 45', 30, 1),
    (N'Думками навиворіт 2', N'Зал «Синій»', '2026-10-10T12:00:00', N'Максим Романюк', N'+380 67 310 65 21', 17, 1),
    (N'Думками навиворіт 2', N'Зал «Синій»', '2026-10-10T12:00:00', N'Ірина Бойко', N'+380 50 450 32 19', 24, 1),
    (N'Оппенгеймер', N'Зал «Червоний»', '2026-10-10T18:15:00', N'Богдан Олійник', N'+380 96 810 42 03', 9, 1),
    (N'Дедпул і Росомаха', N'VIP Lounge', '2026-10-10T21:00:00', N'Катерина Гнатюк', N'+380 73 204 66 18', 4, 1),
    (N'Дюна: Частина друга', N'Зал «Червоний»', '2026-10-11T16:40:00', N'Павло Клим', N'+380 99 503 90 12', 40, 0),
    (N'Марсіанин', N'Зал «Синій»', '2026-10-11T19:20:00', N'Дарина Кравчук', N'+380 63 701 28 54', 11, 0),
    (N'Марсіанин', N'Зал «Синій»', '2026-10-11T19:20:00', N'Михайло Дорошенко', N'+380 98 326 40 77', 20, 1);
INSERT INTO dbo.Tickets (SessionID, CustomerName, CustomerPhone, SeatNumber, IsPaid)
SELECT s.SessionID, sales.CustomerName, sales.CustomerPhone, sales.SeatNumber, sales.IsPaid
FROM @Sales sales
JOIN dbo.Movies m ON m.Title = sales.Title
JOIN dbo.Halls h ON h.HallName = sales.HallName
JOIN dbo.Sessions s ON s.MovieID = m.MovieID AND s.HallID = h.HallID AND s.StartTime = sales.StartTime
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.Tickets existing
    WHERE existing.SessionID = s.SessionID AND existing.SeatNumber = sales.SeatNumber
);
GO
