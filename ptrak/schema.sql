-- Users->Messages->Projects->Announcements->Tasks->Notes
DROP TABLE IF EXISTS Notes;
DROP TABLE IF EXISTS Tasks;
DROP TABLE IF EXISTS Announcements;
DROP TABLE IF EXISTS Projects;
DROP TABLE IF EXISTS Messages;
DROP TABLE IF EXISTS Users;

-- table for user data
CREATE TABLE Users (
  uid INT AUTO_INCREMENT,
  firstname VARCHAR(50) NOT NULL,
  lastname VARCHAR(50) NOT NULL,
  email VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(200) NOT NULL,
  projects TEXT,
  level INT DEFAULT 1,
  lastlogin TIMESTAMP,
  PRIMARY KEY (uid)
);

-- table for project data
CREATE TABLE Projects (
  pid INT AUTO_INCREMENT,
  title VARCHAR(500) NOT NULL,
  owner INT NOT NULL,
  description TEXT NOT NULL,
  date_due TIMESTAMP,   -- not a typo - this *can* be NULL
  PRIMARY KEY (pid),
  FOREIGN KEY (owner) REFERENCES Users (uid)
);

-- table for task data
CREATE TABLE Tasks (
  tid INT AUTO_INCREMENT,
  pid INT NOT NULL,
  creator INT NOT NULL,
  status ENUM('new', 'in progress', 'under review', 'complete') NOT NULL DEFAULT 'new',
  title VARCHAR(250) NOT NULL,
  description TEXT,   -- not a typo
  due_date TIMESTAMP, -- also not a typo
  date_submitted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  date_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  tags TEXT,
  PRIMARY KEY (tid),
  FOREIGN KEY (pid) REFERENCES Projects (pid),
  FOREIGN KEY (creator) REFERENCES Users (uid)
);


-- table for task notes
CREATE TABLE Notes (
  nid INT AUTO_INCREMENT,
  tid INT NOT NULL,
  content TEXT NOT NULL,
  author INT NOT NULL,
  date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (nid),
  FOREIGN KEY (tid) REFERENCES Tasks (tid),
  FOREIGN KEY (author) REFERENCES Users (uid)
);

-- table for user-to-user messages
CREATE TABLE Messages (
  mid INT AUTO_INCREMENT,
  destination INT NOT NULL,
  source INT NOT NULL,
  content TEXT NOT NULL,
  date_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (mid),
  FOREIGN KEY (source) REFERENCES Users (uid),
  FOREIGN KEY (destination) REFERENCES Users (uid)
);

-- table for project announcements
CREATE TABLE Announcements (
  aid INT AUTO_INCREMENT,
  pid INT NOT NULL,
  author INT NOT NULL,
  date_made TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  content TEXT NOT NULL,
  PRIMARY KEY (aid),
  FOREIGN KEY (pid) REFERENCES Projects (pid),
  FOREIGN KEY (author) REFERENCES Users (uid)
);
